import cv2
import os
import time

try:
    from backend.face_detector import FaceDetector
    from backend.train_model import train_model
except ImportError:
    from face_detector import FaceDetector
    from train_model import train_model

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "datasets", "users")


def register_face(student_id, target_count=20, auto_train=True):
    """
    Captures face samples for a student ID via webcam.
    Detects faces in real time and saves cropped face frames.
    Optionally triggers model retraining once completed.
    """
    save_path = os.path.join(DATASET_PATH, str(student_id))
    os.makedirs(save_path, exist_ok=True)

    detector = FaceDetector()
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("[ERROR] Camera not accessible.")
        return False

    count = 0
    print(f"[INFO] Registering faces for Student ID {student_id}. Target: {target_count} images.")
    print("[INFO] Controls: Press 'C' or Spacebar to capture face, 'Q' to exit.")

    last_auto_capture = time.time()

    while count < target_count:
        ret, frame = cap.read()
        if not ret:
            break

        faces = detector.detect_faces(frame)
        display = frame.copy()

        face_detected = len(faces) > 0
        if face_detected:
            x, y, w, h = faces[0]
            cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(
                display,
                f"Face Ready ({count}/{target_count}) - Press 'C' to save",
                (x, max(20, y - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )
        else:
            cv2.putText(
                display,
                "Position face in center...",
                (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )

        cv2.imshow(f"Registering Student {student_id}", display)
        key = cv2.waitKey(1) & 0xFF

        # Manual capture or auto-capture every 0.6s if face is steady
        should_capture = (key in [ord('c'), ord('C'), 32]) or (face_detected and (time.time() - last_auto_capture > 0.8) and count < target_count)

        if should_capture and face_detected:
            x, y, w, h = faces[0]
            face_crop = frame[y:y+h, x:x+w]
            count += 1
            img_path = os.path.join(save_path, f"img{count}.jpg")
            cv2.imwrite(img_path, face_crop)
            print(f"[SAVED] Sample {count}/{target_count} -> {img_path}")
            last_auto_capture = time.time()

        elif key in [ord('q'), ord('Q'), 27]:
            print("[INFO] Registration cancelled by user.")
            break

    cap.release()
    cv2.destroyAllWindows()

    if count > 0 and auto_train:
        print("[INFO] Automatically training recognizer on new dataset...")
        train_model()

    return count >= target_count


if __name__ == "__main__":
    sid = input("Enter Student ID to register: ").strip()
    if sid:
        register_face(sid)
