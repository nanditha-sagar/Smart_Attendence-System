import cv2
import time
import numpy as np

try:
    from backend.face_detector import FaceDetector
    from backend.database.queries import mark_attendance
except ImportError:
    from face_detector import FaceDetector
    from database.queries import mark_attendance


class Camera:
    def __init__(self, camera_index=0):
        """
        Initialize camera with safe fallback handling.
        """
        self.camera_index = camera_index
        self.cap = None
        self.is_opened = False
        self._init_camera()

    def _init_camera(self):
        """Tries to connect to the physical webcam."""
        try:
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                # Fallback to default backend
                self.cap = cv2.VideoCapture(self.camera_index)
            self.is_opened = self.cap.isOpened()
        except Exception:
            self.is_opened = False

    def get_frame(self):
        """
        Captures a single frame. If camera unavailable, generates
        a informative placeholder frame.
        """
        if self.cap and self.is_opened:
            ret, frame = self.cap.read()
            if ret and frame is not None:
                return frame

        # Fallback synthetic frame when physical camera is inaccessible
        placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
        placeholder[:] = (30, 30, 35)
        cv2.putText(
            placeholder,
            "Camera Feed (Hardware Busy or Inaccessible)",
            (30, 230),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (100, 200, 255),
            2
        )
        cv2.putText(
            placeholder,
            "Connect Webcam or Test with Sample Images",
            (50, 270),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (180, 180, 180),
            1
        )
        return placeholder

    def get_frame_jpeg(self):
        """Returns frame encoded as JPEG bytes."""
        frame = self.get_frame()
        ret, buffer = cv2.imencode('.jpg', frame)
        if ret:
            return buffer.tobytes()
        return None

    def release(self):
        """Release camera resources."""
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
        self.is_opened = False
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass


def generate_camera_stream(camera, detector=None, recognizer=None, auto_mark=True):
    """
    Generator yielding multipart MJPEG frames with real-time
    face bounding boxes and attendance recognition badges.
    """
    if detector is None:
        try:
            detector = FaceDetector()
        except Exception:
            detector = None

    last_mark_times = {}

    while True:
        frame = camera.get_frame()
        if frame is None:
            time.sleep(0.05)
            continue

        if detector:
            try:
                faces = detector.detect_faces(frame)
                for (x, y, w, h) in faces:
                    label_text = "Detected Face"
                    box_color = (255, 180, 0)

                    if recognizer and recognizer.is_loaded:
                        face_crop = frame[y:y+h, x:x+w]
                        result = recognizer.recognize_face(face_crop)

                        if result["is_recognized"]:
                            student_name = result["name"]
                            student_id = result["id"]
                            label_text = f"{student_name} ({result['confidence']})"
                            box_color = (0, 255, 80)

                            # Auto mark attendance once every 30 seconds per student in video feed
                            now = time.time()
                            if auto_mark and student_id:
                                if student_id not in last_mark_times or (now - last_mark_times[student_id] > 30):
                                    mark_attendance(student_id)
                                    last_mark_times[student_id] = now
                        else:
                            label_text = f"Unknown ({result['confidence']})"
                            box_color = (0, 0, 255)

                    # Draw stylish bounding rectangle
                    cv2.rectangle(frame, (x, y), (x + w, y + h), box_color, 2)

                    # Draw text banner
                    (tw, th), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                    cv2.rectangle(frame, (x, y - 25), (x + tw + 10, y), box_color, -1)
                    cv2.putText(
                        frame,
                        label_text,
                        (x + 5, y - 7),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (0, 0, 0),
                        2
                    )
            except Exception:
                pass

        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue

        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.03)
