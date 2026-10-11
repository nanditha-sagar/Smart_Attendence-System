import os
import sqlite3
import pandas as pd
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "backend", "database", "attendance.db")
OUTPUT_PATH = os.path.join(BASE_DIR, "monthly_summary.csv")


def generate_monthly_report(target_month=None):
    """
    Generates a detailed monthly attendance report using Pandas.
    target_month: '01' to '12' (defaults to current month)
    """
    if not target_month:
        target_month = datetime.now().strftime("%m")
    else:
        target_month = f"{int(target_month):02d}"

    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database file not found at: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT 
            s.id as student_id,
            s.name,
            s.roll_number,
            s.department,
            a.date,
            a.status
        FROM students s
        LEFT JOIN attendance a ON s.id = a.student_id AND strftime('%m', a.date) = ?
    """
    df = pd.read_sql_query(query, conn, params=(target_month,))
    conn.close()

    total_recorded_days = df['date'].dropna().nunique()
    if total_recorded_days == 0:
        total_recorded_days = 1

    summary = []
    for sid, group in df.groupby(['student_id', 'name', 'roll_number', 'department']):
        student_id, name, roll_number, department = sid
        present_days = group[group['status'] == 'Present']['status'].count()
        absent_days = max(0, total_recorded_days - present_days)
        pct = round((present_days / total_recorded_days) * 100, 2)
        summary.append({
            "Student ID": student_id,
            "Name": name,
            "Roll Number": roll_number,
            "Department": department,
            "Working Days": total_recorded_days,
            "Days Present": present_days,
            "Days Absent": absent_days,
            "Attendance %": pct
        })

    report_df = pd.DataFrame(summary)
    print(f"\n--- Monthly Attendance Report (Month: {target_month}) ---")
    print(report_df.to_string(index=False))

    report_df.to_csv(OUTPUT_PATH, index=False)
    print(f"\n[SUCCESS] Monthly report saved to: {OUTPUT_PATH}")
    return report_df


if __name__ == "__main__":
    generate_monthly_report()
