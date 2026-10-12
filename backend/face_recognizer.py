import cv2
import os
import numpy as np

try:
    from backend.utils.image_utils import preprocess_face
    from backend.database.queries import get_all_students
except ImportError:
    from utils.image_utils import preprocess_face
    from database.queries import get_all_students


class FaceRecognizer:
    def __init__(self, model_path=None):
        """
        Initialize LBPH Face Recognizer with dynamic database label mapping.
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        if model_path is None:
            self.model_path = os.path.join(base_dir, "models", "face_model.yml")
        else:
            self.model_path = model_path

        if not hasattr(cv2, "face") or not hasattr(cv2.face, "LBPHFaceRecognizer_create"):
            raise ImportError(
                "OpenCV face module not found! Ensure 'opencv-contrib-python' is installed."
            )

        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.is_loaded = False
        self.label_map = {}

        self.reload_model()

    def reload_model(self):
        """Reloads trained model weights and student label mapping."""
        # 1. Update label map from database
        try:
            students = get_all_students()
            self.label_map = {int(s["id"]): s["name"] for s in students if "id" in s}
        except Exception:
            self.label_map = {101: "Nanditha Sagar", 1: "Rahul Sharma", 2: "Anita Roy"}

        # 2. Read trained weights
        if os.path.exists(self.model_path) and os.path.getsize(self.model_path) > 0:
            try:
                self.recognizer = cv2.face.LBPHFaceRecognizer_create()
                self.recognizer.read(self.model_path)
                self.is_loaded = True
            except Exception as e:
                print(f"[WARNING] Failed reading face model: {e}")
                self.is_loaded = False
        else:
            self.is_loaded = False

    def recognize_face(self, face_img, threshold=80.0):
        """
        Recognize a face region.
        Returns:
            id: student id or None
            name: matched student name or 'Unknown'
            confidence: distance score (lower is better in LBPH)
            is_recognized: bool
        """
        if not self.is_loaded:
            return {
                "id": None,
                "name": "Model Not Trained",
                "confidence": 999.0,
                "is_recognized": False
            }

        processed = preprocess_face(face_img, target_size=(200, 200))
        if processed is None:
            return {
                "id": None,
                "name": "Unknown",
                "confidence": 999.0,
                "is_recognized": False
            }

        try:
            label, confidence = self.recognizer.predict(processed)

            # In LBPH, confidence is Euclidean distance. Lower = closer match.
            # Confidence <= threshold (e.g. 80.0) is considered a valid match.
            if confidence <= threshold:
                name = self.label_map.get(label, f"Student {label}")
                return {
                    "id": int(label),
                    "name": name,
                    "confidence": round(float(confidence), 1),
                    "is_recognized": True
                }
            else:
                return {
                    "id": None,
                    "name": "Unknown",
                    "confidence": round(float(confidence), 1),
                    "is_recognized": False
                }
        except Exception as e:
            return {
                "id": None,
                "name": "Unknown",
                "confidence": 999.0,
                "is_recognized": False
            }
