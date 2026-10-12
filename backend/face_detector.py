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

    def validate_face_image(self, frame):
        """
        Validates that exactly one clear face is present in the image.
        Returns:
            dict:
                valid (bool): True if exactly one valid face detected
                face_count (int): Number of detected faces
                face_bbox (list): [x, y, w, h] of detected face or None
                face_crop (np.ndarray): Cropped face region or None
                message (str): User-friendly descriptive validation message
        """
        if frame is None or getattr(frame, "size", 0) == 0:
            return {
                "valid": False,
                "face_count": 0,
                "face_bbox": None,
                "face_crop": None,
                "message": "Invalid or unreadable image file. Please provide a valid JPG, PNG, or WEBP."
            }

        # Detect with primary parameters
        faces = self.detect_faces(frame, scale_factor=1.15, min_neighbors=5, min_size=(50, 50))

        # If no face detected, try slightly more permissive parameters for edge lighting
        if len(faces) == 0:
            faces = self.detect_faces(frame, scale_factor=1.1, min_neighbors=4, min_size=(40, 40))

        if len(faces) == 0:
            return {
                "valid": False,
                "face_count": 0,
                "face_bbox": None,
                "face_crop": None,
                "message": "No face detected in the photo. Please ensure the face is centered, well-lit, and facing the camera directly."
            }

        if len(faces) > 1:
            return {
                "valid": False,
                "face_count": len(faces),
                "face_bbox": [[int(b[0]), int(b[1]), int(b[2]), int(b[3])] for b in faces],
                "face_crop": None,
                "message": f"Multiple faces detected ({len(faces)}). Please provide a photo containing only one student."
            }

        # Exactly 1 face
        x, y, w, h = faces[0]
        h_max, w_max = frame.shape[:2]
        pad = int(min(w, h) * 0.12)
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(w_max, x + w + pad)
        y2 = min(h_max, y + h + pad)
        face_crop = frame[y1:y2, x1:x2]

        return {
            "valid": True,
            "face_count": 1,
            "face_bbox": [int(x), int(y), int(w), int(h)],
            "face_crop": face_crop,
            "message": "Face detected and validated successfully."
        }


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
