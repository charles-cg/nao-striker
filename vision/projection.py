# -*- coding: utf-8 -*-
"""Pure-math helpers for projecting image pixels to floor coordinates.

No NAOqi, no numpy. Caller provides camera intrinsics and the camera->robot
transform; this module turns them into (x, y) in robot frame.
"""

from __future__ import print_function, division

def pixel_to_camera_ray(pixel, intrinsics):
    """convert a pixel coordinate to a direction vector in the camera frame.

    pixel: (u, v) pixel coords, origin top-left, u right, v down
    intrinsics: (fx, fy, cx, cy) — focal lengths and principal point in pixels
    Returns (dx, dy, dz) tuple in camera frame: x right, y down, z forward.
    Direction is NOT unit-normalized — magnitude doesn't matter for ray-plane intersection.
    """
    u, v = pixel
    fx, fy, cx, cy = intrinsics
    return (
        (u - cx) / fx, #X
        (v -cy) / fy, #Y
        1.0, #Z
    )

def apply_transform_to_point(point, T):
    """Apply a 4x4 transform to a 3D point.

    point: (x, y, z) tuple
    T: 4x4 matrix as list of 4 rows of 4 floats
    Returns (x, y, z) tuple in the target frame.

    Treats input as a point (homogeneous w=1) — translation IS applied.
    For directions/rays, use apply_transform_to_direction.
    """
    x, y, z = point
    new_x = T[0][0]*x + T[0][1]*y + T[0][2]*z + T[0][3]
    new_y = T[1][0]*x + T[1][1]*y + T[1][2]*z + T[1][3]
    new_z = T[2][0]*x + T[2][1]*y + T[2][2]*z + T[2][3]
    return new_x, new_y, new_z

def apply_transform_to_direction(direction, T):
    """Apply a 4x4 transform to a 3D direction vector.

    direction: (dx, dy, dz) tuple
    T: 4x4 matrix as list of 4 rows of 4 floats
    Returns (dx, dy, dz) tuple in the target frame.

    Treats input as a direction (homogeneous w=0) — translation is NOT applied,
    only rotation. Use this for rays' direction components, not their origins.
    """
    x, y, z = direction
    new_x = T[0][0]*x + T[0][1]*y + T[0][2]*z
    new_y = T[1][0]*x + T[1][1]*y + T[1][2]*z
    new_z = T[2][0]*x + T[2][1]*y + T[2][2]*z
    return new_x, new_y, new_z

def project_to_ground(origin, direction, ground_z=0.0):
    """Find where a ray hits the ground plane z=ground_z.

    origin: (x, y, z) tuple in robot frame
    direction: (dx, dy, dz) tuple in robot frame (need not be unit-normalized)
    ground_z: z-coordinate of the ground plane (default 0.0; use ball_radius
            for the ball's center sitting on the floor)

    Returns (x, y) tuple in robot frame where the ray crosses the plane,
    or None if the ray is parallel to or pointing away from the plane.
    """
    ox, oy, oz = origin
    dx, dy, dz = direction
    if dz == 0.0:
        return None
    s = (ground_z - oz) / dz
    if s < 0:
        return None
    x = ox + s * dx
    y = oy + s * dy
    return (x, y)

def pixel_to_robot_frame(pixel, intrinsics, camera_to_robot_transform, ball_radius=0.0325):
    """Project a pixel detection to the ball's position in robot frame.

    pixel: (u, v) pixel coords of the ball center
    intrinsics: (fx, fy, cx, cy)
    camera_to_robot_transform: 4x4 matrix from NAOqi getTransform(camera, FRAME_ROBOT, True)
    ball_radius: vertical offset of the ball's center above the floor (m). Default
                is 0.0325 m = 65 mm / 2 (the competition ball).

    Returns (x_m, y_m) in robot frame: x forward, y left.
    Returns None if the ray doesn't intersect the ground plane in front of the robot.
    """
    T = camera_to_robot_transform
    ray_cam = pixel_to_camera_ray(pixel, intrinsics)
    origin_robot = apply_transform_to_point((0.0, 0.0, 0.0), T)
    direction_robot = apply_transform_to_direction(ray_cam, T)
    return project_to_ground(origin_robot, direction_robot, ground_z=ball_radius)
