"""
Comprehensive System Verification Test Suite
Tests all database operations, face detection, face recognition, model training,
and Flask HTTP endpoints.
"""

import os
import sys
import unittest
import json

# Ensure project backend in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_config import init_db, get_db_connection
from database.queries import (
    get_all_students,
    get_student_by_id,
    add_student,
    delete_student,
    mark_attendance,
    get_today_attendance,
    get_attendance_report,
    get_dashboard_stats,
    verify_user
)
from face_detector import FaceDetector
from face_recognizer import FaceRecognizer
from train_model import train_model
from app import app


class SmartAttendanceTestSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = app.test_client()

    def test_01_db_admin_verification(self):
        user = verify_user("admin", "admin123")
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "admin")

        invalid = verify_user("admin", "wrongpassword")
        self.assertIsNone(invalid)

    def test_02_db_student_crud(self):
        # Add test student
        test_roll = "TEST999"
        new_id = add_student(name="Test Student", roll_number=test_roll, department="Testing")
        self.assertIsNotNone(new_id)

        student = get_student_by_id(new_id)
        self.assertIsNotNone(student)
        self.assertEqual(student["roll"], test_roll)

        # Mark attendance
        att_res = mark_attendance(new_id, status="Present")
        self.assertTrue(att_res["success"])

        # Check duplicate prevent
        dup_res = mark_attendance(new_id, status="Present")
        self.assertTrue(dup_res.get("already_marked", False))

        # Cleanup test student
        deleted = delete_student(new_id)
        self.assertTrue(deleted)

    def test_03_today_attendance_and_stats(self):
        today = get_today_attendance()
        self.assertIsInstance(today, list)
        self.assertGreater(len(today), 0)

        stats = get_dashboard_stats()
        self.assertIn("total", stats)
        self.assertIn("present", stats)
        self.assertIn("absent", stats)

    def test_04_attendance_reports(self):
        report = get_attendance_report()
        self.assertIsInstance(report, list)
        self.assertGreater(len(report), 0)
        self.assertIn("percentage", report[0])

    def test_05_face_detector(self):
        detector = FaceDetector()
        self.assertIsNotNone(detector.face_cascade)
        self.assertFalse(detector.face_cascade.empty())

    def test_06_model_training_and_recognition(self):
        train_res = train_model()
        self.assertTrue(train_res["success"])

        recognizer = FaceRecognizer()
        self.assertTrue(recognizer.is_loaded)

    def test_07_api_login(self):
        res = self.client.post("/login", json={"username": "admin", "password": "admin123"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])

        fail_res = self.client.post("/login", json={"username": "admin", "password": "bad"})
        self.assertEqual(fail_res.status_code, 401)

    def test_08_api_students(self):
        res = self.client.get("/students")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_09_api_today_attendance(self):
        res = self.client.get("/attendance/today")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIsInstance(data, list)

    def test_10_api_report(self):
        res = self.client.get("/attendance/report/October")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("report", data)

    def test_11_api_export_csv(self):
        res = self.client.get("/attendance/export")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, "text/csv")
        self.assertIn("Student ID,Name", res.get_data(as_text=True))

    def test_12_frontend_static_serving(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Smart Attendance", res.get_data(as_text=True))

        res_dash = self.client.get("/dashboard.html")
        self.assertEqual(res_dash.status_code, 200)

        res_css = self.client.get("/css/style.css")
        self.assertEqual(res_css.status_code, 200)

        res_api_js = self.client.get("/js/api.js")
        self.assertEqual(res_api_js.status_code, 200)


if __name__ == "__main__":
    unittest.main()
