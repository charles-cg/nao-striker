from __future__ import print_function, division

from striker.context import Context
from striker import state_machine
from striker import motion_mock
from vision import mock

mock.reset()

ctx = Context(vision=mock, motion=motion_mock, tts=None, logger=print)
state_machine.run(ctx)
