"""Pure OpenCV detection helpers. No NAOqi.

Splits the HSV-mask-contour-boundingbox pipeline out of tune_hsv.py so it can
be reused by vision/real.py (production) and tune_hsv.py (tuning tool).

Imports cv2 + numpy, so only runs in environments that have them
(Py3 venv on laptop, or onboard the NAO).
"""

import cv2
import numpy as np

from vision.constants import (
    ORANGE_HSV_LOWER,
    ORANGE_HSV_UPPER,
    MIN_CONTOUR_AREA_PX,
)


def detect_largest_blob(frame, hsv_lower, hsv_upper, min_area):
    """Find the largest blob matching the given HSV range in a BGR frame.

    frame: BGR image (numpy array as returned by cv2.VideoCapture / cv2.imread)
    hsv_lower, hsv_upper: 3-tuples (h, s, v)
    min_area: minimum contour area in pixels^2 to count as a real detection
    Returns (x, y, w, h) bounding box tuple, or None.
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array(hsv_lower), np.array(hsv_upper))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < min_area:
        return None
    return cv2.boundingRect(largest)


def detect_ball_pixel(frame):
    """Locate the orange ball center in a BGR frame.

    Returns (u, v) pixel coords of the bounding box center, or None.
    """
    bbox = detect_largest_blob(
        frame, ORANGE_HSV_LOWER, ORANGE_HSV_UPPER, MIN_CONTOUR_AREA_PX,
    )
    if bbox is None:
        return None
    x, y, w, h = bbox
    return (x + w // 2, y + h // 2)
