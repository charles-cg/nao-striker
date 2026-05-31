class Context(object):
    def __init__(self, vision, motion, tts, logger):
        self.vision = vision
        self.motion = motion
        self.tts = tts
        self.logger = logger
        self.keeper_movement = None
        self.kick_direction = None
