"""Interactive HSV tuning tool for the orange ball.

Run from the venv (cv2 only installed there):
    source .venv/bin/activate
    python vision/tune_hsv.py

Aim the webcam at the ball. Adjust sliders until the mask isolates only
the ball. Press 'p' to print the current six values. Press 'q' to quit.

Output values are copied into vision/get_ball() as constants on Monday.
"""

import cv2
import numpy as np


def nothing(x):
    pass


cap = cv2.VideoCapture(0)
cv2.namedWindow("controls")

cv2.createTrackbar("H_lo", "controls", 5, 179, nothing)
cv2.createTrackbar("H_hi", "controls", 25, 179, nothing)
cv2.createTrackbar("S_lo", "controls", 100, 255, nothing)
cv2.createTrackbar("S_hi", "controls", 255, 255, nothing)
cv2.createTrackbar("V_lo", "controls", 100, 255, nothing)
cv2.createTrackbar("V_hi", "controls", 255, 255, nothing)

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    h_lo = cv2.getTrackbarPos("H_lo", "controls")
    h_hi = cv2.getTrackbarPos("H_hi", "controls")
    s_lo = cv2.getTrackbarPos("S_lo", "controls")
    s_hi = cv2.getTrackbarPos("S_hi", "controls")
    v_lo = cv2.getTrackbarPos("V_lo", "controls")
    v_hi = cv2.getTrackbarPos("V_hi", "controls")

    lower = np.array([h_lo, s_lo, v_lo])
    upper = np.array([h_hi, s_hi, v_hi])
    mask = cv2.inRange(hsv, lower, upper)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) > 100:
            x, y, w, h = cv2.boundingRect(largest)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    cv2.imshow("raw", frame)
    cv2.imshow("mask", mask)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('p'):
        print("H: {}-{}  S: {}-{}  V: {}-{}".format(h_lo, h_hi, s_lo, s_hi, v_lo, v_hi))

cap.release()
cv2.destroyAllWindows()
