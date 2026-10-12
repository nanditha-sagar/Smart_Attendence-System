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


def decode_image_bytes(image_input):
    """
    Decodes an image from bytes, raw base64 string, or data URL (e.g. data:image/jpeg;base64,...).
    Returns cv2 BGR image (np.ndarray) or None if invalid.
    """
    import base64

    if image_input is None:
        return None

    try:
        if isinstance(image_input, bytes):
            raw_bytes = image_input
        elif isinstance(image_input, str):
            clean_str = image_input.strip()
            if "," in clean_str:
                clean_str = clean_str.split(",", 1)[1]
            raw_bytes = base64.b64decode(clean_str)
        else:
            return None

        arr = np.frombuffer(raw_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is not None and img.size > 0:
            return img
    except Exception as e:
        print(f"[WARNING] Image decoding error: {e}")
    return None


def compute_face_encoding(face_img):
    """
    Computes a standardized 128-dimensional normalized facial gradient
    and spatial descriptor vector for database storage and feature matching.
    Returns: list of floats (length 128, rounded to 5 decimal places)
    """
    if face_img is None or face_img.size == 0:
        return []

    proc = preprocess_face(face_img, target_size=(128, 128))
    if proc is None:
        return []

    # Compute horizontal and vertical gradients
    gx = cv2.Sobel(proc, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(proc, cv2.CV_32F, 0, 1, ksize=3)
    mag, ang = cv2.cartToPolar(gx, gy, angleInDegrees=True)

    # Divide into 4x4 spatial grid (16 cells) with 8 orientation bins each -> 16 * 8 = 128 dimensions
    encoding = []
    cell_h, cell_w = 32, 32
    for r in range(4):
        for c in range(4):
            c_mag = mag[r * cell_h:(r + 1) * cell_h, c * cell_w:(c + 1) * cell_w]
            c_ang = ang[r * cell_h:(r + 1) * cell_h, c * cell_w:(c + 1) * cell_w]
            hist, _ = np.histogram(c_ang, bins=8, range=(0, 360), weights=c_mag)
            encoding.extend(hist)

    vec = np.array(encoding, dtype=np.float32)
    norm = np.linalg.norm(vec)
    if norm > 1e-6:
        vec = vec / norm
    return [round(float(v), 5) for v in vec]


def generate_augmented_samples(face_crop, target_count=8):
    """
    Generates realistic lighting, rotation, and contrast variations from a single
    face crop to train robust LBPH face recognizers immediately.
    """
    if face_crop is None or face_crop.size == 0:
        return []

    samples = [face_crop.copy()]

    try:
        # 1. Brightness +15%
        hsv = cv2.cvtColor(face_crop, cv2.COLOR_BGR2HSV).astype(np.float32)
        h, s, v = cv2.split(hsv)
        v_bright = np.clip(v * 1.15, 0, 255)
        samples.append(cv2.cvtColor(cv2.merge([h, s, v_bright]).astype(np.uint8), cv2.COLOR_HSV2BGR))

        # 2. Brightness -15%
        v_dark = np.clip(v * 0.85, 0, 255)
        samples.append(cv2.cvtColor(cv2.merge([h, s, v_dark]).astype(np.uint8), cv2.COLOR_HSV2BGR))

        # 3. Slight Rotations
        ch, cw = face_crop.shape[:2]
        for angle in [4, -4]:
            M = cv2.getRotationMatrix2D((cw / 2, ch / 2), angle, 1.0)
            samples.append(cv2.warpAffine(face_crop, M, (cw, ch), borderMode=cv2.BORDER_REFLECT))

        # 4. Contrast enhancement
        samples.append(cv2.convertScaleAbs(face_crop, alpha=1.1, beta=0))

        # 5. Contrast reduction / softening
        samples.append(cv2.convertScaleAbs(face_crop, alpha=0.9, beta=5))

        # 6. Horizontal flip
        samples.append(cv2.flip(face_crop, 1))
    except Exception as e:
        print(f"[WARNING] Augmentation error: {e}")

    return samples[:target_count]


def save_student_face_samples(student_id, face_crop, dataset_root=None):
    """
    Saves face samples into datasets/users/<student_id> for model training.
    Returns:
        dict with saved_count (int) and primary_path (str)
    """
    import os
    if dataset_root is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dataset_root = os.path.join(base_dir, "datasets", "users")

    user_dir = os.path.join(dataset_root, str(student_id))
    os.makedirs(user_dir, exist_ok=True)

    samples = generate_augmented_samples(face_crop, target_count=8)
    saved_files = []

    for i, sample in enumerate(samples, start=1):
        file_path = os.path.join(user_dir, f"img{i}.jpg")
        cv2.imwrite(file_path, sample)
        saved_files.append(file_path)

    # Relative path for database reference
    rel_path = f"datasets/users/{student_id}/img1.jpg"
    return {
        "saved_count": len(saved_files),
        "primary_path": rel_path,
        "absolute_dir": user_dir
    }
