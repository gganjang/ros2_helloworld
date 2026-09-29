#!/usr/bin/env bash
set -eo pipefail

source /opt/franka_ws/install/setup.bash
set -u

test "$(id -un)" = ubuntu
sudo -n true
command -v colcon
command -v rosdep
command -v tmux
command -v rg
command -v jq
command -v nano
command -v vim.tiny
command -v ip
command -v ping
command -v ps
ros2 pkg prefix mujoco_ros2_control
ros2 pkg prefix joint_trajectory_controller
ros2 pkg prefix franka_msgs
ros2 pkg prefix franka_description
ros2 pkg prefix franka_hardware
ros2 pkg prefix franka_bringup
dpkg-query -W -f='${Version}\n' libfranka | grep -Fx '0.20.5'
test -f "$FR3_MUJOCO_SCENE"
python3 -c 'import rclpy'

export ROS_DOMAIN_ID=91
log_file=$(mktemp)
trap 'rm -f "$log_file"' EXIT
set +e
timeout --signal=INT --kill-after=5s 20s \
  ros2 launch franka_bringup franka.launch.py \
    robot_type:=fr3 robot_ip:=dont-care use_fake_hardware:=true \
    load_gripper:=false load_franka_robot_state_broadcaster:=false \
  >"$log_file" 2>&1
launch_status=$?
set -e
if ! { test "$launch_status" -eq 124 &&
       grep -Fq 'mock_components/GenericSystem' "$log_file" &&
       grep -Fq 'Configured and activated joint_state_broadcaster' "$log_file"; }; then
  cat "$log_file"
  exit 1
fi
printf 'Franka fake hardware and joint_state_broadcaster started successfully\n'
