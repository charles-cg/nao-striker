
# NAO Striker — Project Plan

**Competition:** NAO Fútbol TEC — Tiro Penal (Penalty Kick) **Role:** Striker
(Tirador) **Robot:** NAO v6 — "Curie" **Competition Date:** June 4th, 2026
**Tech Stack:** Python 2.7 + NAOqi SDK 2.8 + OpenCV

---

## 1. Competition Spec (per official rules — `NAO Futbol TEC.html` §5.3.2)

### Field geometry

| Symbol | Description                  | Value                      |
| ------ | ---------------------------- | -------------------------- |
| A      | Field length                 | 240 cm                     |
| B      | Field width                  | 240 cm                     |
| G      | Penalty mark → goal line     | **130 cm**                 |
| H      | Striker start → penalty mark | **20 cm**                  |
| E × F  | Keeper area (área chica)     | 60 × 220 cm                |
| —      | Goal                         | **150 W × 80 H × 50 D cm** |

So at start of each kick:

- Striker stands **20 cm behind the ball**
- Ball must travel **130 cm** on wood floor to cross the goal line
- Goal corners are at ±75 cm from goal center → corner kick angle ≈ **30°
  off-axis from ball**

### Environment

- **Ball:** plastic, **orange** (naranja), 65 mm diameter, 55 g
- **Goal posts:** **black** (rule change 2026-06-01 — was originally blue per HTML rules; shares HSV signature with field lines, discriminate by shape)
- **Net:** white
- **Floor:** wood (duela de madera) — brown, grainy, reflective
- **Field lines:** black
- **Camera:** 640 × 480 @ 30 fps

### Match rules

- 5 kicks per team, consecutive
- **30 seconds per kick**, 1 minute setup time between kicks
- Sudden-death (Gol de Oro) on tie
- **Valid shot:** any contact between robot and ball (force/precision don't
  matter for validity)
- **Only goals score**
- **Invalid kick** (no score): striker exceeds 30 s
- **Repetition:** either robot starts before whistle OR robots collide. 3
  repetitions = disqualification.

### Keeper rule (critical for strategy)

- Keeper starts on goal line between posts
- Can move freely within área chica (220 × 60 cm) **after** whistle
- Área chica is **wider than the goal** (220 cm vs 150 cm) — static keeper
  covers entire goal width
- **Implication: scoring requires waiting for keeper to commit, then kicking
  opposite.** READ_KEEPER is mandatory, not optional.

---

## 2. MVP Scope

Full 5-state machine is the MVP (not a stretch goal, given keeper coverage):

```
APPROACH → ALIGN → READ_KEEPER → DECIDE → KICK
```

> A simple system that works reliably beats a complex system that fails on
> competition day.

---

## 3. State Machine Architecture

**Pattern:** dict-of-handler-functions (Python analogue of C's enum +
function-pointer table).

```python
HANDLERS = {"APPROACH": approach, "ALIGN": align, ...}
state = "APPROACH"
while state != "DONE":
    state = HANDLERS[state](ctx)
```

**Threading model:** blocking sequential (no `.post`, no threads). Each motion
call blocks until done. The ball is static so the cost is acceptable.

### State definitions

#### 🟡 APPROACH

- **Camera:** bottom (head tilted ~25° down)
- **Goal:** walk forward until ball is within striking distance
- **Success transition:** `ball.robot_frame[0] < 0.15 m` for 3 consecutive
  frames → ALIGN
- **Timeout:** 6 s → force ALIGN
- **Fallback chain (ball lost):** 5 frames wait → head scan ±30° yaw → walk 10
  cm blind → force ALIGN

#### 🟡 ALIGN

- **Camera:** bottom (head tilted ~25° down)
- **Goal:** position ball at ~(0.12 m forward, −0.10 m lateral) from torso —
  i.e. 12 cm ahead, 10 cm to the right (kick foot side)
- **Success transition:** ball is within ±2 cm of target on both axes for 3
  consecutive frames → READ_KEEPER
- **Timeout:** 8 s → force READ_KEEPER (kick wonky but valid)
- **Fallback (ball lost):** tilt head down further (+10° pitch); if still lost,
  force READ_KEEPER

#### 🟡 READ_KEEPER

- **Camera:** top (head level)
- **Robot is static** during this state (required for motion-detection-based
  keeper observation)
- **Goal:** detect keeper movement direction via
  `vision.get_keeper_movement(window_seconds=2.0)`
- **Success transition:** any non-`None` return value → DECIDE
- **Timeout:** 6 s → DECIDE with `"none"` (default corner)

#### 🟡 DECIDE

- **Logic only**, no vision/motion calls:
  ```python
  if keeper_movement == "left":
      kick_direction = "right_corner"
  elif keeper_movement == "right":
      kick_direction = "left_corner"
  else:
      kick_direction = "corner"   # default to furthest corner
  ```
- **Transition:** → KICK (immediate)

#### 🟡 KICK

- Body rotation to aim (≤ ±30° turn), then trigger pre-recorded
  `strong_kick_right` behavior
- **Timeout:** 5 s
- **Transition:** → DONE

### Time budget per kick

| State       | Allocation                |
| ----------- | ------------------------- |
| APPROACH    | ~3 s (only 20 cm to walk) |
| ALIGN       | ~5 s                      |
| READ_KEEPER | ~5 s                      |
| DECIDE      | <0.5 s                    |
| KICK        | ~4 s (rotation + kick)    |
| **Buffer**  | **~12 s**                 |
| **Total**   | **≤ 30 s** ✓              |

The 1-minute setup time between kicks is generous — manual repositioning of
Curie to the start position is comfortable.

---

## 4. Vision Module Interface (`vision/interface.py`)

**Frozen.** Implementations live in `vision/` (shared) and may be edited;
signatures may not change without team agreement.

### Classes

- **`Ball`**: `.pixel (px, py)`, `.angular (yaw, pitch in rad)`,
  `.distance (m)`, `.robot_frame (x_m, y_m)`, `.confidence ∈ [0, 1]`
- **`Goal`**: `.left_post_angular`, `.right_post_angular`, `.center_angular`,
  `.visible_posts ∈ {"both", "left", "right"}`

### Functions

- `get_ball()` → `Ball | None`
- `get_goal()` → `Goal | None` (returns Goal with partial `visible_posts` if
  only one post visible; None only when zero posts visible)
- `get_keeper_movement(window_seconds=2.0)` → `"left" | "right" | "none" | None`
  (from **shooter's POV**)
- `get_keeper_position()` → `(yaw, pitch) | None`

### Convention

- `None` means "no answer" (sensor failure, target absent, insufficient data)
- `"none"` (string) means "I have an answer and it's empty" (e.g., keeper
  observed but did not commit)

### Detection strategy

| Target                   | Method                                                                                                    |
| ------------------------ | --------------------------------------------------------------------------------------------------------- |
| Ball (orange)            | HSV color mask, tuned for orange on wood background                                                       |
| Goal posts (black)       | HSV V-only mask (low brightness) + shape filter (tall narrow rectangles) to discriminate from field lines |
| Keeper                   | Motion detection (frame differencing) within bounding box defined by black posts                          |
| Pixel → meter conversion | `ALMotion.getTransform(camera_frame, FRAME_ROBOT)` + `ALVideoDevice` intrinsics + ground-plane projection |

---

## 5. Camera Strategy

NAO v6 has two cameras — only one streams at a time.

| State       | Camera     | Head pose                                        |
| ----------- | ---------- | ------------------------------------------------ |
| APPROACH    | **bottom** | tilted ~25° down                                 |
| ALIGN       | **bottom** | tilted ~25° down (may tilt further on ball lost) |
| READ_KEEPER | **top**    | level                                            |
| DECIDE      | (n/a)      | —                                                |
| KICK        | (n/a)      | —                                                |

**Camera switching** happens at the 2 state transitions where it changes
(ALIGN→READ_KEEPER and KICK→DONE reset). `ALVideoDevice.subscribe`/`unsubscribe`
costs ~100–500 ms; only switching at transitions makes this negligible.

**Head is fixed within each state** (no live tracking). Reduces math complexity
for pixel→meter conversion. Re-center via head scan only as a ball-lost
fallback.

---

## 6. Kick Mechanism

- **Approach:** pre-recorded Choregraphe Timeline animation on the right leg,
  tuned for ball to travel >1.3 m on wood floor
- **Direction control:** body rotation before kick (single kick animation,
  variable aim angle)
  - Center: 0° rotation
  - Right corner: ~+25° body rotation right
  - Left corner: ~−25° body rotation left
- **Saved as behavior:** `behaviors/strong_kick_right.crg` triggered via
  `ALBehaviorManager.runBehavior()`

**Recording is Monday session priority #1** because:

1. Cannot be validated in simulator (no ball physics)
2. Highest physical risk: if no recordable force reaches 1.3 m, fall back to
   hand-coded angle interpolation (1 day of work)

---

## 7. Execution Timeline (6 days)

### Saturday May 30 (today, partial — robot not available)

- ✅ Vision interface frozen and committed (`vision/interface.py`)
- ✅ Repo skeleton (`vision/`, `striker/`, `goalkeeper/`, `__init__.py`s)
- ✅ Plan doc updated (this document)
- ✅ Toolchain working (Python 2.7 + naoqi on Mac via Choregraphe framework
  symlink)
- ⏳ Teammate sync: ball is orange, READ_KEEPER mandatory, interface frozen —
  please pull and review

### Sunday May 31 (laptop only)

1. `striker/state_machine.py` — dispatch loop + 5 empty handler functions, runs
   against a mock context
2. `striker/context.py` — context object passed between handlers (vision proxy,
   motion proxy, kick variant, etc.)
3. `vision/mock.py` — fake implementation of `vision/interface.py` returning
   scripted values (drop-in replacement for testing)
4. HSV detection script on laptop webcam — orange ball on wood-colored
   background; produces bounding box
5. State machine integration test: full mock-driven run, observe transitions in
   logs

**Do NOT touch NAOqi motion code Sunday.** It can wait until Monday — virtual
robot at lab is equivalent to virtual robot at home.

### Monday June 1 evening (robot session 1)

1. **First 10 min:** verify mock-driven state machine connects to Curie
2. **Next 20 min (highest priority):** record `strong_kick_right` in Choregraphe
   Timeline; iterate force until ball reliably travels >1.3 m on wood
3. **Next 30 min:** tune HSV thresholds for orange ball + black posts (V-only)
   under real lab lighting (collaborate with goalkeeper teammate if present)
4. Remaining time: integrate APPROACH with real `vision.get_ball()`

### Tuesday June 2 evening (robot session 2)

- Integrate ALIGN with real vision
- Test camera switching (bottom ↔ top)
- First full APPROACH → ALIGN → KICK run (skip READ_KEEPER initially)
- Iterate on alignment tolerance and timing
- Test body rotation aiming

### Wednesday June 3 evening (robot session 3 — last before competition)

- Add READ_KEEPER + DECIDE
- Full kick run-throughs, aim for consistency
- Stress test: vary lighting, vary keeper behavior
- **Do not add new features Wednesday.** Only fix bugs.

### Thursday June 4 — competition

- Rest. Don't code. Trust the work.

---

## 8. Risk Register

| Risk                                                                 | Likelihood | Impact   | Mitigation                                                                                              |
| -------------------------------------------------------------------- | ---------- | -------- | ------------------------------------------------------------------------------------------------------- |
| Kick cannot reach 1.3 m on wood with stock force                     | Medium     | Critical | Test Monday first; fall back to hand-coded interpolation Tuesday if needed                              |
| Orange ball + wood floor HSV separation poor                         | High       | High     | Tune Monday under real lighting; use blob shape/size validation alongside color                         |
| READ_KEEPER motion detection unreliable (robot drift while "static") | Medium     | High     | Tighten motion-detection threshold; if hopeless, default to corner every time (still ~25% score chance) |
| Robot falls during walk                                              | Low        | Critical | Enable `ALMotion.setFallManagerEnabled(True)`; on fall detection, transition to DONE (forfeit kick)     |
| Ball alignment within ±2 cm impossible due to walk drift             | Medium     | Medium   | Loosen to ±3 cm if needed; rely on body rotation to compensate for residual alignment error             |
| Network drop to robot mid-session                                    | Medium     | Low      | Always work with a backup local script that runs onboard via SSH                                        |
| Vision interface drift between teammates                             | Low        | High     | Interface FROZEN as of 2026-05-30; signature changes require explicit agreement                         |
| Battery depletes during long lab session                             | Medium     | Medium   | Keep robot on charge between attempts; only stand/walk when actively testing                            |

---

## 9. Key Technical Decisions (changelog)

Decisions locked during planning session 2026-05-29/30:

- **State machine:** Pattern B (dict + handler functions), not big switch
- **Threading:** A (blocking sequential), not threaded
- **Camera:** per-state switching, fixed head per state, NAOqi transforms for
  coordinate math
- **Kick:** C (pre-recorded Choregraphe animation) + Y (body rotation for
  aiming)
- **Vision interface:** classes return rich data (multiple coordinate
  representations) + `None` for missing, `"none"` for measured-but-empty
- **Keeper movement convention:** **shooter's POV** (left = striker's left),
  documented in `vision/interface.py`
- **Goal partial visibility:** if only one post visible, return a `Goal` object
  (not None); `visible_posts` field encodes which

---

## 10. Open Questions

- [ ] What goalkeeper module is teammate building? Does it share kick
      implementation work?
- [ ] Who handles `.gitignore` (teammate said they would — confirm done before
      Monday)
- [ ] Confirm NAO's onboard NAOqi version matches Choregraphe 2.8.8 (check
      Monday first thing)
- [ ] Lab lighting conditions — is there a window? Fluorescent? Mixed?

---

## 11. Handoff to Claude Code (for future sessions)

> "I am building the striker module for a NAO v6 robot named Curie, for the NAO
> Fútbol TEC penalty-kick competition on 2026-06-04. Tech: Python 2.7 + NAOqi
> 2.8 + OpenCV, dev'd on Mac with Choregraphe virtual robot. Architecture is a
> 5-state machine (APPROACH → ALIGN → READ_KEEPER → DECIDE → KICK) implemented
> as dict-of-handler-functions, blocking sequential calls to NAOqi. Vision
> interface frozen at `vision/interface.py`. Kick is a pre-recorded Choregraphe
> behavior aimed via body rotation. See this plan doc for the full spec,
> transition thresholds, and timeline."

---

_Plan revised 2026-05-30 during design grilling session — incorporates official
rules, frozen interface, and locked architectural decisions._
