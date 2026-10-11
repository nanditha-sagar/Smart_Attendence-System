import cv2

try:
    from backend.face_detector import FaceDetector
    from backend.face_recognizer import FaceRecognizer
    from backend.database.queries import mark_attendance
except ImportError:
    from face_detector import FaceDetector
    from face_recognizer import FaceRecognizer
    from database.queries import mark_attendance

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    cap = cv2.VideoCapture(0)

detector = FaceDetector()
recognizer = FaceRecognizer()

print("[INFO] Starting Face Recognition Test. Press 'Q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    faces = detector.detect_faces(frame)

    for (x, y, w, h) in faces:
        face_crop = frame[y:y+h, x:x+w]
        res = recognizer.recognize_face(face_crop)

        name = res.get("name", "Unknown")
        conf = res.get("confidence", 0.0)
        is_rec = res.get("is_recognized", False)

        color = (0, 255, 0) if is_rec else (0, 0, 255)
        display_text = f"{name} ({conf})"

        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        cv2.putText(frame, display_text, (x, max(20, y-10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        if is_rec and res.get("id"):
            mark_attendance(res["id"])

    cv2.imshow("Face Recognition Test", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
