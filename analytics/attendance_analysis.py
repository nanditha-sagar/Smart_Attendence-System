import pandas as pd
import numpy as np


data = pd.read_csv("attendance.csv")

print("\nAttendance Data Preview:")
print(data.head())

total_days = data['date'].nunique()

print("\nTotal Working Days:", total_days)

attendance_count = data[data['status'] == 'Present'].groupby('name').count()['status']

attendance_percentage = (attendance_count / total_days) * 100

report = pd.DataFrame({
    'Total Days': total_days,
    'Days Present': attendance_count,
    'Attendance %': attendance_percentage.round(2)
})

report = report.fillna(0)

print("\nAttendance Analysis Report:")
print(report)

report.to_csv("attendance_report.csv")

print("\nAttendance report saved as attendance_report.csv")
