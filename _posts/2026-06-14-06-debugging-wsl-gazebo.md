---
layout: post
title: "Debugging notes — WSL2, Gazebo Classic, and ROS2 builds"
date: 2026-06-14
categories: [debugging]
tags: [wsl, gazebo, ros2, troubleshooting]
---

This is the post I wish I had read before starting. If you hit any of these on WSL2 +
Gazebo Classic 11 + ROS2 Humble, the fix is here.

---

## 1. Gazebo GUI dies with `boost::shared_ptr Assertion px != 0`

**Symptom**

```
gzclient: /usr/include/boost/smart_ptr/shared_ptr.hpp:728:
  ... Assertion `px != 0' failed.
[ERROR] [gzclient-X]: process has died
```

The GUI window opens, shows black screen, then exits. gzserver keeps running.

**Cause**

WSLg + Gazebo Classic's camera initialization race condition. The graphics context isn't
ready when Ogre tries to attach a camera.

**Fix — separate gzserver and gzclient launches**

```bash
# Terminal 1
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
# This spawns gzserver successfully; gzclient dies. That's OK.

# Wait ~1 minute for the world to fully load.

# Terminal 2
gzclient
# Launching late, after gzserver is stable, usually succeeds.
```

**Convenience aliases**

```bash
alias sim_server='ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py'
alias sim_gui='gzclient'
```

I added many similar aliases throughout the journey:

```bash
# Phase-specific
alias sim_mpo500='ros2 launch neo_simulation2 simulation.launch.py my_robot:=mpo_500 world:=neo_track1'
alias sim_mpo700='ros2 launch neo_simulation2 simulation.launch.py my_robot:=mpo_700 world:=neo_track1'
```

---

## 2. `Service /spawn_entity unavailable. Was Gazebo started with GazeboRosFactory?`

**Symptom**

The robot is not spawned. Gazebo runs the world but no robot model appears in the Models
tree. RViz shows "No transform for [wheel_link]" errors.

**Cause**

`libgazebo_ros_factory.so` is the plugin that exposes `/spawn_entity` as a ROS2 service.
If `GAZEBO_PLUGIN_PATH` doesn't include `/opt/ros/humble/lib`, the plugin isn't loaded.

**Diagnosis**

```bash
echo $GAZEBO_PLUGIN_PATH
# Expected to contain /opt/ros/humble/lib
```

**Fix 1 — Source the right setup files**

```bash
source /opt/ros/humble/setup.bash         # ROS2 sets GAZEBO_PLUGIN_PATH
source ~/ros2_ws/install/setup.bash       # Workspace overlay
# Do NOT source /usr/share/gazebo/setup.bash AFTER ROS2 — it overwrites the plugin path
```

**Fix 2 — Add explicitly**

```bash
echo 'export GAZEBO_PLUGIN_PATH=$GAZEBO_PLUGIN_PATH:/opt/ros/humble/lib' >> ~/.bashrc
exec bash  # start a fresh shell
```

**Fix 3 — `.bashrc` order debugging**

```bash
grep -n "source\|GAZEBO_" ~/.bashrc
```

Order matters. ROS2 sources should be the last ones that touch `GAZEBO_PLUGIN_PATH`.

---

## 3. `Unable to find shader lib. Your GAZEBO_RESOURCE_PATH is probably improperly set`

**Symptom**

```
[Err] [RTShaderSystem.cc:480] Unable to find shader lib.
```

This cascades into rendering failures, then spawn timeouts, then RobotModel "No transform"
errors in RViz.

**Fix**

```bash
source /usr/share/gazebo/setup.bash
echo $GAZEBO_RESOURCE_PATH
# Should contain /usr/share/gazebo-11
```

But be careful with the ordering vs Fix 2 above. The two `setup.bash` files set different
variables. The simplest cleanest answer is:

```bash
# Add to ~/.bashrc, in this order:
source /usr/share/gazebo/setup.bash       # Gazebo resource path
source /opt/ros/humble/setup.bash         # ROS2 — overrides plugin path correctly
source ~/ros2_ws/install/setup.bash       # Workspace
```

ROS2's setup.bash is designed to *add to* Gazebo's, not overwrite it.

---

## 4. Build error: `error: 'subscriber-pkg', 'console_scripts', 'X' has no attribute 'main'`

**Symptom**

```
AttributeError: module 'X' has no attribute 'main'
```

Builds succeed, launch fails immediately.

**Cause**

In your Python node, `def main()` is **indented inside the class** instead of at module level.
A common mistake when refactoring code or copy-pasting.

**Fix**

```python
class MyNode(Node):
    def __init__(self):
        ...

    def some_method(self):
        ...

# def main MUST be at column 0, not indented:
def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(MyNode())
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

Verify with:

```bash
grep -n "^def main\|^if __name__" path/to/your_node.py
```

Both must start at column 0 (no leading whitespace).

---

## 5. `colcon build` builds to wrong directory

**Symptom**

You run `cbp my_package` from somewhere other than `~/ros2_ws`, and `colcon` creates
`build/`, `install/`, `log/` folders in your **current directory** instead of the workspace.

**Cause**

The strict reading of `cbp = 'colcon build --symlink-install --packages-select'` (no `cd`)
means it builds wherever you are.

**Fix — better alias**

```bash
alias cbp='cd ~/ros2_ws && colcon build --symlink-install --packages-select'
```

Or always `cd ~/ros2_ws` first.

---

## 6. `Could not load mesh file:` after rebuild

**Symptom**

RViz shows blank where a robot should be. Or a strange placeholder mesh.

**Cause**

After rebuilding the simulation package, the install/ resource paths might be stale in the
running shell.

**Fix**

```bash
source ~/.bashrc
# or simply: exec bash
```

This re-sources the workspace overlay and any `GAZEBO_MODEL_PATH` updates.

---

## 7. Two `wsl` shells see different `GAZEBO_*` variables

**Symptom**

One terminal works, the next doesn't. Why?

**Cause**

`.bashrc` setup is non-deterministic when sourced multiple times. A clean shell is more
reliable than a shell where you've manually sourced extras.

**Fix**

When in doubt: `exec bash`. It restarts the current shell from scratch.

For systematic reproducibility, write your sources to `.bashrc` in the correct order, and
trust the new terminals to do the right thing.

---

## 8. Audio errors (`ALSA lib confmisc.c:855:(parse_card) cannot find card '0'`)

**Symptom**

Spam in the logs about audio failing.

**Cause**

WSL2 has no real audio device. Gazebo's OpenAL tries to open one anyway.

**Fix**

Ignore them. They are not blocking. You can suppress them with:

```bash
export AL_DRIVER=null
```

if you really want, but it's purely cosmetic.

---

## 9. `xterm: cannot load font` warnings

Also ignorable. xterm tries to load fonts that don't exist in WSL2's minimal X server.
The simulation works fine; the spurious xterm window may be empty.

---

## 10. Slow Gazebo FPS in WSL2

**Symptom**

Real Time Factor consistently below 0.5. Gazebo lags.

**Causes**

- WSL2 doesn't have hardware-accelerated 3D in default config.
- Heavy world (many models, lighting).

**Mitigations**

1. Use simpler worlds (`empty_world` instead of `turtlebot3_world` for early experiments).
2. Reduce physics step rate if your task allows.
3. Update WSL: `wsl --update` from PowerShell. Newer WSL versions have improved graphics.
4. Consider installing NVIDIA WSL drivers if your laptop has an NVIDIA GPU.

For this kinematics-learning project, RTF 0.3-0.5 is acceptable; you're not running closed-loop
control in real time anyway.

---

## Recovery patterns

If multiple of the above happen at once, the cleanest reset is:

```bash
killgazebo                                   # kill any stuck Gazebo processes
killall -9 rviz2                              # if RViz is hung
exec bash                                     # fresh shell, clean env vars
ros2 launch <your_launch_file>                # restart
```

`killgazebo` is just an alias I defined:

```bash
alias killgazebo='killall -9 gazebo & killall -9 gzserver & killall -9 gzclient'
```

I used this maybe 50 times during the journey. Worth saving keystrokes.

---

## What I did NOT debug

- **Migrate to Gazebo Sim (Ignition)**. The neo_simulation2 `humble` branch uses Classic.
  Migration is out of scope.
- **CUDA / GPU acceleration in WSL2**. Possible but adds another rabbit hole.
- **Build farm CI for the workspace**. Personal project, no need.

If any of these become bottlenecks for you, they're solvable but plan a day for each.

---

May your assertions never fail.
