import cv2
from face_detector import FaceDetector
from face_recognizer import FaceRecognizer

cap = cv2.VideoCapture(0)
detector = FaceDetector()
recognizer = FaceRecognizer()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    faces = detector.detect_faces(frame)

    for (x, y, w, h) in faces:
        face_img = cv2.cvtColor(frame[y:y+h, x:x+w], cv2.COLOR_BGR2GRAY)
        face_img = cv2.resize(face_img, (200, 200))

        name, confidence = recognizer.recognize_face(face_img)

        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame, f"{name}", (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    cv2.imshow("Face Recognition Test", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
