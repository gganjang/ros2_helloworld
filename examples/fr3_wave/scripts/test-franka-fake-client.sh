#!/usr/bin/env bash
# Run inside the pinned shared FR3 dev image with this repository mounted at /repo.
set -eo pipefail
source /opt/franka_ws/install/setup.bash
export ROS_DOMAIN_ID=93

work_dir=$(mktemp -d)
launch_pid=''
cleanup() {
  if [[ -n "$launch_pid" ]]; then
    kill -TERM "$launch_pid" 2>/dev/null || true
    sleep 1
    kill -KILL "$launch_pid" 2>/dev/null || true
  fi
  rm -rf "$work_dir"
}
trap cleanup EXIT

mkdir -p "$work_dir/ws/src"
cp -a /repo/examples/fr3_wave/src/fr3_wave "$work_dir/ws/src/"
cd "$work_dir/ws"
colcon build --packages-select fr3_wave
source install/setup.bash
set -u

cat > "$work_dir/controllers.yaml" <<'YAML'
controller_manager:
  ros__parameters:
    update_rate: 100
    joint_state_broadcaster:
      type: joint_state_broadcaster/JointStateBroadcaster
    joint_trajectory_controller:
      type: joint_trajectory_controller/JointTrajectoryController
joint_trajectory_controller:
  ros__parameters:
    joints: [fr3_joint1, fr3_joint2, fr3_joint3, fr3_joint4, fr3_joint5, fr3_joint6, fr3_joint7]
    command_interfaces: [position]
    state_interfaces: [position, velocity]
    allow_partial_joints_goal: false
YAML

ros2 launch franka_bringup franka.launch.py \
  robot_type:=fr3 robot_ip:=dont-care use_fake_hardware:=true \
  load_gripper:=false load_franka_robot_state_broadcaster:=false \
  "controllers_yaml:=$work_dir/controllers.yaml" \
  > "$work_dir/launch.log" 2>&1 &
launch_pid=$!

if ! timeout 45s ros2 run controller_manager spawner \
  joint_trajectory_controller --controller-manager /controller_manager \
  > "$work_dir/spawner.log" 2>&1; then
  cat "$work_dir/spawner.log" "$work_dir/launch.log"
  exit 1
fi

if ! timeout 40s ros2 run fr3_wave wave --ros-args \
  -p joint_prefix:=fr3 -p wave_joint:=fr3_joint5 \
  -p amplitude:=0.1 -p cycles:=1 -p period:=1.0 -p settle_time:=1.0 \
  > "$work_dir/wave.log" 2>&1; then
  cat "$work_dir/wave.log" "$work_dir/launch.log"
  exit 1
fi

if ! timeout 40s ros2 run fr3_wave spin --ros-args \
  -p joint_prefix:=fr3 -p amplitude:=0.1 \
  -p segment_time:=0.5 -p settle_time:=1.0 \
  > "$work_dir/spin.log" 2>&1; then
  cat "$work_dir/spin.log" "$work_dir/launch.log"
  exit 1
fi

grep -Fq 'wave on fr3_joint5 complete' "$work_dir/wave.log"
grep -Fq 'base spin complete' "$work_dir/spin.log"
grep -Fq 'mock_components/GenericSystem' "$work_dir/launch.log"
cat "$work_dir/wave.log" "$work_dir/spin.log"
