---
layout: post
title: "Analysis — Kinematics vs Dynamics, and what this journey did NOT cover"
date: 2026-06-14
categories: [analysis]
tags: [kinematics, dynamics, theory]
---

This whole journey was about **kinematics**. That's a specific word with a specific meaning,
and it's important to know what we did NOT do.

## The textbook distinction

| | Kinematics | Dynamics |
|---|---|---|
| Asks | "How does it move?" | "Why does it move?" |
| Inputs | Velocities, angles | Forces, torques, masses |
| Equations | Geometry | Newton's laws (F=ma, τ=Iα) |
| Time horizon | Instantaneous | Time-evolving |
| Solved by | Algebra, trig | ODEs, integration |
| Example | "Given wheel speeds, robot moves at v_x" | "Given wheel torques, mass m, find acceleration" |

This blog stayed strictly on the left column.

## What we did

For each phase we wrote equations like:

```
v_b_x = (v_right + v_left) / 2          ← Phase 1 forward kinematics
v_i = √(v_i_x² + v_i_y²)                ← Phase 5 module speed
φ = arctan(l / R)                       ← Phase 3 steering
```

These are **geometric relationships**. They tell you what the robot will do **right now,
this instant**, given a velocity command. No mention of:

- Mass
- Inertia
- Friction
- Motor torque
- Acceleration limits
- Stopping distance
- Slip dynamics
- Tire deformation
- Center-of-mass shift during turns

## What kinematics cannot answer

Try this question: **"How long does it take MPO-700 to accelerate from 0 to 0.5 m/s?"**

Kinematics: silent. We need:

- Robot mass `m`
- Maximum motor torque `τ_max`
- Wheel radius `r` (for force = torque/r)
- Rolling friction
- Air drag (negligible at 0.5 m/s)

Then `a = F_net / m`, and time to reach v = v/a.

Another question: **"What's the maximum lateral acceleration before MPO-500 slips
sideways during a tight turn?"**

Kinematics: silent. We need:

- Coefficient of friction `μ` between roller and floor
- Normal force on each wheel (from weight distribution)
- Then `F_lateral_max = μ · N`

Yet another: **"Will MPO-700 tip over if I command angular velocity 3 rad/s while moving
0.5 m/s forward?"**

Kinematics: silent. Tip-over is a dynamics question involving:

- Center-of-mass height
- Track width (we measured this!)
- Lateral acceleration during the turn

So kinematics is a **subset** of what you need for real robot operation. It's necessary
but not sufficient.

## Why we still spent a month on just kinematics

Three reasons:

1. **Foundation.** Dynamics builds on top of kinematics. You can't reason about forces and
   accelerations without first knowing what motion the system can produce.

2. **Simulation hides dynamics complexity.** Gazebo's physics engine quietly solves
   dynamics for you, applies friction models, handles slip. Our cmd_vel-based experiments
   were always in the "low-velocity, low-acceleration" regime where kinematics dominates
   and dynamics is negligible. (Phase 4 robot tip-overs happened, and they were
   dynamics-induced — but we didn't model that, we just used `--reset_world`.)

3. **Kinematics is portable across platforms.** The differential kinematics for Turtlebot3
   is the same as for a Roomba and the same as for a 5-ton industrial AGV. Dynamics
   depends on the specific platform.

## What comes after this journey, dynamics-wise

If you want to go deeper, the natural next topics:

### Lateral dynamics (single-track model)

Used in autonomous vehicle path tracking. Adds tire slip angle, cornering stiffness,
yaw moment of inertia. The "Bicycle Model" you'll see in self-driving courses is *not*
the kinematic Bicycle Model from our Phase 3 — it's a **dynamic** Bicycle Model with
tire forces:

```
β = arctan((l_r · tan(δ)) / (l_f + l_r))    ← slip angle
F_y_f = -C_f · α_f                            ← lateral tire force
m·v·(β̇ + ψ̇) = F_y_f + F_y_r                  ← lateral acceleration
```

### Wheel slip and traction control

For high-acceleration regimes (rocket-fast EVs, FRC speed runs), wheels can slip
longitudinally. The kinematic relationship `v = r·ω` becomes `v ≠ r·ω` and you need to
estimate and control slip ratio.

### Mass distribution and stability

For Phase 5 swerve robots that can accelerate aggressively in any direction, the
center-of-mass moves dynamically (or pressure on each wheel changes), and you must
limit acceleration to prevent tip-over. This requires **dynamic** modeling.

### Motor dynamics

Real motors don't instantly reach commanded torque. There's electrical (RL) and
mechanical (J) lag. PID tuning operates in this dynamic regime.

### Full multi-body dynamics

For high-fidelity simulation (or for analyzing manipulators with mobile bases), the
chassis and each wheel are linked rigid bodies. The full equations involve mass matrices,
Coriolis terms, and gravity. Tools like Pinocchio or RBDL solve these.

## A practical mental model

For working roboticists, a useful split is:

| Velocity range | What dominates | What you need |
|---|---|---|
| < 0.5 m/s | Kinematics | This blog ✓ |
| 0.5 - 2 m/s | Kinematics + simple friction | + brake models |
| 2 - 10 m/s | Tire dynamics emerging | + Pacejka tire model |
| > 10 m/s | Full vehicle dynamics | + suspension, aero |

Indoor mobile robots almost always live in the top row. Cars live across all four. Race
cars in the bottom. This blog is sufficient for the top row — start there.

## What our Python code "hides"

In Phase 4 we computed:

```python
v_RL = v_x * (R - self.w_r/2) / R
v_RR = v_x * (R + self.w_r/2) / R
```

A real 4WD vehicle controller doesn't just *command* these speeds — it has to *achieve*
them through closed-loop motor control. Each motor:

1. Receives a target speed
2. Reads its encoder
3. Computes error
4. Applies PID + feedforward
5. Outputs PWM to the motor driver

That PID layer is **dynamic**, not kinematic. It cares about acceleration limits, motor
current, encoder noise.

So even when our kinematics is correct, real deployment needs another layer. That layer
deserves its own learning path.

## Conclusion

Kinematics tells you **what's possible** for a given robot. Dynamics tells you **what's
required** to make it actually do that. Both are needed; we've completed the first.

If after this journey you find yourself thinking in capability matrices ("Can this robot
do sideways motion? Can it rotate in place?"), the kinematics has done its job. The next
journey starts when you ask: "Can it do this *fast enough*? Can it do this *with this
payload*? Can it do this *on this surface*?"

Those are dynamics questions. And there's a whole month's worth of journey there too.
