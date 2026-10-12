import os
import json
from flask import Flask, jsonify, request, Response, send_from_directory
from flask_cors import CORS

try:
    from backend.database.db_config import init_db, get_db_connection
    from backend.database.queries import (
        get_all_students,
        get_student_by_id,
        add_student,
        delete_student,
        check_duplicate_student,
        mark_attendance as db_mark_attendance,
        mark_attendance_by_name,
        get_today_attendance,
        get_attendance_report,
        get_dashboard_stats,
        verify_user
    )
    from backend.face_detector import FaceDetector
    from backend.face_recognizer import FaceRecognizer
    from backend.train_model import train_model
    from backend.camera import Camera, generate_camera_stream
    from backend.utils.image_utils import (
        decode_image_bytes,
        compute_face_encoding,
        save_student_face_samples
    )
except ImportError:
    from database.db_config import init_db, get_db_connection
    from database.queries import (
        get_all_students,
        get_student_by_id,
        add_student,
        delete_student,
        check_duplicate_student,
        mark_attendance as db_mark_attendance,
        mark_attendance_by_name,
        get_today_attendance,
        get_attendance_report,
        get_dashboard_stats,
        verify_user
    )
    from face_detector import FaceDetector
    from face_recognizer import FaceRecognizer
    from train_model import train_model
    from camera import Camera, generate_camera_stream
    from utils.image_utils import (
        decode_image_bytes,
        compute_face_encoding,
        save_student_face_samples
    )

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))

app = Flask(__name__, static_folder=FRONTEND_DIR)
CORS(app)

# Initialize database
init_db()

# Lazy-loaded singletons for camera, detector, and recognizer
detector = None
recognizer = None
camera = None


def get_detector():
    global detector
    if detector is None:
        detector = FaceDetector()
    return detector


def get_recognizer():
    global recognizer
    if recognizer is None:
        recognizer = FaceRecognizer()
    return recognizer


def get_camera():
    global camera
    if camera is None:
        camera = Camera()
    return camera


# ---------------- Frontend Serving Routes ----------------

@app.route("/")
def index():
    """Serves the login page or API status."""
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return send_from_directory(FRONTEND_DIR, "index.html")
    return jsonify({"message": "Smart Attendance Backend Running", "status": "active"})


@app.route("/<path:path>")
def static_proxy(path):
    """Serves static files (html, css, js, assets) from frontend directory."""
    if os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    return jsonify({"error": "File not found"}), 404


# ---------------- Authentication ----------------

@app.route("/login", methods=["POST"])
def login():
    """Authenticates admin users against database."""
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"success": False, "message": "Username and password required"}), 400

    user = verify_user(username, password)
    if user:
        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": {"username": user["username"], "role": user.get("role", "admin")}
        })
    else:
        return jsonify({"success": False, "message": "Invalid username or password"}), 401


# ---------------- Student Management ----------------

@app.route("/students", methods=["GET"])
def list_students():
    """Returns list of registered students with face enrollment status."""
    students = get_all_students()
    return jsonify(students)


@app.route("/students/check", methods=["GET"])
def check_student_availability():
    """Checks whether a student ID or Roll number is available or already in use."""
    sid = request.args.get("id") or request.args.get("student_id")
    roll = request.args.get("roll") or request.args.get("roll_number")
    exclude = request.args.get("exclude_id")

    sid_int = None
    if sid and sid.strip().isdigit():
        sid_int = int(sid.strip())

    exclude_int = None
    if exclude and exclude.strip().isdigit():
        exclude_int = int(exclude.strip())

    is_dup, field, msg = check_duplicate_student(
        student_id=sid_int,
        roll_number=roll.strip() if roll else None,
        exclude_id=exclude_int
    )
    return jsonify({
        "available": not is_dup,
        "is_duplicate": is_dup,
        "field": field,
        "message": msg if is_dup else "Available"
    })


@app.route("/students/validate-face", methods=["POST"])
def validate_face_endpoint():
    """Validates face in uploaded/captured image for instant client feedback."""
    img = None
    if request.files and ("photo" in request.files or "image" in request.files):
        f = request.files.get("photo") or request.files.get("image")
        img = decode_image_bytes(f.read())
    else:
        data = request.get_json(silent=True) or {}
        photo_payload = data.get("photo") or data.get("image") or data.get("photo_base64")
        if photo_payload:
            img = decode_image_bytes(photo_payload)

    if img is None:
        return jsonify({"valid": False, "face_count": 0, "message": "No valid image payload provided"}), 400

    det = get_detector()
    result = det.validate_face_image(img)
    return jsonify({
        "valid": result["valid"],
        "face_count": result["face_count"],
        "face_bbox": result["face_bbox"],
        "message": result["message"]
    }), (200 if result["valid"] else 400)


@app.route("/students", methods=["POST"])
def register_student():
    """
    Registers a new student. Supports details (name, student ID, department/class, roll number)
    and photo enrollment (upload or webcam capture). Validates face, computes 128-d encoding,
    saves dataset samples, retrains model, and immediately reloads recognizer.
    """
    img = None
    if request.content_type and "multipart/form-data" in request.content_type:
        data = request.form.to_dict()
        photo_file = request.files.get("photo") or request.files.get("image")
        if photo_file:
            img = decode_image_bytes(photo_file.read())
    else:
        data = request.get_json(silent=True) or {}
        photo_payload = data.get("photo") or data.get("image") or data.get("photo_base64")
        if photo_payload:
            img = decode_image_bytes(photo_payload)

    name = data.get("name", "").strip()
    roll = (data.get("roll") or data.get("roll_number") or "").strip()
    email = data.get("email", "").strip()
    phone = data.get("phone", "").strip()
    department = data.get("department", "Computer Science").strip()
    student_id_val = data.get("id") or data.get("student_id")

    # 1. Input Validation
    if not name:
        return jsonify({"success": False, "message": "Full Name is required"}), 400

    parsed_student_id = None
    if student_id_val is not None and str(student_id_val).strip() != "":
        try:
            parsed_student_id = int(str(student_id_val).strip())
            if parsed_student_id <= 0:
                return jsonify({"success": False, "message": "Student ID must be a positive integer"}), 400
        except ValueError:
            return jsonify({"success": False, "message": "Student ID must be a valid number"}), 400

    if not roll:
        if parsed_student_id is not None:
            roll = f"STU{parsed_student_id}"
        else:
            return jsonify({"success": False, "message": "Roll Number or Student ID is required"}), 400

    # 2. Duplicate Checks
    is_dup, dup_field, dup_msg = check_duplicate_student(
        student_id=parsed_student_id,
        roll_number=roll
    )
    if is_dup:
        return jsonify({"success": False, "message": dup_msg, "field": dup_field}), 409

    # 3. Face Detection & Validation
    face_val_res = None
    face_encoding_str = ""
    if img is not None:
        det = get_detector()
        face_val_res = det.validate_face_image(img)
        if not face_val_res["valid"]:
            return jsonify({
                "success": False,
                "message": face_val_res["message"],
                "face_count": face_val_res["face_count"]
            }), 400

        # Compute 128-d face encoding
        face_crop = face_val_res["face_crop"]
        encoding_vec = compute_face_encoding(face_crop)
        face_encoding_str = json.dumps(encoding_vec)

    # 4. Insert into Database
    try:
        new_id = add_student(
            name=name,
            roll_number=roll,
            email=email,
            phone=phone,
            department=department,
            student_id=parsed_student_id,
            photo_path="",
            face_encoding=face_encoding_str
        )

        face_enrolled = False
        photo_path = ""

        # 5. Save Face Samples & Retrain Model if photo was provided
        if face_val_res and face_val_res["valid"]:
            sample_info = save_student_face_samples(new_id, face_val_res["face_crop"])
            photo_path = sample_info["primary_path"]

            # Update student record with saved photo path
            conn = get_db_connection()
            conn.execute("UPDATE students SET photo_path = ? WHERE id = ?", (photo_path, new_id))
            conn.commit()
            conn.close()

            # Train model immediately so new student is instantly recognized
            train_model()
            face_enrolled = True

        # 6. Reload recognizer in memory
        try:
            get_recognizer().reload_model()
        except Exception as e:
            print(f"[WARNING] Recognizer reload error: {e}")

        success_msg = f"Student '{name}' registered successfully!"
        if face_enrolled:
            success_msg += " Face profile generated and active for instant recognition."

        return jsonify({
            "success": True,
            "message": success_msg,
            "id": new_id,
            "name": name,
            "roll": roll,
            "department": department,
            "photo_url": f"/students/{new_id}/photo" if face_enrolled else None,
            "face_enrolled": face_enrolled
        }), 201

    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 409
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {e}"}), 500


@app.route("/students/<int:student_id>/photo", methods=["GET"])
def get_student_photo(student_id):
    """Serves the student's enrolled face photo or a fallback SVG avatar."""
    student = get_student_by_id(student_id)
    if student and student.get("photo_path"):
        full_path = os.path.join(BASE_DIR, student["photo_path"])
        if os.path.exists(full_path):
            return send_from_directory(os.path.dirname(full_path), os.path.basename(full_path), mimetype="image/jpeg")

    # Fallback to datasets/users/<id>/img1.jpg directly
    direct_path = os.path.join(BASE_DIR, "datasets", "users", str(student_id), "img1.jpg")
    if os.path.exists(direct_path):
        return send_from_directory(os.path.dirname(direct_path), os.path.basename(direct_path), mimetype="image/jpeg")

    # Clean SVG fallback avatar
    initial = (student["name"][0] if student and student.get("name") else "S").upper()
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 120 120">
        <rect width="120" height="120" rx="24" fill="#4f46e5" />
        <text x="50%" y="54%" font-family="Arial, sans-serif" font-size="52" font-weight="bold" fill="#ffffff" dominant-baseline="middle" text-anchor="middle">{initial}</text>
    </svg>"""
    return Response(svg, mimetype="image/svg+xml")


@app.route("/students/<int:student_id>", methods=["DELETE"])
def remove_student(student_id):
    """Deletes a student and cleans up model and recognizer."""
    success = delete_student(student_id)
    if success:
        try:
            train_model()
            get_recognizer().reload_model()
        except Exception:
            pass
        return jsonify({"success": True, "message": f"Student ID {student_id} deleted successfully"})
    else:
        return jsonify({"success": False, "message": "Student not found"}), 404


# ---------------- Attendance Records & Actions ----------------

@app.route("/attendance/today", methods=["GET"])
def today_attendance():
    """Returns today's attendance status for all students."""
    records = get_today_attendance()
    return jsonify(records)


@app.route("/attendance/stats", methods=["GET"])
def attendance_stats():
    """Returns dashboard statistics (total, present, absent, rate)."""
    stats = get_dashboard_stats()
    return jsonify(stats)


@app.route("/attendance/mark", methods=["POST"])
def manual_mark_attendance():
    """Manually marks attendance by student id or name."""
    data = request.get_json(silent=True) or {}
    student_id = data.get("id") or data.get("student_id")
    name = data.get("name")
    status = data.get("status", "Present")

    if student_id:
        result = db_mark_attendance(int(student_id), status=status)
    elif name:
        result = mark_attendance_by_name(name, status=status)
    else:
        return jsonify({"success": False, "message": "Student ID or name required"}), 400

    return jsonify(result)


# ---------------- Reports & Exports ----------------

@app.route("/attendance/report/<month>", methods=["GET"])
def monthly_report(month):
    """Returns attendance report for specified month or 'all'."""
    month_arg = None if month.lower() in ["all", "overall"] else month
    report = get_attendance_report(month_arg)
    return jsonify({
        "month": month,
        "report": report
    })


@app.route("/attendance/export", methods=["GET"])
def export_csv_report():
    """Generates and downloads attendance report as CSV."""
    report = get_attendance_report()
    import io
    import csv
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Student ID", "Name", "Roll Number", "Department", "Total Days", "Days Present", "Days Absent", "Attendance %"])
    for r in report:
        writer.writerow([r["id"], r["name"], r["roll"], r["department"], r["total_days"], r["days_present"], r["days_absent"], r["percentage"]])
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=attendance_report.csv"}
    )


# ---------------- Face Training & Recognition Stream ----------------

@app.route("/train", methods=["POST"])
def trigger_training():
    """Retrains the LBPH model on all images in datasets/users."""
    result = train_model()
    try:
        get_recognizer().reload_model()
    except Exception:
        pass
    return jsonify(result)


@app.route("/video_feed")
def video_feed():
    """Live MJPEG video streaming route with face recognition overlay."""
    cam = get_camera()
    det = get_detector()
    rec = get_recognizer()
    return Response(
        generate_camera_stream(cam, detector=det, recognizer=rec, auto_mark=True),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


if __name__ == "__main__":
    print("[INFO] Starting Smart Attendance Server on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
