"""Sanity tests for vision/projection.py. Run with `py27 vision/test_projection.py`."""

from __future__ import print_function, division

from projection import (
    pixel_to_camera_ray,
    apply_transform_to_point,
    apply_transform_to_direction,
    project_to_ground,
    pixel_to_robot_frame,
)


IDENTITY = [
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 0.0, 0.0],
    [0.0, 0.0, 1.0, 0.0],
    [0.0, 0.0, 0.0, 1.0],
]


def approx_equal(a, b, eps=1e-6):
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, (int, float)):
        return abs(a - b) < eps
    return all(abs(x - y) < eps for x, y in zip(a, b))


# ---- pixel_to_camera_ray ----

intr = (500.0, 500.0, 320.0, 240.0)
assert approx_equal(pixel_to_camera_ray((320, 240), intr), (0.0, 0.0, 1.0)), "center pixel"
assert approx_equal(pixel_to_camera_ray((820, 240), intr), (1.0, 0.0, 1.0)), "1 focal length right"
assert approx_equal(pixel_to_camera_ray((320, 740), intr), (0.0, 1.0, 1.0)), "1 focal length down"

# ---- apply_transform_to_point ----

assert approx_equal(apply_transform_to_point((1, 2, 3), IDENTITY), (1, 2, 3)), "identity point"

translate_T = [
    [1.0, 0.0, 0.0, 10.0],
    [0.0, 1.0, 0.0, 20.0],
    [0.0, 0.0, 1.0, 30.0],
    [0.0, 0.0, 0.0,  1.0],
]
assert approx_equal(apply_transform_to_point((1, 2, 3), translate_T), (11, 22, 33)), "pure translation point"

# ---- apply_transform_to_direction ----

assert approx_equal(apply_transform_to_direction((1, 2, 3), IDENTITY), (1, 2, 3)), "identity direction"
assert approx_equal(apply_transform_to_direction((1, 2, 3), translate_T), (1, 2, 3)), "translation ignored for direction"

# ---- project_to_ground ----

assert approx_equal(project_to_ground((0, 0, 1), (0, 0, -1), 0.0), (0, 0)), "straight down hits origin"
assert approx_equal(project_to_ground((0, 0, 1), (1, 0, -1), 0.0), (1, 0)), "diagonal forward+down"
assert project_to_ground((0, 0, 1), (0, 0, 1), 0.0) is None, "pointing up -> None"
assert project_to_ground((0, 0, 1), (1, 0, 0), 0.0) is None, "parallel -> None"

# ---- pixel_to_robot_frame ----

# Camera mounted 50 cm above robot origin, pointing straight down.
# Camera axes: x = robot forward, y = robot right, z = robot down.
# So R has column 3 = (0, 0, -1), column 1 = (1, 0, 0), column 2 = (0, -1, 0).
CAMERA_LOOKING_DOWN_50CM = [
    [1.0,  0.0,  0.0, 0.0],
    [0.0, -1.0,  0.0, 0.0],
    [0.0,  0.0, -1.0, 0.5],
    [0.0,  0.0,  0.0, 1.0],
]

# Center pixel: ray goes straight down, hits floor directly below camera = robot origin.
assert approx_equal(
    pixel_to_robot_frame((320, 240), intr, CAMERA_LOOKING_DOWN_50CM, ball_radius=0.0),
    (0.0, 0.0),
), "down-looking camera, center pixel -> robot origin"

# Pixel 100 px right of center, fx=500. In camera frame the ray is (0.2, 0, 1).
# After rotation, direction in robot frame is (0.2, 0, -1).
# Camera origin at (0, 0, 0.5). Ground plane at z=0.
# s = (0 - 0.5) / -1 = 0.5. Hit point: (0 + 0.5*0.2, 0 + 0.5*0, 0) = (0.1, 0).
assert approx_equal(
    pixel_to_robot_frame((420, 240), intr, CAMERA_LOOKING_DOWN_50CM, ball_radius=0.0),
    (0.1, 0.0),
), "down-looking camera, pixel right of center -> 10cm ahead"

print("all tests passed")
