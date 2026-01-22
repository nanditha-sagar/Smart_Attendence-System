import cv2
import os

DATASET_PATH = "datasets/users"

def register_face(student_id):
    save_path = os.path.join(DATASET_PATH, str(student_id))
    os.makedirs(save_path, exist_ok=True)

    cap = cv2.VideoCapture(0)
    count = 0

    print("Press C to capture image, Q to quit")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cv2.imshow("Register Face", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('c'):
            count += 1
            cv2.imwrite(f"{save_path}/img{count}.jpg", gray)
            print(f"Saved img{count}.jpg")

        elif key == ord('q') or count >= 20:
            break

    cap.release()
    cv2.destroyAllWindows()
