import cv2
import os
import numpy as np


class FaceRecognizer:
    def __init__(self, model_path="models/face_model.yml"):
        """
        Initialize LBPH Face Recognizer
        """
        self.model_path = model_path
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()

        if os.path.exists(self.model_path):
            self.recognizer.read(self.model_path)
        else:
            print("⚠️ Trained model not found. Train the model first.")

        self.label_map = {
            1: "Rahul",
            2: "Anita"
        }

    def recognize_face(self, face_img):
        """
        Recognize a single face image (grayscale, cropped)
        Returns name and confidence
        """
        label, confidence = self.recognizer.predict(face_img)

        if confidence < 70:
            name = self.label_map.get(label, "Unknown")
        else:
            name = "Unknown"

        return name, confidence
