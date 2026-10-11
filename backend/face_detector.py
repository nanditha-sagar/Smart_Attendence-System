import cv2
import os
import urllib.request


class FaceDetector:
    def __init__(self, cascade_path=None):
        """
        Load Haar Cascade face detector.
        Searches multiple locations and downloads fallback if needed.
        """
        self.face_cascade = None
        base_dir = os.path.dirname(os.path.abspath(__file__))
        local_model_path = os.path.join(base_dir, "models", "haarcascade_frontalface_default.xml")

        candidates = []
        if cascade_path:
            candidates.append(cascade_path)
        candidates.append(local_model_path)
        if hasattr(cv2, "data") and hasattr(cv2.data, "haarcascades"):
            candidates.append(os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"))

        # Try existing candidates
        for path in candidates:
            if os.path.exists(path):
                cascade = cv2.CascadeClassifier(path)
                if not cascade.empty():
                    self.face_cascade = cascade
                    self.cascade_path = path
                    break

        # If not loaded, download to local models directory
        if self.face_cascade is None or self.face_cascade.empty():
            try:
                os.makedirs(os.path.dirname(local_model_path), exist_ok=True)
                url = "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml"
                print("Downloading haarcascade_frontalface_default.xml...")
                urllib.request.urlretrieve(url, local_model_path)
                cascade = cv2.CascadeClassifier(local_model_path)
                if not cascade.empty():
                    self.face_cascade = cascade
                    self.cascade_path = local_model_path
            except Exception as e:
                print(f"Warning: Could not download cascade XML: {e}")

        if self.face_cascade is None or self.face_cascade.empty():
            raise RuntimeError("[ERROR] Haar Cascade file not loaded. Ensure haarcascade_frontalface_default.xml is present.")

    def detect_faces(self, frame, scale_factor=1.2, min_neighbors=5, min_size=(40, 40)):
        """
        Detect faces in a given frame.
        Returns list of bounding boxes (x, y, w, h).
        """
        if frame is None:
            return []

        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=scale_factor,
            minNeighbors=min_neighbors,
            minSize=min_size
        )

        return list(faces)

    def draw_faces(self, frame, faces, color=(0, 255, 0), thickness=2):
        """
        Draw rectangles around detected faces.
        """
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, thickness)
        return frame


if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    detector = FaceDetector()
    print("Testing FaceDetector. Press 'q' to quit.")

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
