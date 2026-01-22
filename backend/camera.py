import cv2


class Camera:
    def __init__(self, camera_index=0):
        """
        Initialize camera
        camera_index = 0 (default laptop webcam)
        """
        self.cap = cv2.VideoCapture(camera_index)

        if not self.cap.isOpened():
            raise Exception("❌ Camera not accessible")

    def get_frame(self):
        """
        Capture a single frame from the camera
        Returns the frame if successful
        """
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    def show_camera(self):
        """
        Display live camera feed (for testing)
        Press 'q' to quit
        """
        while True:
            frame = self.get_frame()
            if frame is None:
                break

            cv2.imshow("Camera Feed", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.release()

    def release(self):
        """
        Release camera resources
        """
        self.cap.release()
        cv2.destroyAllWindows()


# Run this file directly to test camera
if __name__ == "__main__":
    cam = Camera()
    cam.show_camera()
