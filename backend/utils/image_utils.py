import cv2
import numpy as np


def preprocess_face(face_img, target_size=(200, 200)):
    """
    Prepares a face image for recognition:
    - Converts to grayscale if needed
    - Applies histogram equalization for lighting invariance
    - Resizes to standard dimension (200x200)
    """
    if face_img is None or face_img.size == 0:
        return None

    if len(face_img.shape) == 3:
        gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
    else:
        gray = face_img.copy()

    # Normalize lighting contrast
    equalized = cv2.equalizeHist(gray)

    # Standardize dimensions
    resized = cv2.resize(equalized, target_size, interpolation=cv2.INTER_AREA)

    return resized


def crop_face(frame, bbox, padding=10):
    """
    Crops face region with safe boundary padding.
    bbox: (x, y, w, h)
    """
    h_max, w_max = frame.shape[:2]
    x, y, w, h = bbox

    x1 = max(0, x - padding)
    y1 = max(0, y - padding)
    x2 = min(w_max, x + w + padding)
    y2 = min(h_max, y + h + padding)

    return frame[y1:y2, x1:x2]
