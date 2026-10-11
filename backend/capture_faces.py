import cv2
import os

try:
    from backend.face_detector import FaceDetector
    from backend.train_model import train_model
except ImportError:
    from face_detector import FaceDetector
    from train_model import train_model

user_id = input("Enter student ID (number): ").strip()
if not user_id:
    user_id = "1"

save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasets", "users", user_id)
os.makedirs(save_path, exist_ok=True)

detector = FaceDetector()
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    cap = cv2.VideoCapture(0)

count = 0
print("[INFO] Press 'C' to capture face sample, 'Q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    faces = detector.detect_faces(frame)
    display = frame.copy()

    for (x, y, w, h) in faces:
        cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(display, f"Face Detected ({count})", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    cv2.imshow("Capture Faces - Press C to capture, Q to quit", display)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('c') or key == ord('C'):
        if len(faces) > 0:
            x, y, w, h = faces[0]
            face_crop = frame[y:y+h, x:x+w]
        else:
            face_crop = frame
        count += 1
        img_path = os.path.join(save_path, f"img{count}.jpg")
        cv2.imwrite(img_path, face_crop)
        print(f"[SAVED] {img_path}")

    elif key == ord('q') or key == ord('Q') or count >= 20:
        break

cap.release()
cv2.destroyAllWindows()
print(f"[COMPLETED] Captured {count} images for User {user_id}")
if count > 0:
    train_model()
