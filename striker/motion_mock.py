"""No-op mock of striker/motion.py for laptop-only state machine testing.

Drop-in replacement: same function names as striker.motion, but logs the call
instead of moving anything. Lets run_mock.py exercise the full handler logic
(including motion calls) without a robot.
"""

from __future__ import print_function, division


def _log(call):
    print("[motion_mock] {}".format(call))


def init(ip="mock", port=0):
    _log("init(ip={}, port={})".format(ip, port))


def stand_up():
    _log("stand_up()")


def stiffness_on():
    _log("stiffness_on()")


def stiffness_off():
    _log("stiffness_off()")


def enable_fall_manager(on=True):
    _log("enable_fall_manager({})".format(on))


def stop_move():
    _log("stop_move()")


def set_head_pose(pitch_rad, yaw_rad=0.0, speed=0.2):
    _log("set_head_pose(pitch={:.2f}, yaw={:.2f})".format(pitch_rad, yaw_rad))


def head_down_25deg():
    _log("head_down_25deg()")


def head_level():
    _log("head_level()")


def walk_step(x_m, y_m, theta_rad):
    _log("walk_step(x={:.3f}, y={:.3f}, theta={:.3f})".format(x_m, y_m, theta_rad))


def rotate(angle_rad):
    _log("rotate({:.3f} rad)".format(angle_rad))


def run_behavior(name):
    _log("run_behavior('{}')".format(name))
