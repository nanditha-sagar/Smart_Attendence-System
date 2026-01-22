import pandas as pd
import numpy as np

# Load attendance data (from CSV or database export)
# CSV format: id, name, date, status
data = pd.read_csv("attendance.csv")

# Display first few rows
print("\nAttendance Data Preview:")
print(data.head())

# Total number of days
total_days = data['date'].nunique()

print("\nTotal Working Days:", total_days)

# Attendance count per student
attendance_count = data[data['status'] == 'Present'].groupby('name').count()['status']

# Attendance percentage
attendance_percentage = (attendance_count / total_days) * 100

# Convert to DataFrame
report = pd.DataFrame({
    'Total Days': total_days,
    'Days Present': attendance_count,
    'Attendance %': attendance_percentage.round(2)
})

# Fill absent students with 0
report = report.fillna(0)

print("\nAttendance Analysis Report:")
print(report)

# Save report to CSV
report.to_csv("attendance_report.csv")

print("\nAttendance report saved as attendance_report.csv")
