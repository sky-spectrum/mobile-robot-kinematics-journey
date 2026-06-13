---
layout: post
title: "Phase 2 — Mecanum / Omnidirectional (MPO-500)"
date: 2026-06-14
categories: [phase]
tags: [mecanum, omnidirectional, neobotix]
---

The first time `linear.y` is not silently discarded. Mecanum wheels break the nonholonomic
constraint by having diagonal rollers on each wheel.

## The trick — diagonal rollers

A mecanum wheel's surface is not a smooth tire. It has small **passive rollers** mounted at
45° around the wheel's circumference. When the wheel rotates, the contact point moves
forward (like normal) — but the roller also imposes a sideways force component.

With four wheels arranged in a rectangle, and rollers oriented in an X-pattern:

```
   FL: rollers point ↘     FR: rollers point ↙
   BL: rollers point ↗     BR: rollers point ↖
```

You can combine the four roller directions to produce any direction in the plane,
plus rotation. **Three degrees of freedom from four wheels.**

## The equations

For each wheel `i` at body-frame position `(l_x, l_y)`, with `l = wheelbase/2`,
`w = track/2`, wheel radius `r`:

```
ω_fl = (v_x - v_y - (l+w)·ω_z) / r
ω_fr = (v_x + v_y + (l+w)·ω_z) / r
ω_rl = (v_x + v_y - (l+w)·ω_z) / r
ω_rr = (v_x - v_y + (l+w)·ω_z) / r
```

The signs of `v_y` and `ω_z` differ across wheels — exactly the asymmetry that the
roller geometry exploits.

## Environment

- **Robot**: Neobotix MPO-500 (mecanum, 4-wheel sized omni base)
- **Source**: [`neobotix/neo_simulation2`](https://github.com/neobotix/neo_simulation2), branch `humble`
- **Launch**:
  ```bash
  ros2 launch neo_simulation2 simulation.launch.py my_robot:=mpo_500 world:=neo_track1
  ```

> The Neobotix `humble` branch uses Gazebo Classic 11, which is exactly what we have. The
> `simulation_classic` documentation page describes the launch interface.

### Neobotix simulation note

Neobotix's mecanum model uses a **planar_move-style plugin**: the chassis itself is driven
in 3 DOF directly by the controller, while the wheels are visual only. As a result:

- `cmd_vel.linear.y` produces real sideways motion ✅
- `/joint_states` does NOT publish wheel rotation (no wheel TF in RViz) ⚠️

I treated this as a feature, not a bug: the *external* kinematic behavior is what
matters here. Phase 4 will be the first phase where individual wheel kinematics matter.

## The five experiments

Run an `odom` monitor in one terminal, send commands in another:

```bash
ros2 topic echo /odom --field twist.twist
```

### 1. Pure forward (Phase 1 baseline)

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.3}, angular: {z: 0.0}}"
```

`linear.x ≈ 0.3` in odom. Same as Phase 1.

### 2. Pure rotation

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0}, angular: {z: 0.5}}"
```

`angular.z ≈ 0.5`. Same as Phase 1.

### 3. ★ Pure sideways (this is Phase 2's moment)

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0, y: 0.3}, angular: {z: 0.0}}"
```

`linear.y ≈ 0.3`. **The robot crabs sideways while keeping its heading constant.**
Phase 1 was incapable of this.

### 4. Diagonal motion (also new)

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.3, y: 0.3}, angular: {z: 0.0}}"
```

Robot moves at 45° without rotating.

### 5. All three axes together

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.2, y: 0.2}, angular: {z: 0.3}}"
```

Forward + sideways + rotating simultaneously. The most complex omnidirectional motion.

## Automation — the rotationless square

Phase 1's square required 4 rotations. Phase 2's square requires 0:

```python
class OmniSquare(Node):
    def __init__(self):
        super().__init__('omni_square')
        self.pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.state = 'FORWARD'
        self.state_start = self.get_clock().now()
        self.side_count = 0
        self.speed = 0.2
        self.side_duration = 3.0

    def timer_callback(self):
        elapsed = (self.get_clock().now() - self.state_start).nanoseconds / 1e9
        msg = Twist()
        # Note: msg.angular.z is NEVER set — heading must be preserved.
        if self.state == 'FORWARD':
            msg.linear.x = self.speed
        elif self.state == 'LEFT':
            msg.linear.y = self.speed
        elif self.state == 'BACKWARD':
            msg.linear.x = -self.speed
        elif self.state == 'RIGHT':
            msg.linear.y = -self.speed
        self.pub.publish(msg)

        if elapsed >= self.side_duration:
            self.side_count += 1
            transitions = {'FORWARD':'LEFT','LEFT':'BACKWARD',
                          'BACKWARD':'RIGHT','RIGHT':'FORWARD'}
            self.state = transitions[self.state] if self.side_count<4 else 'DONE'
            self.state_start = self.get_clock().now()
```

Full file: [`code/phase2_omni_square.py`](../../code/phase2_omni_square.py).

**The robot returns to its starting orientation** because no rotation was ever commanded.
In Phase 1, this is structurally impossible.

## Phase 1 vs Phase 2

| Action | P1 Diff | P2 Mec |
|---|:---:|:---:|
| Sideways motion | ❌ | ✅ |
| Diagonal motion | ❌ | ✅ |
| Constant-heading translation | ❌ | ✅ |
| Sideways + rotate simultaneously | ❌ | ✅ |
| Parallel parking in one motion | ❌ | ✅ |

## Mecanum's price

The capability isn't free:

1. **Roller friction** — diagonal sliding on each roller wastes energy. About 70-80%
   efficiency vs differential's 90+.
2. **Rough terrain hostility** — small rollers get caught on debris, grass, anything
   uneven. Pure indoor robot.
3. **Mechanical complexity** — each wheel is a full assembly. Expensive to manufacture
   and maintain.
4. **Precision** — slip in roller contact makes rotation slightly inaccurate.

These costs are exactly what Phase 3 will trade efficiency back for.

## What Phase 2 still cannot do

| Action | Possible? | Why |
|---|---|---|
| Precise rotation under load | △ | Roller slip |
| Efficient long-distance travel | ❌ | Friction loss |
| Independent 4-wheel speed control | ❌ | Chassis-driven plugin |
| Sloped / rough terrain | ❌ | Roller geometry |

**Phase 3 reintroduces nonholonomic constraint to gain precision.** ↓

[Phase 3 — Ackermann →]({% post_url 2026-06-14-03-phase3-ackermann %})
