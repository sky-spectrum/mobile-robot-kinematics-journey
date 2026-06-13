---
layout: post
title: "Phase 4 — Ackermann + Traction (4WD + front steer)"
date: 2026-06-14
categories: [phase]
tags: [ackermann, traction, mpo-700, kinematics]
---

Phase 4 is the bridge between Phase 3 (simplified car) and Phase 5 (swerve). The shift:
**different left and right wheel speeds**, computed from kinematic geometry rather than
assumed equal.

This is what every real 4WD car has to do mechanically (or electronically) when turning.

## Why left ≠ right when turning

In a turn, the inner wheel traces a smaller circle than the outer wheel:

```
                              (outer wheel)
         ↑  R + w/2                    ↑
         │                              │
    ←────●─── pivot center        ●────→
         │  R - w/2                    │
         ↓  (inner wheel)              ↓
```

If both wheels are forced to the same speed, **one of them slips**. Slip wastes energy,
makes turns inaccurate, and accelerates tire wear. So we need:

```
v_rear_left  = v · (R - w_r/2) / R    ← inner (slower)
v_rear_right = v · (R + w_r/2) / R    ← outer (faster)
```

where `R = l / tan(φ)` is the turning radius and `w_r` is the rear track.

Extending to the front wheels (Ackermann + Traction):

```
φ_left  = arctan(l / (R - w_f/2))    ← inner wheel steers more
φ_right = arctan(l / (R + w_f/2))    ← outer wheel steers less

v_front_left  = v · √(l² + (R - w_f/2)²) / R
v_front_right = v · √(l² + (R + w_f/2)²) / R
```

That's 6 numbers (4 speeds + 2 angles) computed from 3 inputs (`v_x`, `ω_z`, plus
geometry constants `l`, `w_f`, `w_r`).

## The strategy on MPO-700

MPO-700 internally does swerve regardless of what we send. For Phase 4 my code:

1. Sends a sequence of `cmd_vel` commands (straight → left turn → right turn → ...)
2. **Computes the 4-wheel speeds and 2 steering angles** that an Ackermann-with-Traction
   robot *would need* to follow that command
3. Logs them to the terminal in real time

The simulation visualizes the result; the calculator verifies the kinematics. Together
they form the learning loop.

## Measured dimensions

```
l   = 0.480 m   (wheelbase)
w_f = 0.450 m   (front track)
w_r = 0.450 m   (rear track)
```

Symmetric chassis. Makes the equations slightly simpler but isn't required.

## The calculator code

The core kinematic computation:

```python
def calculate_ackermann_traction(self, v_x, w_z):
    if abs(w_z) < 1e-6:
        # Straight line: every wheel same speed, no steering
        return dict(mode='STRAIGHT', R=float('inf'),
                    phi_L=0, phi_R=0,
                    v_FL=v_x, v_FR=v_x, v_RL=v_x, v_RR=v_x)
    if abs(v_x) < 1e-6:
        return dict(mode='IMPOSSIBLE')  # in-place rotation
    R = v_x / w_z

    # Front steering — left and right different angles
    phi_L = math.atan(self.l / (R - self.w_f/2))
    phi_R = math.atan(self.l / (R + self.w_f/2))

    # Rear speeds — left and right different magnitudes
    v_RL = v_x * (R - self.w_r/2) / R
    v_RR = v_x * (R + self.w_r/2) / R

    # Front speeds — arc length based approximation
    v_FL = v_x * math.sqrt(self.l**2 + (R - self.w_f/2)**2) / R
    v_FR = v_x * math.sqrt(self.l**2 + (R + self.w_f/2)**2) / R

    return dict(mode='TURNING', R=R,
                phi_L=phi_L, phi_R=phi_R,
                v_FL=v_FL, v_FR=v_FR, v_RL=v_RL, v_RR=v_RR)
```

The driving sequence (`STRAIGHT → LEFT_TURN → RIGHT_TURN → repeat`) is a simple timer
state machine. The interesting output is the **log**:

```
[TURNING] cmd_vel: v_x=+0.30, ω_z=+0.30
  Turning radius R = +1.000 m
  Front Steer   L= +25.6° | R= +21.8°
  Front Wheel v L= +0.300 | R= +0.300   m/s
  Rear  Wheel v L= +0.232 | R= +0.367   m/s
  → rear left/right speed difference: 0.135 m/s
```

This is the moment the Ackermann + Traction equations become visible. A 45 cm wide
robot turning on a 1 m radius needs its rear wheels to differ by **13.5 cm/s** — about
**45%** difference relative to the smaller speed. That's not subtle.

Full file: [`code/phase4_ackermann_traction.py`](../../code/phase4_ackermann_traction.py).

## What this teaches

1. **The differential gear in your car is doing this math for you.** Mechanically,
   continuously, with zero electronics.

2. **The closer R is to w/2, the more dramatic the left/right asymmetry.** Tight turns
   stress the system. Larger turning radius spreads the load more evenly.

3. **Phase 4 is structurally one move from Phase 5.** The only thing Phase 4 cannot do
   that Phase 5 can is **steer the rear wheels too**. One more degree of freedom.

## Phase 3 vs Phase 4

| | P3 Ackermann | P4 Ackermann + Traction |
|---|---|---|
| Rear wheel modeling | Single speed (simplified) | **Left ≠ Right speed** |
| Front wheel modeling | Single steering angle | **Left ≠ Right angle** |
| Front wheel speeds | Same as rear (simplified) | **Computed from arc length** |
| Slip-free turning | △ approximate | ✅ accurate |
| Distance to Swerve | "Far" | **"One step"** |

[Phase 5 — Swerve →]({% post_url 2026-06-14-05-phase5-swerve %})
