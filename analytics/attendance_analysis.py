import os
import pandas as pd
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "backend", "database", "attendance.db")
CSV_PATH = os.path.join(BASE_DIR, "attendance.csv")


def load_attendance_data():
    """Loads data from attendance.csv or directly from SQLite database."""
    if os.path.exists(CSV_PATH) and os.path.getsize(CSV_PATH) > 0:
        return pd.read_csv(CSV_PATH)
    elif os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        query = """
            SELECT 
                a.id, 
                s.name, 
                s.roll_number, 
                s.department, 
                a.date, 
                a.time, 
                a.status 
            FROM attendance a
            JOIN students s ON a.student_id = s.id
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    else:
        # Fallback dummy sample
        return pd.DataFrame([
            {"name": "Nanditha Sagar", "date": "2026-10-10", "status": "Present"},
            {"name": "Rahul Sharma", "date": "2026-10-10", "status": "Present"},
            {"name": "Anita Roy", "date": "2026-10-10", "status": "Absent"}
        ])


def analyze_attendance():
    """Performs statistical attendance analysis and exports a summary report."""
    data = load_attendance_data()

    if data.empty:
        print("[WARNING] No attendance records found to analyze.")
        return

    print("\n--- Attendance Data Preview ---")
    print(data.head())

    total_days = data['date'].nunique()
    print("\nTotal Working / Recorded Days:", total_days)

    present_df = data[data['status'] == 'Present']
    attendance_count = present_df.groupby('name')['status'].count()

    # Reindex against all students
    all_names = data['name'].unique()
    attendance_count = attendance_count.reindex(all_names, fill_value=0)

    attendance_percentage = (attendance_count / max(1, total_days)) * 100

    report = pd.DataFrame({
        'Total Days': total_days,
        'Days Present': attendance_count,
        'Attendance %': attendance_percentage.round(2)
    })

    print("\n--- Attendance Analysis Report ---")
    print(report)

    output_csv = os.path.join(BASE_DIR, "attendance_report.csv")
    report.to_csv(output_csv)
    print(f"\n[SUCCESS] Report successfully exported to: {output_csv}")
    return report


if __name__ == "__main__":
    analyze_attendance()
