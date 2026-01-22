import cv2


class FaceDetector:
    def __init__(self):
        """
        Load Haar Cascade face detector
        """
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        if self.face_cascade.empty():
            raise Exception("❌ Haar Cascade file not loaded")

    def detect_faces(self, frame):
        """
        Detect faces in a given frame
        Returns list of face coordinates (x, y, w, h)
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.3,
            minNeighbors=5,
            minSize=(50, 50)
        )

        return faces

    def draw_faces(self, frame, faces):
        """
        Draw rectangles around detected faces
        """
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        return frame


# Test face detection independently
if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    detector = FaceDetector()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        faces = detector.detect_faces(frame)
        frame = detector.draw_faces(frame, faces)

        cv2.imshow("Face Detection Test", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
