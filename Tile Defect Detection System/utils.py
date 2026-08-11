import cv2
import numpy as np

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------
PIXEL_TO_MM = 0.1

CRACK_LIMIT = 8        # mm
SPOT_LIMIT = 3
DEFECT_LIMIT = 1.5     # %

# ------------------------------------------------------------
# MAIN INSPECTION FUNCTION
# ------------------------------------------------------------
def inspect_tile(image, debug=False):
    """
    Inspect a tile image for cracks and spots.

    Args:
        image (np.array): BGR image
        debug (bool): if True, draw debug labels

    Returns:
        img (np.array): processed image
        crack_mm (float)
        spots (int)
        defect_percent (float)
        result (str): GOOD / DEFECTIVE
    """

    # ----------------------------
    # PREPROCESSING
    # ----------------------------
    img = cv2.resize(image, (512, 512))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # ----------------------------
    # CRACK DETECTION (EDGE BASED)
    # ----------------------------
    edges = cv2.Canny(blur, 60, 160)
    edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), 1)

    contours, _ = cv2.findContours(
        edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    total_len = 0
    for c in contours:
        if cv2.contourArea(c) > 200:
            total_len += cv2.arcLength(c, False)
            cv2.drawContours(img, [c], -1, (255, 0, 0), 2)

    crack_mm = total_len * PIXEL_TO_MM

    # ----------------------------
    # SPOT DETECTION (SHAPE BASED)
    # ----------------------------
    thresh = cv2.adaptiveThreshold(
        blur, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        15, 3
    )

    thresh = cv2.morphologyEx(
        thresh,
        cv2.MORPH_OPEN,
        np.ones((3, 3), np.uint8),
        iterations=2
    )

    contours, _ = cv2.findContours(
        thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    spots = 0
    spot_area = 0

    for c in contours:

        a = cv2.contourArea(c)
        if a < 80 or a > 3000:
            continue

        x, y, w, h = cv2.boundingRect(c)

        # ---- shape metrics ----
        aspect_ratio = max(w, h) / (min(w, h) + 1e-5)

        hull = cv2.convexHull(c)
        hull_area = cv2.contourArea(hull)
        solidity = a / (hull_area + 1e-5)

        # ---- REAL SPOT ----
        if aspect_ratio < 2.5 and solidity > 0.6:
            spots += 1
            spot_area += a
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)

            if debug:
                cv2.putText(
                    img, "SPOT",
                    (x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.45,
                    (0, 255, 0),
                    1
                )

        # ---- CRACK FRAGMENT (NOT A SPOT) ----
        else:
            if debug:
                cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 1)
                cv2.putText(
                    img, "CRACK-FRAG",
                    (x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    (255, 0, 0),
                    1
                )

    # ----------------------------
    # DEFECT PERCENTAGE
    # ----------------------------
    tile_area = 512 * 512
    defect_percent = ((spot_area + total_len * 3) / tile_area) * 100

    # ----------------------------
    # FINAL DECISION
    # ----------------------------
    if (
        crack_mm > CRACK_LIMIT or
        spots >= SPOT_LIMIT or
        defect_percent > DEFECT_LIMIT
    ):
        result = "DEFECTIVE"
    else:
        result = "GOOD"

    return img, crack_mm, spots, defect_percent, result
