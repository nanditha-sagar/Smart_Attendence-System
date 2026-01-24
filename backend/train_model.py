import cv2
import os
import numpy as np


DATASET_PATH = "datasets/users"
MODEL_PATH = "models/face_model.yml"


def load_dataset():
    faces = []
    labels = []

    for user_folder in os.listdir(DATASET_PATH):
        user_path = os.path.join(DATASET_PATH, user_folder)

        if not os.path.isdir(user_path):
            continue

        label = int(user_folder)

        for image_name in os.listdir(user_path):
            image_path = os.path.join(user_path, image_name)

            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

            if img is None:
                continue

            img = cv2.resize(img, (200, 200))

            faces.append(img)
            labels.append(label)

    return faces, labels


def train_model():
    faces, labels = load_dataset()

    if len(faces) == 0:
        print("❌ No training data found")
        return

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(labels))

    os.makedirs("models", exist_ok=True)
    recognizer.save(MODEL_PATH)

    print("✅ Model trained and saved at:", MODEL_PATH)


if __name__ == "__main__":
    train_model()
