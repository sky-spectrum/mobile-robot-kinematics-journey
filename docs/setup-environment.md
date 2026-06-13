# Environment Setup

How to reproduce the development environment used throughout this journey.

## Host

- Windows 11
- WSL2 with Ubuntu 22.04
- VSCode (with WSL extension)

## ROS2

```bash
# Locale (must be UTF-8)
sudo apt update && sudo apt install locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

# ROS2 Humble apt source
sudo apt install software-properties-common -y
sudo add-apt-repository universe -y
sudo apt update && sudo apt install curl -y
export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F'"' '{print $4}')
curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME})_all.deb"
sudo dpkg -i /tmp/ros2-apt-source.deb

# Install ROS2 Humble desktop + dev tools
sudo apt update
sudo apt install ros-humble-desktop ros-dev-tools -y
```

In `~/.bashrc`:

```bash
source /opt/ros/humble/setup.bash
```

## Workspace

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws
colcon build --symlink-install
```

In `~/.bashrc`:

```bash
source ~/ros2_ws/install/setup.bash
```

## Gazebo Classic 11

Comes with `ros-humble-gazebo-*` packages:

```bash
sudo apt install ros-humble-gazebo-* -y
sudo apt install ros-humble-cartographer ros-humble-cartographer-ros -y
sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup -y
sudo apt install ros-humble-teleop-twist-keyboard -y
sudo apt install python3-colcon-common-extensions -y
```

## Robot simulations

### Turtlebot3 (Phase 1)

```bash
cd ~/ros2_ws/src
git clone -b humble https://github.com/ROBOTIS-GIT/DynamixelSDK.git
git clone -b humble https://github.com/ROBOTIS-GIT/turtlebot3_msgs.git
git clone -b humble https://github.com/ROBOTIS-GIT/turtlebot3.git
git clone -b humble https://github.com/ROBOTIS-GIT/turtlebot3_simulations.git
cd ~/ros2_ws
colcon build --symlink-install
```

In `~/.bashrc`:

```bash
export TURTLEBOT3_MODEL=waffle_pi
```

### Neobotix simulations (Phase 2–5)

```bash
cd ~/ros2_ws/src
git clone -b humble https://github.com/neobotix/neo_simulation2.git
git clone -b humble https://github.com/neobotix/neo_local_planner2.git
git clone -b humble https://github.com/neobotix/neo_localization2.git
git clone https://github.com/neobotix/neo_common2.git
git clone https://github.com/neobotix/neo_msgs2.git
git clone https://github.com/neobotix/neo_srvs2.git

cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -r -y || true
colcon build --symlink-install
```

## Critical environment variables

The biggest debugging time sink in this journey was getting `GAZEBO_PLUGIN_PATH` right.
The correct `.bashrc` order:

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
# Do NOT source /usr/share/gazebo/setup.bash after the ROS2 ones — it can overwrite
# GAZEBO_PLUGIN_PATH and break /spawn_entity.
```

If something goes wrong, verify:

```bash
echo $GAZEBO_PLUGIN_PATH        # should include /opt/ros/humble/lib
echo $GAZEBO_RESOURCE_PATH      # should include /usr/share/gazebo-11
echo $GAZEBO_MODEL_PATH         # should include workspace install/share paths
```

## Useful aliases

The ones I added through the project:

```bash
# Build shortcuts
alias cb='cd ~/ros2_ws && colcon build --symlink-install'
alias cbp='cd ~/ros2_ws && colcon build --symlink-install --packages-select'

# Kill Gazebo
alias killgazebo='killall -9 gazebo & killall -9 gzserver & killall -9 gzclient'

# Phase-specific sim launchers
alias sim_tb3='ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py'
alias sim_tb3_empty='ros2 launch turtlebot3_gazebo empty_world.launch.py'
alias sim_mp400='ros2 launch neo_simulation2 simulation.launch.py my_robot:=mp_400 world:=neo_track1'
alias sim_mpo500='ros2 launch neo_simulation2 simulation.launch.py my_robot:=mpo_500 world:=neo_track1'
alias sim_mpo700='ros2 launch neo_simulation2 simulation.launch.py my_robot:=mpo_700 world:=neo_track1'
alias sim_gui='gzclient'
```

## Recommended VSCode setup

1. Install the **WSL** extension (Microsoft).
2. Open the workspace from WSL: `code ~/ros2_ws` from the WSL shell.
3. VSCode extensions that helped:
   - Python (Microsoft)
   - C/C++
   - CMake
   - ROS (Microsoft)
   - YAML

## Hardware requirements

- 16 GB RAM recommended (8 GB minimum but Gazebo + RViz + VSCode can chew)
- 50+ GB free disk
- Multi-core CPU (4+ helps with Gazebo physics)

If running on lower spec, use `empty_world` for early phases and prefer headless Gazebo
(don't run gzclient) when not actively visualizing.

## Verifying your setup

A quick smoke test after install:

```bash
# Should print 'humble'
echo $ROS_DISTRO

# Should run without errors and print "All 4 checks passed"
ros2 doctor

# Should list installed packages including turtlebot3* and neo_*
ros2 pkg list | grep -E "turtlebot3|neo_"

# Should launch and run (kill with Ctrl+C)
ros2 launch turtlebot3_gazebo empty_world.launch.py
```

If all four work, you're ready for Phase 1.
