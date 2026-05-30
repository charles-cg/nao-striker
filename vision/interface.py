"""This file serves the function of interfacing with the vision module.

Signatures are FROZEN.
Implementations live in the striker and goalkeeper directories.

Convention:
    None means there is no answer.
    "none" (as a string) means there is an answer and it is empty.
"""

from __future__ import print_function, division


class Ball(object):
    """Detected ball - pure data container, populated by get_ball()."""
    def __init__(self, pixel, angular, distance, robot_frame, confidence):
        self.pixel = pixel              # tuple (px, py)
        self.angular = angular          # tuple (yaw_rad, pitch_rad)
        self.distance = distance        # float in m
        self.robot_frame = robot_frame  # tuple (x_m, y_m) from FRAME_ROBOT origin
                                        # x positive ahead, y positive to robot's left
        self.confidence = confidence    # float score for the particular detection


class Goal(object):
    """Detected goal - pure data container, populated by get_goal()."""
    def __init__(self, left_post_angular, right_post_angular, center_angular, visible_posts):
        self.left_post_angular = left_post_angular
        self.right_post_angular = right_post_angular
        self.center_angular = center_angular
        self.visible_posts = visible_posts


def get_ball():
    """Return Ball when a red ball is detected, None when no ball is visible."""
    raise NotImplementedError("vision.get_ball not yet implemented")


def get_goal():
    """Return Goal when goal posts are detected, None when none of the goal posts are visible.

    If only one post is visible, returns a Goal with visible_posts="left" or "right".
    Only returns None when zero posts are visible.
    """
    raise NotImplementedError("vision.get_goal not yet implemented")


def get_keeper_movement(window_seconds=2.0):
    """Detect goalkeeper movement direction over a recent time window.

    Returns:
        "left"  - keeper moved to the shooter's left
        "right" - keeper moved to the shooter's right
        "none"  - keeper did not commit
        None    - insufficient observation or keeper not visible
    """
    raise NotImplementedError("vision.get_keeper_movement not yet implemented")


def get_keeper_position():
    """Return (yaw, pitch) bearing to keeper, or None if not detected."""
    raise NotImplementedError("vision.get_keeper_position not yet implemented")
