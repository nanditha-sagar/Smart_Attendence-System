import os
import sqlite3
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "backend", "database", "attendance.db")
OUTPUT_PATH = os.path.join(BASE_DIR, "attendance.csv")


def export_attendance_to_csv():
    """Exports all attendance records from the SQLite database to attendance.csv."""
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database file not found at: {DB_PATH}")
        return False

    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT 
            a.id as record_id,
            s.id as student_id,
            s.name,
            s.roll_number,
            s.department,
            a.date,
            a.time,
            a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        ORDER BY a.date DESC, a.time DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    df.to_csv(OUTPUT_PATH, index=False)
    print(f"[SUCCESS] Exported {len(df)} records to: {OUTPUT_PATH}")
    return True


if __name__ == "__main__":
    export_attendance_to_csv()
