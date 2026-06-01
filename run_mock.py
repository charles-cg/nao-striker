from __future__ import print_function, division

from striker.context import Context
from striker import state_machine
from vision import mock

mock.reset()

ctx = Context(vision=mock, motion=None, tts=None, logger=print)
state_machine.run(ctx)
