import cv2
import os
import numpy as np

try:
    from backend.face_detector import FaceDetector
    from backend.utils.image_utils import preprocess_face
except ImportError:
    from face_detector import FaceDetector
    from utils.image_utils import preprocess_face

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "datasets", "users")
MODEL_PATH = os.path.join(BASE_DIR, "models", "face_model.yml")


def load_dataset():
    """
    Scans datasets/users for each student's face images.
    Crops and normalizes faces using FaceDetector and image_utils.
    """
    if not os.path.exists(DATASET_PATH):
        os.makedirs(DATASET_PATH, exist_ok=True)
        return [], []

    detector = FaceDetector()
    faces = []
    labels = []
    user_folders = [f for f in os.listdir(DATASET_PATH) if os.path.isdir(os.path.join(DATASET_PATH, f))]

    for user_folder in user_folders:
        try:
            label = int(user_folder)
        except ValueError:
            continue

        user_path = os.path.join(DATASET_PATH, user_folder)
        image_files = [f for f in os.listdir(user_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

        for image_name in image_files:
            image_path = os.path.join(user_path, image_name)
            img = cv2.imread(image_path)

            if img is None or img.size == 0:
                continue

            # Detect face inside frame
            detected = detector.detect_faces(img)
            if len(detected) > 0:
                x, y, w, h = detected[0]
                face_crop = img[y:y+h, x:x+w]
            else:
                # If already cropped or close up
                face_crop = img

            processed = preprocess_face(face_crop, target_size=(200, 200))
            if processed is not None:
                faces.append(processed)
                labels.append(label)

    return faces, labels


def train_model():
    """
    Trains LBPH face recognizer model on all available student faces
    and saves to models/face_model.yml.
    """
    faces, labels = load_dataset()

    if len(faces) == 0:
        print("[WARNING] No valid face training data found in datasets/users")
        return {
            "success": False,
            "message": "No training images found. Register student faces first.",
            "faces_count": 0,
            "users_count": 0
        }

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(labels, dtype=np.int32))

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    recognizer.save(MODEL_PATH)

    unique_users = len(set(labels))
    print(f"[SUCCESS] Model trained successfully with {len(faces)} samples across {unique_users} user(s).")
    print(f"[INFO] Saved to: {MODEL_PATH}")

    return {
        "success": True,
        "message": f"Successfully trained model on {len(faces)} images across {unique_users} student(s).",
        "faces_count": len(faces),
        "users_count": unique_users
    }


if __name__ == "__main__":
    train_model()
