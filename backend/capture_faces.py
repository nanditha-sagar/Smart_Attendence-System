import cv2
import os

user_id = input("Enter user ID (number): ")
save_path = f"datasets/users/{user_id}"

os.makedirs(save_path, exist_ok=True)

cap = cv2.VideoCapture(0)
count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    cv2.imshow("Capture Faces - Press C to capture, Q to quit", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('c'):
        count += 1
        img_path = f"{save_path}/img{count}.jpg"
        cv2.imwrite(img_path, gray)
        print(f"Saved {img_path}")

    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
