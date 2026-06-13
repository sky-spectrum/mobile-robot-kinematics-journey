---
layout: post
title: "Phase 1 — Differential Drive (Turtlebot3)"
date: 2026-06-14
categories: [phase]
tags: [differential, turtlebot3, kinematics]
---

The simplest kinematic. Two wheels, each with independent speed. The robot's motion is
determined entirely by the speed difference.

## The kinematics

```
Forward kinematics  (wheel speeds → robot motion):
  v_b_x  = (v_right + v_left) / 2          ← forward speed
  ω_b_z  = (v_right - v_left) / w          ← rotation speed (w = wheel track)

Inverse kinematics  (desired motion → wheel speeds):
  v_left  = v_b_x - ω_b_z · w / 2
  v_right = v_b_x + ω_b_z · w / 2

Nonholonomic constraint:
  v_b_y  = 0                               ← cannot move sideways
```

The third line is the heart of Phase 1. **No matter how you spin the two wheels,
sideways motion is physically impossible.** This is the constraint that the rest of
the journey relentlessly attacks.

## Environment

- **Robot**: Turtlebot3 Waffle Pi (since we already had it installed)
- **Simulation**: Gazebo Classic 11, `turtlebot3_world.launch.py`
- **Visualization**: RViz2 with `RobotModel`, `LaserScan`, `Odometry`

Wheel track measured via TF: `w ≈ 0.288 m` (28.8 cm).

```bash
ros2 run tf2_ros tf2_echo base_link wheel_left_link
# Translation: [0.000, 0.144, 0.023]   → y = +0.144 m

ros2 run tf2_ros tf2_echo base_link wheel_right_link
# Translation: [0.000, -0.144, 0.023]  → y = −0.144 m

# w = 0.144 + 0.144 = 0.288 m
```

## The four canonical experiments

In one terminal, monitor wheel velocities:

```bash
ros2 topic echo /joint_states --field velocity
```

In another terminal, send commands one at a time:

### Experiment 1 — Pure forward

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.2}, angular: {z: 0.0}}"
```

Both wheels show **the same sign, the same magnitude**. Robot moves in a straight line.

### Experiment 2 — Pure rotation

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0}, angular: {z: 0.5}}"
```

Wheels show **opposite signs, same magnitude**. Robot rotates in place.

### Experiment 3 — Curve

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.2}, angular: {z: 0.5}}"
```

Wheels show **same sign, different magnitudes**. Robot traces a curve.

### Experiment 4 — Sideways (the impossible one)

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0, y: 0.5}, angular: {z: 0.0}}"
```

Wheels: **0, 0**. Robot does **not move at all.** `linear.y` is silently discarded.

> This is the moment the nonholonomic constraint becomes real. The next four phases
> exist to undo this.

## Automation — square drive

After hand-driving, I wrote a state-machine node that drives a 4-sided square:

```python
class SquareDrive(Node):
    def __init__(self):
        super().__init__('square_drive')
        self.pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.state = 'GO_STRAIGHT'
        self.state_start = self.get_clock().now()
        self.side_count = 0
        self.linear_speed = 0.2
        self.angular_speed = 0.5
        self.straight_duration = 3.0
        # 90 degrees at 0.5 rad/s = π/2 / 0.5 ≈ 3.14 s
        self.turn_duration = 3.14159 / 2 / self.angular_speed

    def timer_callback(self):
        elapsed = (self.get_clock().now() - self.state_start).nanoseconds / 1e9
        msg = Twist()

        if self.state == 'GO_STRAIGHT':
            msg.linear.x = self.linear_speed
            if elapsed >= self.straight_duration:
                self.state = 'TURN'
                self.state_start = self.get_clock().now()
        elif self.state == 'TURN':
            msg.angular.z = self.angular_speed
            if elapsed >= self.turn_duration:
                self.side_count += 1
                if self.side_count >= 4:
                    self.state = 'DONE'
                else:
                    self.state = 'GO_STRAIGHT'
                self.state_start = self.get_clock().now()
        self.pub.publish(msg)
```

Full file: [`code/phase1_square_drive.py`](../../code/phase1_square_drive.py).

**The square is not perfect.** This is intentional: open-loop time-based control accumulates
error every cycle. Phase 1's hidden lesson is that without odometry feedback you can't
build precise behavior.

## Lessons

1. **The kinematic equations are physically real, not abstract.** The wheel velocity
   pattern in `/joint_states` matches the inverse kinematics exactly.

2. **The `cmd_vel` interface is a contract — and Phase 1's contract has only 2 DOF.**
   `linear.y` is part of the message schema but not part of the physical capability.

3. **Open-loop control accumulates error.** Even a perfect square plan drifts. Closed-loop
   feedback control (using `/odom`) is the natural next step beyond this journey.

## What I still cannot do

| Action | Possible? | Why |
|---|---|---|
| Sideways motion | ❌ | Nonholonomic constraint |
| Keep heading constant while translating | ❌ | Coupling between linear and angular |
| Parallel parking in one motion | ❌ | Must rotate first |
| 4-wheel independent control | ❌ | Only 2 wheels exist |

**Phase 2 attacks the first three.** ↓

[Phase 2 — Mecanum →]({% post_url 2026-06-14-02-phase2-mecanum %})
