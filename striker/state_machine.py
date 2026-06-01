from __future__ import print_function, division

import time

APPROACH_TIMEOUT_S = 6.0
APPROACH_SUCCESS_DISTANCE_M = 0.15
APPROACH_DEBOUNCE_FRAMES = 3

ALIGN_TIMEOUT_S = 8.0
ALIGN_TARGET_X_M = 0.12
ALIGN_TARGET_Y_M = -0.10
ALIGN_TOLERANCE_M = 0.02
ALIGN_DEBOUNCE_FRAMES = 3

READ_KEEPER_TIMEOUT_S = 6.0
READ_KEEPER_WINDOW_S = 2.0

KICK_TIMEOUT_S = 5.0
KICK_ROTATION_DEGREES = {
    "right_corner": +25.0,
    "left_corner": -25.0,
    "corner": +25.0
}

def approach(ctx):
    ctx.logger("APPROACH entered")
    start = time.time()
    in_range_counter = 0

    while True:
        if time.time() - start > APPROACH_TIMEOUT_S:
            ctx.logger("APPROACH timeout -> ALIGN")
            return "ALIGN"

        ball = ctx.vision.get_ball()

        if ball is None:
            ctx.logger("APPROACH: ball is lost")
            in_range_counter = 0
            time.sleep(0.1)
            continue
        if ball.robot_frame[0] < APPROACH_SUCCESS_DISTANCE_M:
            in_range_counter += 1
            ctx.logger("APPROACH: in range ({}/{}) at {:.2f}m".format(in_range_counter, APPROACH_DEBOUNCE_FRAMES, ball.robot_frame[0]))
            if in_range_counter >= APPROACH_DEBOUNCE_FRAMES:
                ctx.logger("APPROACH success -> ALIGN")
                return "ALIGN"
        else:
            if in_range_counter > 0:
                ctx.logger("APPROACH: lost streak, reset")
            in_range_counter = 0
            ctx.logger("APPROACH: ball at {:.2f}m, walking".format(ball.robot_frame[0]))
            # TODO Monday: ctx.motion.moveTo(0.05, 0.0, 0.0)

        time.sleep(0.1)

def align(ctx):
    ctx.logger("ALIGN entered")
    start = time.time()
    in_range_counter = 0

    while True:
        if time.time() - start > ALIGN_TIMEOUT_S:
            ctx.logger("ALIGN timeout -> READ_KEEPER")
            return "READ_KEEPER"

        ball = ctx.vision.get_ball()

        if ball is None:
            ctx.logger("ALIGN: ball is lost")
            in_range_counter = 0
            time.sleep(0.1)
            continue
        dx = abs(ball.robot_frame[0] - ALIGN_TARGET_X_M)
        dy = abs(ball.robot_frame[1] - ALIGN_TARGET_Y_M)
        if dx < ALIGN_TOLERANCE_M and dy < ALIGN_TOLERANCE_M:
            in_range_counter += 1
            ctx.logger("ALIGN: in range ({}/{}) at {:.2f}m, {:.2f}m".format(in_range_counter, ALIGN_DEBOUNCE_FRAMES, ball.robot_frame[0], ball.robot_frame[1]))
            if in_range_counter >= ALIGN_DEBOUNCE_FRAMES:
                ctx.logger("ALIGN success -> READ_KEEPER")
                return "READ_KEEPER"
        else:
            if in_range_counter > 0:
                ctx.logger("ALIGN: lost streak, reset")
            in_range_counter = 0
            ctx.logger("ALIGN: ball at {:.2f}m, {:.2f}m, walking".format(ball.robot_frame[0], ball.robot_frame[1]))
            # TODO Monday: ctx.motion.moveTo(0.05, 0.0, 0.0)

        time.sleep(0.1)

def read_keeper(ctx):
    ctx.logger("READ_KEEPER entered")
    start = time.time()

    while True:
        if time.time() - start > READ_KEEPER_TIMEOUT_S:
            ctx.logger("READ_KEEPER timeout -> DECIDE (default none)")
            ctx.keeper_movement = "none"
            return "DECIDE"
        movement = ctx.vision.get_keeper_movement(window_seconds=READ_KEEPER_WINDOW_S)
        if movement is not None:
            ctx.keeper_movement = movement
            ctx.logger("READ_KEEPER: keeper moved {} -> DECIDE".format(movement))
            return "DECIDE"
        
        time.sleep(0.1)

def decide(ctx):
    ctx.logger("DECIDE entered")
    if ctx.keeper_movement == "left":
        ctx.kick_direction = "right_corner"
    elif ctx.keeper_movement == "right":
        ctx.kick_direction = "left_corner"
    else:
        ctx.kick_direction = "corner"
    ctx.logger("DECIDE: keeper={} -> kick={}".format(ctx.keeper_movement, ctx.kick_direction))
    return "KICK"

def kick(ctx):
    ctx.logger("KICK entered")
    rotation = KICK_ROTATION_DEGREES.get(ctx.kick_direction, 0.0)
    ctx.logger("KICK: direction={}, rotation={:+.1f}deg".format(ctx.kick_direction, rotation))

    # TODO Monday:
    #   ctx.motion.moveTo(0.0, 0.0, math.radians(rotation))
    #   ctx.motion.behaviorManager.runBehavior("strong_kick_right")
    #   wait with timeout
    
    time.sleep(0.2)
    ctx.logger("KICK done -> DONE")
    return "DONE"

HANDLERS = {
    "APPROACH": approach,
    "ALIGN": align,
    "READ_KEEPER": read_keeper,
    "DECIDE": decide,
    "KICK": kick
}

def run(ctx, start_state="APPROACH"):
    state = start_state
    while state != "DONE":
        handler = HANDLERS[state]
        state = handler(ctx)
    ctx.logger("DONE")
