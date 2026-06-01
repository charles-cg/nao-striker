"""Scripted mock of vision/interface.py for laptop-only state machine testing.

Drop-in replacement: same function names and return types as vision.interface,
but returns hardcoded values so the state machine can run end-to-end without
a camera or a robot.

Tune the returned values to exercise different branches of the state machine.
"""

from __future__ import print_function, division

from vision.interface import Ball, Goal

_get_ball_count = 0
_ball_positions = [
    (0.40, 0.0),    # APPROACH walking
    (0.30, 0.0),
    (0.20, 0.0),
    (0.15, 0.0),
    (0.12, 0.0),    # APPROACH in-range 1/3
    (0.10, 0.0),    # 2/3
    (0.10, 0.0),    # 3/3 -> ALIGN
    (0.10, -0.03),  # ALIGN: ball drifting toward target
    (0.11, -0.06),
    (0.12, -0.08),
    (0.12, -0.10),  # ALIGN in-range 1/3
    (0.12, -0.10),  # 2/3
    (0.12, -0.10),  # 3/3 -> READ_KEEPER
    (0.12, -0.10),  # clamp tail
]


def get_ball():
    """Return a Ball positioned within APPROACH's success threshold."""
    global _get_ball_count
    idx = min(_get_ball_count, len(_ball_positions) - 1)
    x, y = _ball_positions[idx]
    _get_ball_count += 1
    return Ball(
        pixel=(320, 240),
        angular=(0.0, 0.0),
        distance=x,
        robot_frame=(x, y),   # < 0.15 m ahead -> APPROACH succeeds
        confidence=1.0,
    )

def reset():
    global _get_ball_count
    _get_ball_count = 0


def get_goal():
    """Return a Goal with both posts visible, centered ahead."""
    return Goal(
        left_post_angular=(0.20, 0.0),
        right_post_angular=(-0.20, 0.0),
        center_angular=(0.0, 0.0),
        visible_posts="both",
    )


def get_keeper_movement(window_seconds=2.0):
    """Return 'left' so DECIDE picks the right corner."""
    return None


def get_keeper_position():
    """Return a plausible (yaw, pitch) bearing to the keeper."""
    return (0.0, -0.05)
