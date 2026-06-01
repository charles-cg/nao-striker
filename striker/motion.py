"""Motion proxy wrapping NAOqi ALMotion, ALRobotPosture, ALBehaviorManager.

Drop-in for ctx.motion. Must call init() once before any other function.
All motion calls are blocking (matches plan section 3 threading model).

Usage:
    from striker import motion
    motion.init("192.168.0.4")
    motion.stand_up()
    motion.walk_step(0.05, 0.0, 0.0)
"""

from __future__ import print_function, division

import math


# --- Module-level proxies (populated by init) ---
_motion = None
_posture = None
_behavior = None


def init(ip="192.168.0.4", port=9559):
    """Connect to Curie. Lazy-imports naoqi so this file parses on laptop."""
    global _motion, _posture, _behavior
    from naoqi import ALProxy   # lazy import: only fails if init() is called without naoqi
    _motion = ALProxy("ALMotion", ip, port)
    _posture = ALProxy("ALRobotPosture", ip, port)
    _behavior = ALProxy("ALBehaviorManager", ip, port)


def _require_init():
    if _motion is None:
        raise RuntimeError("striker.motion.init() must be called before use")


# ------------------------------------------------------------
# Setup / teardown
# ------------------------------------------------------------

def stand_up():
    """Bring robot to StandInit posture. Blocks until done."""
    _require_init()
    _posture.goToPosture("StandInit", 0.5)


def stiffness_on():
    """Enable motors on the whole body."""
    _require_init()
    _motion.setStiffnesses("Body", 1.0)


def stiffness_off():
    """Release motors. Call at shutdown so Curie doesn't drift while idle."""
    _require_init()
    _motion.setStiffnesses("Body", 0.0)


def enable_fall_manager(on=True):
    """If on, NAOqi will catch falls automatically (safety)."""
    _require_init()
    _motion.setFallManagerEnabled(on)


def stop_move():
    """Emergency stop on any in-progress walk."""
    _require_init()
    _motion.stopMove()


# ------------------------------------------------------------
# Head pose (for camera aiming)
# ------------------------------------------------------------

def set_head_pose(pitch_rad, yaw_rad=0.0, speed=0.2):
    """Move head to (pitch, yaw) in radians.

    Plan section 5: APPROACH/ALIGN want pitch ~+0.44 rad (~25 deg down);
    READ_KEEPER wants pitch 0 (level). Yaw stays 0 unless ball-lost fallback.
    """
    _require_init()
    _motion.setAngles(["HeadPitch", "HeadYaw"], [pitch_rad, yaw_rad], speed)


def head_down_25deg():
    """Convenience: tilt head 25 degrees down (APPROACH / ALIGN)."""
    set_head_pose(math.radians(25.0), 0.0)


def head_level():
    """Convenience: head level (READ_KEEPER)."""
    set_head_pose(0.0, 0.0)


# ------------------------------------------------------------
# Locomotion
# ------------------------------------------------------------

def walk_step(x_m, y_m, theta_rad):
    """Walk a single step: x forward, y left, theta yaw rotation. Blocking.

    Used by APPROACH (x>0 only) and ALIGN (small dx + dy nudges).
    """
    _require_init()
    _motion.moveTo(x_m, y_m, theta_rad)


def rotate(angle_rad):
    """Rotate body in place by angle (positive = left). Blocking."""
    _require_init()
    _motion.moveTo(0.0, 0.0, angle_rad)


# ------------------------------------------------------------
# Behaviors (pre-recorded Choregraphe animations)
# ------------------------------------------------------------

def run_behavior(name):
    """Run a stored behavior to completion. Blocks until done.

    KICK uses this with name='strong_kick_right' (recorded Monday).
    """
    _require_init()
    _behavior.runBehavior(name)
