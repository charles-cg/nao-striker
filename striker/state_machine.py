from __future__ import print_function, division

def approach(ctx):
    ctx.logger("APPROACH entered")
    return "ALIGN"

def align(ctx):
    ctx.logger("ALIGN entered")
    return "READ_KEEPER"

def read_keeper(ctx):
    ctx.logger("READ_KEEPER entered")
    ctx.keeper_movement = ctx.vision.get_keeper_movement()
    return "DECIDE"

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
