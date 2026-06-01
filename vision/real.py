"""Production vision implementation backed by NAOqi + OpenCV.

Drop-in replacement for vision/mock.py when running on or against Curie.
Same four function names and return types as vision/interface.py.

Usage:
    from vision import real
    real.init("192.168.0.4")
    ball = real.get_ball()

Must call init() once before any of the interface functions. init() does the
actual NAOqi import, so the module can be parsed on the laptop without naoqi
installed -- only call sites fail.
"""

import numpy as np

from vision.constants import (
    CAMERA_INTRINSICS_BOTTOM_640X480,
    CAMERA_INTRINSICS_TOP_640X480,
    BALL_RADIUS_M,
    BLACK_HSV_LOWER,
    BLACK_HSV_UPPER,
    MIN_CONTOUR_AREA_PX,
)
from vision.detect import detect_ball_pixel, detect_largest_blob
from vision.interface import Ball, Goal
from vision.projection import pixel_to_robot_frame


# --- NAOqi constants (avoid magic numbers in calls) ---
_CAMERA_INDEX_TOP = 0
_CAMERA_INDEX_BOTTOM = 1
_RESOLUTION_VGA = 2          # 640 x 480
_COLOR_SPACE_BGR = 13        # ALVideoDevice BGR color space
_FPS = 30
_FRAME_ROBOT = 2             # ALMotion FRAME_ROBOT


# --- Module-level proxies (populated by init) ---
_motion = None
_video = None
_curie_ip = None
_curie_port = None


def init(ip="192.168.0.4", port=9559):
    """Connect to Curie. Must be called once before any interface function.

    Raises ImportError if naoqi isn't installed (laptop without bundle).
    """
    global _motion, _video, _curie_ip, _curie_port
    from naoqi import ALProxy   # imported lazily so this file parses on laptop
    _motion = ALProxy("ALMotion", ip, port)
    _video = ALProxy("ALVideoDevice", ip, port)
    _curie_ip = ip
    _curie_port = port


def _require_init():
    if _motion is None or _video is None:
        raise RuntimeError("vision.real.init() must be called before use")


def _flat_to_4x4(flat_16):
    """Reshape NAOqi getTransform's flat 16-float list into our 4x4 list-of-lists."""
    return [list(flat_16[i*4:(i+1)*4]) for i in range(4)]


def _grab_frame(camera_index):
    """Grab a single BGR frame from the given camera. Returns numpy ndarray (H, W, 3).

    TODO Monday: verify subscriber-name uniqueness and unsubscribe lifecycle --
    NAOqi leaks subscribers if not cleaned up.
    """
    _require_init()
    name = "striker_{}".format(camera_index)
    sub_id = _video.subscribeCamera(name, camera_index, _RESOLUTION_VGA, _COLOR_SPACE_BGR, _FPS)
    try:
        image = _video.getImageRemote(sub_id)
        if image is None:
            return None
        width, height = image[0], image[1]
        raw = image[6]
        frame = np.frombuffer(raw, dtype=np.uint8).reshape((height, width, 3))
        return frame
    finally:
        _video.unsubscribe(sub_id)


# ------------------------------------------------------------
# Interface functions (match vision/interface.py signatures)
# ------------------------------------------------------------

def get_ball():
    """Return a Ball detection from the bottom camera, or None."""
    _require_init()
    frame = _grab_frame(_CAMERA_INDEX_BOTTOM)
    if frame is None:
        return None

    pixel = detect_ball_pixel(frame)
    if pixel is None:
        return None

    # TODO Monday: replace constants with _video.getCameraIntrinsicMatrix(...) if available.
    intrinsics = CAMERA_INTRINSICS_BOTTOM_640X480

    flat = _motion.getTransform("CameraBottom", _FRAME_ROBOT, True)
    T = _flat_to_4x4(flat)

    robot_frame = pixel_to_robot_frame(pixel, intrinsics, T, ball_radius=BALL_RADIUS_M)

    # TODO: compute angular bearing and a real confidence score
    return Ball(
        pixel=pixel,
        angular=(0.0, 0.0),
        distance=(robot_frame[0]**2 + robot_frame[1]**2) ** 0.5 if robot_frame else None,
        robot_frame=robot_frame,
        confidence=1.0,
    )


def get_goal():
    """Return a Goal detection from the top camera, or None.

    TODO Tuesday: shape-filter the largest dark blobs into post candidates
    (tall narrow rectangles), match left/right pair, compute angular bearings.
    """
    _require_init()
    frame = _grab_frame(_CAMERA_INDEX_TOP)
    if frame is None:
        return None

    # Placeholder: largest dark blob, no shape filter yet
    bbox = detect_largest_blob(frame, BLACK_HSV_LOWER, BLACK_HSV_UPPER, MIN_CONTOUR_AREA_PX)
    if bbox is None:
        return None

    raise NotImplementedError("get_goal: shape filter + post pairing not yet built")


def get_keeper_movement(window_seconds=2.0):
    """Detect keeper motion direction via frame differencing over the window.

    TODO Tuesday: capture N frames from top camera over `window_seconds`,
    diff consecutive pairs, sum motion in left/right halves of the keeper
    bounding box, return whichever dominates (or "none" / None).
    """
    _require_init()
    raise NotImplementedError("get_keeper_movement not yet built")


def get_keeper_position():
    """Return (yaw, pitch) bearing to keeper, or None.

    TODO Tuesday: detect dark blob inside the keeper area from the top camera,
    compute angular bearing from pixel coordinates.
    """
    _require_init()
    raise NotImplementedError("get_keeper_position not yet built")
