---
layout: post
title: "Phase 3 — Ackermann (FWD + Front Steer) on MPO-700"
date: 2026-06-14
categories: [phase]
tags: [ackermann, mpo-700, steering]
---

The first phase where the robot has a steering angle as input. Also the first phase where
we *voluntarily* refuse to use part of the cmd_vel interface — to feel what a real car
can and cannot do.

## A philosophical shift

Phase 1 → Phase 2 added a degree of freedom (sideways motion).
**Phase 2 → Phase 3 takes one away.** And we gain precision in return.

Why would we ever want to give up `linear.y`? Because:

- Real cars cannot move sideways. If we're designing autonomy for cars, we need
  algorithms that work under the Ackermann constraint.
- Steering geometry is dramatically more efficient at high speed than mecanum.
- A steered wheel can be designed for any terrain (real tires!).

So Phase 3 is about training the autonomy mindset for the most common platform on the
planet — the wheeled car.

## The kinematics — Bicycle Model

Two wheels, simplified to one front (steered) and one rear (driven):

```
Forward kinematics:
  ẋ = v · cos(θ)
  ẏ = v · sin(θ)
  θ̇ = v · tan(φ) / l
```

Where `v` is rear-wheel speed, `φ` is steering angle, `l` is wheelbase, `θ` is heading.

Key derived quantities:

```
Turning radius:  R = l / tan(φ)
Required steering for desired (v, ω):  φ = arctan(l · ω / v)
```

Two takeaways:

1. `φ = 0` ⇒ `R = ∞` ⇒ straight line. No steering, no curve.
2. There's a maximum `φ` (mechanical limit). So there's a minimum turning radius
   `R_min = l / tan(φ_max)`. Cars cannot do tight U-turns in narrow streets.

## The trick — use MPO-700 with constraint

MPO-700 is a swerve drive (Phase 5). For Phase 3, I refuse to use:

- `linear.y` (no sideways)
- The rear modules (Phase 4 will turn them on)

The simulation still runs the full swerve internally, but I only send commands that an
Ackermann robot could execute. **The constraint is in my code, not in the robot.**

## Launch

```bash
ros2 launch neo_simulation2 simulation.launch.py my_robot:=mpo_700 world:=neo_track1
```

Wheelbase and tracks via TF:

```bash
ros2 run tf2_ros tf2_echo mpo_700_wheel_front_left_link mpo_700_wheel_back_left_link
# Translation: [-0.480, 0.000, 0.000]  → l = 0.480 m

ros2 run tf2_ros tf2_echo mpo_700_wheel_back_left_link mpo_700_wheel_back_right_link
# Translation: [0.000, -0.450, 0.000]  → w_r = 0.450 m
```

## Experiments — verifying the Ackermann equations

Send a series of cmd_vel commands. For each, compute `R = v/ω` and `φ = arctan(l/R)`,
and check whether the simulation behaves like that radius.

### Experiment 1 — Straight

```bash
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.3}, angular: {z: 0.0}}"
```

Expected `R = ∞`, `φ = 0°`. Robot goes straight.

### Experiment 2 — Wide curve

```bash
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.3}, angular: {z: 0.3}}"
```

Expected:
- `R = 0.3 / 0.3 = 1.0 m`
- `φ = arctan(0.48 / 1.0) ≈ 25.6°`

The robot should circle on a 1m-radius arc. Compare with Gazebo's grid (1m squares).

### Experiment 3 — Tight curve

```bash
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.2}, angular: {z: 0.5}}"
```

Expected:
- `R = 0.4 m`
- `φ ≈ 50.2°` — close to a typical car's steering limit

### Experiment 4 — Beyond Ackermann

```bash
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.1}, angular: {z: 1.0}}"
```

`R = 0.1 m`, `φ ≈ 78°`. **No real car can steer 78°.** But MPO-700 still moves — because
internally it's swerve, not Ackermann. This is the moment to feel the difference:
*the Ackermann equation says "no", the swerve robot says "yes anyway"*.

### Experiment 5 — In-place rotation

```bash
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0}, angular: {z: 0.5}}"
```

`R = 0 / 0.5 = 0`. **For Ackermann, this is undefined: cars cannot turn in place.**
For swerve, it works fine. Same gap as Experiment 4, more extreme.

## Automation — figure-of-eight

The natural Ackermann pattern is the figure-of-eight (you draw one in driving school):

```python
class FigureEight(Node):
    def __init__(self):
        super().__init__('figure_eight')
        self.pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.wheelbase = 0.480
        self.linear_speed = 0.3
        self.angular_speed = 0.5
        self.half_loop_time = 4.0
        self.state = 'LEFT_TURN'
        self.state_start = self.get_clock().now()
        self.loop_count = 0
        # Predict and log the required steering angle
        radius = self.linear_speed / self.angular_speed
        steering = math.atan(self.wheelbase / radius)
        self.get_logger().info(
            f'R = {radius:.3f} m, required φ = {math.degrees(steering):.1f}°')

    def timer_callback(self):
        elapsed = (self.get_clock().now() - self.state_start).nanoseconds / 1e9
        msg = Twist()
        msg.linear.x = self.linear_speed
        # The discipline: linear.y is NEVER set.
        if self.state == 'LEFT_TURN':
            msg.angular.z = self.angular_speed
        elif self.state == 'RIGHT_TURN':
            msg.angular.z = -self.angular_speed
        self.pub.publish(msg)
        if elapsed >= self.half_loop_time:
            self.state = 'RIGHT_TURN' if self.state=='LEFT_TURN' else 'LEFT_TURN'
            self.state_start = self.get_clock().now()
            self.loop_count += 1
```

Full file: [`code/phase3_figure_eight.py`](../../code/phase3_figure_eight.py).

The node also **logs the steering angle the kinematics requires** at startup, even though
the simulator is internally swerve. The discipline of computing the Ackermann-required
value teaches the kinematics directly.

## Phase 2 vs Phase 3

| | P2 Mecanum | P3 Ackermann |
|---|---|---|
| DOF | 3 (`v_x`, `v_y`, `ω_z`) | 2 (`v_x`, `ω_z`) |
| Sideways | ✅ | ❌ |
| In-place rotation | ✅ | ❌ |
| Precise steering | ❌ | ✅ |
| Efficient high speed | ❌ | ✅ |
| New concept | Omnidirectional | **Steering angle φ, radius R** |

## What Phase 3 still cannot do (correctly)

| Issue | Why |
|---|---|
| Slip-free turning | Both rear wheels assumed equal speed |
| Slip-free turning | Both front wheels assumed equal angle |

Real cars solve this with a **differential gear** (rear) and **Ackermann steering linkage**
(front). Phase 4 will solve it in code.

[Phase 4 — Ackermann + Traction →]({% post_url 2026-06-14-04-phase4-ackermann-traction %})
