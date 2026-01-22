from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)   # Allow frontend to access backend

# ---------------------------------
# Dummy Data (Replace with DB later)
# ---------------------------------

students = [
    {"id": 1, "name": "Rahul", "roll": "CS101"},
    {"id": 2, "name": "Anita", "roll": "CS102"}
]

attendance_today = [
    {"name": "Rahul", "status": "Present", "time": "09:01"},
    {"name": "Anita", "status": "Absent", "time": "--"}
]

# ---------------------------------
# Routes / APIs
# ---------------------------------

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Smart Attendance Backend Running"})


# 🔹 Login API
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if username == "admin" and password == "admin123":
        return jsonify({"success": True, "message": "Login successful"})
    else:
        return jsonify({"success": False, "message": "Invalid credentials"}), 401


# 🔹 Get all students (IMPORTANT)
@app.route("/students", methods=["GET"])
def get_students():
    return jsonify(students)


# 🔹 Get today's attendance
@app.route("/attendance/today", methods=["GET"])
def get_today_attendance():
    return jsonify(attendance_today)


# 🔹 Get monthly attendance report
@app.route("/attendance/report/<month>", methods=["GET"])
def get_report(month):
    report = [
        {"name": "Rahul", "percentage": "92%"},
        {"name": "Anita", "percentage": "85%"}
    ]
    return jsonify({
        "month": month,
        "report": report
    })


# ---------------------------------
# Run Server
# ---------------------------------
if __name__ == "__main__":
    app.run(debug=True)
