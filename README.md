# Mobile Robot Kinematics Journey

> A 5-phase progressive learning track from Differential Drive to Swerve Drive,
> using ROS2 Humble + Gazebo Classic 11 + Neobotix simulations.

[![Status](https://img.shields.io/badge/status-completed-success)]()
[![ROS2](https://img.shields.io/badge/ROS2-Humble-blue)]()
[![Gazebo](https://img.shields.io/badge/Gazebo-Classic_11-orange)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## What is this?

This is a self-study journey through **5 types of wheeled mobile robot kinematics**,
where each phase progressively adds one new degree of freedom until reaching
**Swerve Drive** — the most sophisticated mobile robot kinematics used in modern
autonomous vehicles and competition robotics (FRC, etc.).

Every phase is verified in simulation with code I wrote myself.

## The 5 Phases

| # | Phase | Robot | Key Concept |
|---|---|---|---|
| 1 | **Differential Drive** | Turtlebot3 Waffle Pi | Two independent wheel speeds → nonholonomic |
| 2 | **Mecanum / Omnidirectional** | Neobotix MPO-500 | Sideways motion via diagonal rollers |
| 3 | **Ackermann (FWD + Front Steer)** | Neobotix MPO-700 (front modules only) | Steering angle φ, turning radius R |
| 4 | **Ackermann + Traction** | Neobotix MPO-700 (front steer + 4WD) | Left/right wheel speed difference |
| 5 | **Swerve Drive** ⭐ | Neobotix MPO-700 (full freedom) | 4 independent steering+driving modules |

## The Capability Matrix

| Action | P1 Diff | P2 Mec | P3 Ack | P4 Ack+T | P5 Swerve |
|---|:---:|:---:|:---:|:---:|:---:|
| Forward | ✅ | ✅ | ✅ | ✅ | ✅ |
| Rotation | ✅ | ✅ | ✅ | ✅ | ✅ |
| Sideways motion | ❌ | ✅ | ❌ | ❌ | ✅ |
| In-place rotation | ✅ | ✅ | ❌ | ❌ | ✅ |
| Independent 4-wheel speed | ❌ | ❌ | ❌ | ✅ | ✅ |
| Independent 4-wheel steering | ❌ | ❌ | ❌ | ❌ | ✅ |
| Slip-free turning | ❌ | ❌ | △ | ✅ | ✅ |

→ **Swerve combines everything**, which is why high-end autonomy chose it.

## Repository structure

```
.
├── README.md                       This file
├── _config.yml                     Jekyll site config
├── _posts/                         Blog posts per phase + analysis
│   ├── 2026-06-13-00-overview.md
│   ├── 2026-06-13-01-phase1-differential.md
│   ├── 2026-06-13-02-phase2-mecanum.md
│   ├── 2026-06-13-03-phase3-ackermann.md
│   ├── 2026-06-13-04-phase4-ackermann-traction.md
│   ├── 2026-06-13-05-phase5-swerve.md
│   ├── 2026-06-13-06-debugging-wsl-gazebo.md
│   ├── 2026-06-13-07-kinematics-vs-dynamics.md
│   └── 2026-06-13-08-comparison-summary.md
├── code/                           Reference Python implementations
│   ├── phase1_square_drive.py
│   ├── phase2_omni_square.py
│   ├── phase3_figure_eight.py
│   ├── phase4_ackermann_traction.py
│   └── phase5_swerve_kinematics.py
└── docs/
    └── setup-environment.md        How to reproduce the env
```

## How to follow

1. Start with the [Overview post](_posts/2026-06-13-00-overview.md)
2. Read each phase in order — they build on each other
3. Try running the Python code on your own ROS2 setup
4. Compare your observations with mine

## Tech stack

- **OS**: Windows 11 → WSL2 → Ubuntu 22.04
- **ROS**: ROS2 Humble
- **Simulator**: Gazebo Classic 11
- **Robot models**: Turtlebot3 Waffle Pi (P1), Neobotix MPO-500 (P2), MPO-700 (P3-5)
- **Visualization**: RViz2
- **Language**: Python 3 (rclpy)

## License

MIT — feel free to use, modify, share, fork.

## Acknowledgments

- [ROS2 Control — Mobile Robot Kinematics](https://control.ros.org/master/doc/ros2_controllers/doc/mobile_robot_kinematics.html) for the canonical kinematics reference
- [Neobotix neo_simulation2](https://github.com/neobotix/neo_simulation2) for the simulation models
- [ROBOTIS](https://emanual.robotis.com/docs/en/platform/turtlebot3/overview/) for Turtlebot3

---

*Journey completed in a month, on a Windows laptop with WSL2. If I can do it, you can too.*
