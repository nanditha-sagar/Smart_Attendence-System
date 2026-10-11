import os
from flask import Flask, jsonify, request, Response, send_from_directory
from flask_cors import CORS

try:
    from backend.database.db_config import init_db
    from backend.database.queries import (
        get_all_students,
        get_student_by_id,
        add_student,
        delete_student,
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
except ImportError:
    from database.db_config import init_db
    from database.queries import (
        get_all_students,
        get_student_by_id,
        add_student,
        delete_student,
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
    """Returns list of registered students."""
    students = get_all_students()
    return jsonify(students)


@app.route("/students", methods=["POST"])
def register_student():
    """Registers a new student."""
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    roll = data.get("roll") or data.get("roll_number", "").strip()
    email = data.get("email", "").strip()
    department = data.get("department", "Computer Science").strip()
    student_id = data.get("id")

    if not name or not roll:
        return jsonify({"success": False, "message": "Name and Roll Number are required"}), 400

    try:
        new_id = add_student(
            name=name,
            roll_number=roll,
            email=email,
            department=department,
            student_id=int(student_id) if student_id else None
        )
        # Reload label map in recognizer
        try:
            get_recognizer().reload_model()
        except Exception:
            pass

        return jsonify({
            "success": True,
            "message": f"Student '{name}' registered successfully",
            "id": new_id
        }), 201
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 409
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {e}"}), 500


@app.route("/students/<int:student_id>", methods=["DELETE"])
def remove_student(student_id):
    """Deletes a student."""
    success = delete_student(student_id)
    if success:
        try:
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
