#!/usr/bin/env bash
set -eo pipefail

source /opt/franka_ws/install/setup.bash
set -u

test "$(id -un)" = ubuntu
sudo -n true
# The shared base stays CUDA-free; projects own CUDA in their runtime images.
! command -v nvcc >/dev/null 2>&1
test ! -d /usr/local/cuda
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
command -v smbd
command -v smbclient
command -v testparm
command -v start-samba-share
ros2 pkg prefix mujoco_ros2_control
ros2 pkg prefix joint_trajectory_controller
ros2 pkg prefix franka_msgs
ros2 pkg prefix franka_description
ros2 pkg prefix franka_hardware
ros2 pkg prefix franka_bringup
dpkg-query -W -f='${Version}\n' libfranka | grep -Fx '0.20.5'
test -f "$FR3_MUJOCO_SCENE"
python3 -c 'import rclpy'

# Verify the Samba server can authenticate and write a workspace file.
share_dir=$(mktemp -d /workspaces/samba-smoke.XXXXXX)
auth_file=$(mktemp)
log_file=$(mktemp)
trap 'rm -rf "$share_dir" "$auth_file" "$log_file"' EXIT
password="Ci$(date +%s)${RANDOM}${RANDOM}"
printf 'username = ubuntu\npassword = %s\n' "$password" > "$auth_file"
chmod 0600 "$auth_file"
printf '%s\n%s\n' "$password" "$password" | start-samba-share "$share_dir"
printf 'Samba write check\n' > /tmp/samba-smoke.txt
sleep 1
smbclient //127.0.0.1/workspace -A "$auth_file" \
  -c 'put /tmp/samba-smoke.txt smoke.txt'
test "$(cat "$share_dir/smoke.txt")" = 'Samba write check'

export ROS_DOMAIN_ID=91
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
