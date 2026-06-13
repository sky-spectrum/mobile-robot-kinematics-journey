---
layout: post
title: "Summary — All 5 phases in one table"
date: 2026-06-14
categories: [analysis]
tags: [summary, comparison]
---

A single reference card for the whole journey.

## Capability matrix

| Action | P1 Diff | P2 Mec | P3 Ack | P4 Ack+T | P5 Swerve |
|---|:---:|:---:|:---:|:---:|:---:|
| Forward | ✅ | ✅ | ✅ | ✅ | ✅ |
| Backward | ✅ | ✅ | ✅ | ✅ | ✅ |
| In-place rotation | ✅ | ✅ | ❌ | ❌ | ✅ |
| Curved trajectory | ✅ | ✅ | ✅ | ✅ | ✅ |
| Sideways translation | ❌ | ✅ | ❌ | ❌ | ✅ |
| Diagonal translation | ❌ | ✅ | ❌ | ❌ | ✅ |
| Heading-locked translation | ❌ | ✅ | ❌ | ❌ | ✅ |
| Sideways + rotate combo | ❌ | ✅ | ❌ | ❌ | ✅ |
| Independent 4-wheel speeds | ❌ | ❌ | ❌ | ✅ | ✅ |
| Independent 4-wheel steering | ❌ | ❌ | ❌ | ❌ | ✅ |
| Field-oriented driving | ❌ | ❌ | ❌ | ❌ | ✅ |
| Slip-free precise turning | ❌ | ❌ | △ | ✅ | ✅ |

## Property comparison

| | P1 | P2 | P3 | P4 | P5 |
|---|---|---|---|---|---|
| DOF (input) | 2 | 3 | 2 | 2 | 3 |
| DOF (output) | 2 | 3 | 2 | 2 | 3 |
| Holonomic? | No | **Yes** | No | No | **Yes** |
| Active wheel count | 2 | 4 | 2 | 4 | 4 |
| Active steering joints | 0 | 0 | 1 (or 2) | 2 | **4** |
| Slip during turn | Hidden | High (rollers) | Some | Minimal | Minimal |
| Energy efficiency | High | Low | High | High | Moderate |
| Mechanical complexity | Low | Medium | Medium | High | **Very high** |
| Typical cost (research) | $1k | $5k | $10k | $20k | $30k+ |
| Common in | Education | Indoor logistics | Cars | Performance cars | FRC, advanced research |

## Decision tree — "which kinematic do I need?"

```
Need to move sideways without rotating?
├─ Yes → omnidirectional (P2 or P5)
│         Indoor? Choose P2 (cheaper).
│         Outdoor? Choose P5 (P2 rollers fail on rough surface).
│
└─ No  → nonholonomic OK
          Precision at speed matters?
          ├─ Yes → Ackermann family (P3 or P4)
          │         Need 4WD for traction? Choose P4.
          │         Otherwise P3.
          │
          └─ No  → Differential (P1) — cheapest, simplest, ubiquitous
```

## The single equation per phase (cheat sheet)

| Phase | The defining equation |
|---|---|
| P1 Diff | `ω_b_z = (v_right − v_left) / w` |
| P2 Mecanum | `ω_i = (v_x ± v_y ± (l+w)·ω_z) / r` (X-pattern of signs) |
| P3 Ackermann | `R = l / tan(φ)`, `θ̇ = v·tan(φ)/l` |
| P4 Ack+Traction | `v_R_outer = v · (R + w/2)/R`, `v_R_inner = v · (R − w/2)/R` |
| P5 Swerve | `v_i = √(v_iₓ² + v_iy²)`, `φ_i = arctan2(v_iy, v_iₓ)` |

Memorize one per phase. Recover the rest.

## What I'd do differently next time

1. **Start with measurement.** Phase 1 worked but I should have used TF to read the
   wheel track before doing any experiments. It builds the "measure first" habit early.

2. **Use the same world across phases.** I bounced between `turtlebot3_world`, `empty_world`,
   `neo_track1`, `neo_workshop`. Sticking to one (probably `empty_world`-like clear space)
   would have made odom trails directly comparable.

3. **Record bag files.** rosbag2 of each automated drive run, organized by phase. Would
   have made post-hoc analysis trivial.

4. **Write the kinematics calculator first, drive second.** Especially for Phase 4 and 5,
   knowing what the wheels *should* do clarifies what to look for in the simulation.

5. **Stick to one robot vendor when possible.** Neobotix's consistent simulation interface
   for P2, P3, P4, P5 saved a huge amount of setup time. The first phase (Turtlebot3) was
   "free" because I'd already installed it from previous learning — but in retrospect I
   could have used MP-400 and stayed in the Neobotix ecosystem the whole way.

## A note on order of phases

I chose the order: Diff → Mecanum → Ackermann → Ack+Traction → Swerve.

An alternative would be: Diff → Ackermann → Mecanum → Swerve. This emphasizes "constraint
release" (Diff is constrained, Ackermann is constrained differently, Mecanum releases all
constraints, Swerve adds precision).

Mine was chosen because Mecanum is *visually* the most striking second step — you watch
the robot move sideways and your brain registers "wait, that's not normal". That early
emotional payoff matters when self-studying for a month.

## Final reflection

What started as "I want to understand why Turtlebot3 is called differential drive" became
a month-long arc that ended with me typing inverse kinematics for swerve modules from
memory. The mental model I now have:

- **Every wheeled robot is a small set of kinematic equations + the cost it pays to honor
  those equations.**
- The choice between kinematic types is a choice about which costs you'll pay (efficiency,
  precision, mechanical complexity, capability gaps).
- There's no universally best kinematic — but for any specific application there is one
  natural choice.

If anyone in 2026 is starting their own ROS2 + kinematics journey, my single advice:
**don't read your way to understanding. Drive your way to understanding.** Five robots,
five months at most, and you'll have a foundation that no amount of textbook reading
would have built.

---

← [Debugging notes]({% post_url 2026-06-14-06-debugging-wsl-gazebo %})
| [Overview]({% post_url 2026-06-14-00-overview %})
