"""Entry point for running the striker state machine against the real robot.

Usage on the robot (or from the laptop with Choregraphe Py2.7):
    py27 run_real.py

Mirrors run_mock.py but swaps the mock vision module for the NAOqi-backed
vision and motion proxies.
"""

from __future__ import print_function, division

from striker.context import Context
from striker import state_machine
from striker import motion
from vision import real

CURIE_IP = "192.168.0.4"
CURIE_PORT = 9559

real.init(CURIE_IP, CURIE_PORT)
motion.init(CURIE_IP, CURIE_PORT)

motion.enable_fall_manager(True)
motion.stiffness_on()
motion.stand_up()
motion.head_down_25deg()

ctx = Context(vision=real, motion=motion, tts=None, logger=print)

try:
    state_machine.run(ctx)
finally:
    motion.stop_move()
    motion.stiffness_off()
