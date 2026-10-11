try:
    from backend.database.queries import (
        mark_attendance as db_mark_attendance,
        mark_attendance_by_name as db_mark_by_name,
        get_today_attendance as db_get_today_attendance,
        get_attendance_report as db_get_report,
        get_dashboard_stats as db_get_stats
    )
except ImportError:
    from database.queries import (
        mark_attendance as db_mark_attendance,
        mark_attendance_by_name as db_mark_by_name,
        get_today_attendance as db_get_today_attendance,
        get_attendance_report as db_get_report,
        get_dashboard_stats as db_get_stats
    )


def mark_attendance(identifier):
    """
    Marks attendance for a student by either integer ID or string name.
    Ensures attendance is recorded in SQLite database.
    """
    if isinstance(identifier, int) or (isinstance(identifier, str) and identifier.isdigit()):
        return db_mark_attendance(int(identifier))
    else:
        return db_mark_by_name(str(identifier))


def get_today_attendance():
    """
    Returns today's attendance records for all enrolled students.
    """
    return db_get_today_attendance()


def get_monthly_report(month=None):
    """
    Generates monthly or overall attendance report.
    """
    return db_get_report(month)


def get_attendance_stats():
    """
    Returns counts of total students, present today, and absent today.
    """
    return db_get_stats()


if __name__ == "__main__":
    print("[INFO] Today's attendance:", get_today_attendance())
    print("[INFO] Dashboard stats:", get_attendance_stats())
