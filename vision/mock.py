"""Scripted mock of vision/interface.py for laptop-only state machine testing.

Drop-in replacement: same function names and return types as vision.interface,
but returns hardcoded values so the state machine can run end-to-end without
a camera or a robot.

Tune the returned values to exercise different branches of the state machine.
"""

from __future__ import print_function, division

from vision.interface import Ball, Goal


def get_ball():
    """Return a Ball positioned within APPROACH's success threshold."""
    return Ball(
        pixel=(320, 240),
        angular=(0.0, 0.0),
        distance=0.10,
        robot_frame=(0.10, 0.0),   # < 0.15 m ahead -> APPROACH succeeds
        confidence=1.0,
    )


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
    return "none"


def get_keeper_position():
    """Return a plausible (yaw, pitch) bearing to the keeper."""
    return (0.0, -0.05)
