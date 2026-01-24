from datetime import datetime

attendance_records = []


def mark_attendance(name):
    """
    Marks attendance for a recognized person.
    Ensures attendance is marked only once per day.
    """

    today = datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.now().strftime("%H:%M:%S")

    for record in attendance_records:
        if record["name"] == name and record["date"] == today:
            return {
                "message": "Attendance already marked",
                "name": name,
                "date": today
            }

    record = {
        "name": name,
        "date": today,
        "time": current_time,
        "status": "Present"
    }

    attendance_records.append(record)

    return {
        "message": "Attendance marked successfully",
        "record": record
    }


def get_today_attendance():
    """
    Returns today's attendance records
    """
    today = datetime.now().strftime("%Y-%m-%d")
    return [r for r in attendance_records if r["date"] == today]
