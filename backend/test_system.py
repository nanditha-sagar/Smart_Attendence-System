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

    def test_13_student_duplicate_checks(self):
        # 101 already exists
        check_res = self.client.get("/students/check?id=101")
        self.assertEqual(check_res.status_code, 200)
        data = check_res.get_json()
        self.assertTrue(data["is_duplicate"])
        self.assertFalse(data["available"])

        # Attempt to insert duplicate ID
        dup_post = self.client.post("/students", json={
            "id": 101,
            "name": "Duplicate Student",
            "roll": "DUP101",
            "department": "Computer Science"
        })
        self.assertEqual(dup_post.status_code, 409)

    def test_14_face_validation_endpoint(self):
        import base64
        # Validate blank/no face
        blank_data = "data:image/jpeg;base64," + base64.b64encode(b"\x00" * 500).decode("utf-8")
        res_blank = self.client.post("/students/validate-face", json={"photo": blank_data})
        self.assertEqual(res_blank.status_code, 400)
        self.assertFalse(res_blank.get_json()["valid"])

        # Validate real face sample
        sample_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasets", "users", "101", "img1.jpg")
        if os.path.exists(sample_path):
            with open(sample_path, "rb") as f:
                face_data = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode("utf-8")
            res_face = self.client.post("/students/validate-face", json={"photo": face_data})
            self.assertEqual(res_face.status_code, 200)
            self.assertTrue(res_face.get_json()["valid"])
            self.assertEqual(res_face.get_json()["face_count"], 1)

    def test_15_register_student_with_photo_and_recognition(self):
        import base64
        from app import get_recognizer
        sample_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasets", "users", "101", "img1.jpg")
        if os.path.exists(sample_path):
            with open(sample_path, "rb") as f:
                face_data = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode("utf-8")

            # Register new student with face
            reg_res = self.client.post("/students", json={
                "id": 303,
                "name": "UnitTest Student",
                "roll": "UT303",
                "department": "AI & Data Science",
                "photo": face_data
            })
            self.assertEqual(reg_res.status_code, 201)
            reg_data = reg_res.get_json()
            self.assertTrue(reg_data["success"])
            self.assertTrue(reg_data["face_enrolled"])

            # Verify recognizer label map includes student immediately
            recognizer = get_recognizer()
            self.assertIn(303, recognizer.label_map)
            self.assertEqual(recognizer.label_map[303], "UnitTest Student")

            # Verify photo retrieval
            photo_res = self.client.get("/students/303/photo")
            self.assertEqual(photo_res.status_code, 200)
            self.assertEqual(photo_res.mimetype, "image/jpeg")

            # Cleanup
            del_res = self.client.delete("/students/303")
            self.assertEqual(del_res.status_code, 200)
            self.assertNotIn(303, recognizer.label_map)


if __name__ == "__main__":
    unittest.main()
