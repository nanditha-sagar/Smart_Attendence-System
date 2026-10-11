import sqlite3
from datetime import datetime
try:
    from backend.database.db_config import get_db_connection, init_db
except ImportError:
    from database.db_config import get_db_connection, init_db


def ensure_initialized():
    init_db()


def get_all_students():
    """Fetches all registered students."""
    ensure_initialized()
    conn = get_db_connection()
    students = conn.execute(
        "SELECT id, name, roll_number as roll, email, phone, department, created_at FROM students ORDER BY id ASC"
    ).fetchall()
    conn.close()
    return [dict(s) for s in students]


def get_student_by_id(student_id):
    """Fetches a single student by ID."""
    ensure_initialized()
    conn = get_db_connection()
    student = conn.execute(
        "SELECT id, name, roll_number as roll, email, phone, department, created_at FROM students WHERE id = ?",
        (student_id,)
    ).fetchone()
    conn.close()
    return dict(student) if student else None


def get_student_by_name(name):
    """Finds a student by exact or partial name match."""
    ensure_initialized()
    conn = get_db_connection()
    student = conn.execute(
        "SELECT id, name, roll_number as roll FROM students WHERE LOWER(name) LIKE ? LIMIT 1",
        (f"%{name.lower()}%",)
    ).fetchone()
    conn.close()
    return dict(student) if student else None


def add_student(name, roll_number, email="", phone="", department="Computer Science", student_id=None):
    """Adds a new student to the database."""
    ensure_initialized()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if student_id:
            cursor.execute(
                "INSERT INTO students (id, name, roll_number, email, phone, department) VALUES (?, ?, ?, ?, ?, ?)",
                (student_id, name, roll_number, email, phone, department)
            )
            inserted_id = student_id
        else:
            cursor.execute(
                "INSERT INTO students (name, roll_number, email, phone, department) VALUES (?, ?, ?, ?, ?)",
                (name, roll_number, email, phone, department)
            )
            inserted_id = cursor.lastrowid
        conn.commit()
        return inserted_id
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValueError(f"Student with this ID or Roll Number already exists: {e}")
    finally:
        conn.close()


def delete_student(student_id):
    """Deletes a student and their attendance history."""
    ensure_initialized()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM attendance WHERE student_id = ?", (student_id,))
    cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def mark_attendance(student_id, date_str=None, time_str=None, status="Present"):
    """
    Marks attendance for a student on a specific date.
    Prevents duplicate marks on the same day.
    """
    ensure_initialized()
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    if not time_str:
        time_str = datetime.now().strftime("%H:%M:%S")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check student existence
    student = conn.execute("SELECT id, name, roll_number FROM students WHERE id = ?", (student_id,)).fetchone()
    if not student:
        conn.close()
        return {"success": False, "message": f"Student ID {student_id} not found"}

    # Check if already marked
    existing = conn.execute(
        "SELECT id, status, time FROM attendance WHERE student_id = ? AND date = ?",
        (student_id, date_str)
    ).fetchone()

    if existing:
        conn.close()
        return {
            "success": True,
            "already_marked": True,
            "message": f"Attendance already marked for {student['name']}",
            "student_id": student["id"],
            "name": student["name"],
            "status": existing["status"],
            "time": existing["time"],
            "date": date_str
        }

    cursor.execute(
        "INSERT INTO attendance (student_id, date, time, status) VALUES (?, ?, ?, ?)",
        (student_id, date_str, time_str, status)
    )
    conn.commit()
    conn.close()

    return {
        "success": True,
        "already_marked": False,
        "message": f"Attendance marked for {student['name']}",
        "student_id": student["id"],
        "name": student["name"],
        "status": status,
        "time": time_str,
        "date": date_str
    }


def mark_attendance_by_name(name, status="Present"):
    """Marks attendance matching student name."""
    student = get_student_by_name(name)
    if not student:
        return {"success": False, "message": f"Student '{name}' not found"}
    return mark_attendance(student["id"], status=status)


def get_today_attendance():
    """
    Returns today's attendance status for all students.
    Students without a record for today are listed as 'Absent' with time '--'.
    """
    ensure_initialized()
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db_connection()
    query = """
        SELECT 
            s.id,
            s.name,
            s.roll_number as roll,
            s.department,
            COALESCE(a.status, 'Absent') as status,
            COALESCE(a.time, '--') as time,
            COALESCE(a.date, ?) as date
        FROM students s
        LEFT JOIN attendance a ON s.id = a.student_id AND a.date = ?
        ORDER BY s.id ASC
    """
    rows = conn.execute(query, (today, today)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_dashboard_stats():
    """Calculates overall student counts and today's attendance summary."""
    records = get_today_attendance()
    total = len(records)
    present = len([r for r in records if r["status"] == "Present"])
    absent = total - present
    rate = f"{(present / total * 100):.1f}%" if total > 0 else "0%"
    return {
        "total": total,
        "present": present,
        "absent": absent,
        "rate": rate
    }


def get_attendance_report(month_filter=None):
    """
    Generates attendance percentages per student.
    Can filter by month name (e.g. 'January') or number.
    """
    ensure_initialized()
    conn = get_db_connection()

    # Map month names to two-digit strings
    month_map = {
        "january": "01", "february": "02", "march": "03", "april": "04",
        "may": "05", "june": "06", "july": "07", "august": "08",
        "september": "09", "october": "10", "november": "11", "december": "12"
    }

    month_str = None
    if month_filter:
        clean = str(month_filter).strip().lower()
        if clean in month_map:
            month_str = month_map[clean]
        elif clean.isdigit() and 1 <= int(clean) <= 12:
            month_str = f"{int(clean):02d}"

    # Calculate total working/recorded days
    if month_str:
        days_query = "SELECT COUNT(DISTINCT date) as count FROM attendance WHERE strftime('%m', date) = ?"
        total_days = conn.execute(days_query, (month_str,)).fetchone()["count"]
    else:
        days_query = "SELECT COUNT(DISTINCT date) as count FROM attendance"
        total_days = conn.execute(days_query).fetchone()["count"]

    if total_days == 0:
        total_days = 1  # avoid division by zero

    # Get student list
    students = conn.execute("SELECT id, name, roll_number as roll, department FROM students ORDER BY id ASC").fetchall()

    report = []
    for s in students:
        if month_str:
            p_query = """
                SELECT COUNT(*) as count 
                FROM attendance 
                WHERE student_id = ? AND status = 'Present' AND strftime('%m', date) = ?
            """
            present_days = conn.execute(p_query, (s["id"], month_str)).fetchone()["count"]
        else:
            p_query = "SELECT COUNT(*) as count FROM attendance WHERE student_id = ? AND status = 'Present'"
            present_days = conn.execute(p_query, (s["id"],)).fetchone()["count"]

        percentage = round((present_days / total_days) * 100, 1) if total_days > 0 else 0.0

        report.append({
            "id": s["id"],
            "name": s["name"],
            "roll": s["roll"],
            "department": s["department"],
            "total_days": total_days,
            "days_present": present_days,
            "days_absent": max(0, total_days - present_days),
            "percentage": f"{percentage}%",
            "percent_val": percentage
        })

    conn.close()
    return report


def verify_user(username, password):
    """Verifies username and password against users table."""
    ensure_initialized()
    conn = get_db_connection()
    user = conn.execute(
        "SELECT id, username, role FROM users WHERE username = ? AND password = ?",
        (username, password)
    ).fetchone()
    conn.close()
    return dict(user) if user else None
