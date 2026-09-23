# Two ROS 2 clients, one MuJoCo controller

`mujoco.launch.py` starts one FR3 MuJoCo simulation and one
`joint_trajectory_controller`. It does not start an application client.
`wave` and `spin` are independent ROS 2 nodes and action clients. Both send
`control_msgs/action/FollowJointTrajectory` goals to the same controller.

`spin` sweeps the base joint in both directions and returns home. The FR3
joint limit does not permit continuous 360-degree rotation.

## Run locally

From the repository root:

```bash
source /opt/ros/jazzy/setup.bash
colcon build --packages-select fr3_wave
source install/setup.bash
ros2 launch fr3_wave mujoco.launch.py scene:=$PWD/assets/models/franka_fr3_v2/scene.xml headless:=false
```

In another terminal, source the same ROS environment and run either client:

```bash
ros2 run fr3_wave wave
ros2 run fr3_wave spin
```

Run them one after the other to see both complete through the same controller.
To see contention, start `wave` in one terminal, then start `spin` while
`wave` is moving. The controller accepts the newer goal, preempts the active
goal, and notifies the first client. It does not execute both trajectories at
once. A job scheduler should serialize motion jobs when both must finish.

For a server without a display, use `headless:=true`. The simulation still
steps MuJoCo physics; only the viewer is disabled. The `scene` path must exist
on the machine that starts MuJoCo. `wave.launch.py` remains as a compatibility
alias for the shared simulator launch.

## Action naming

Both clients default to the relative action name
`joint_trajectory_controller/follow_joint_trajectory`. The controller launched
in the root ROS namespace exposes
`/joint_trajectory_controller/follow_joint_trajectory`.

Each client also accepts `trajectory_action`, so a remote or namespaced
simulator can provide its actual action name without an application code change:

```bash
ros2 run fr3_wave spin --ros-args -p trajectory_action:=/jobs/42/fr3/joint_trajectory_controller/follow_joint_trajectory
```

The simulator server must expose that action name. For separate concurrent
simulation jobs, isolate each simulator and its clients with a namespace or ROS
domain, then configure the matching action name.

## Docker and CI

Build the shared developer/test image from the repository root:

```bash
docker build -t fr3-wave-dev .
docker run --rm -it --name fr3-dev fr3-wave-dev bash
```

Inside the container, start the simulator. The scene is included in the image:

```bash
source /workspace/install/setup.bash
ros2 launch fr3_wave mujoco.launch.py headless:=true
```

In a second host terminal, run either application in that same container:

```bash
docker exec -it fr3-dev bash -lc 'source /workspace/install/setup.bash && ros2 run fr3_wave wave'
docker exec -it fr3-dev bash -lc 'source /workspace/install/setup.bash && ros2 run fr3_wave spin'
```

The Docker image contains ROS 2, MuJoCo, the FR3 simulation assets, and the
project code. It contains no AI model weights. GUI mode requires a host display
connection; the headless commands above work without one.

The GitLab pipeline builds this image on pushes and merge requests, runs ROS
package tests, then runs platform acceptance tests against headless MuJoCo.
A matching GitHub Actions workflow is included for GitHub mirrors. See
[the acceptance test guide](../../tests/acceptance/README.md).

## Control PC runtime image

After the headless acceptance tests pass, CI builds a smaller image containing
only the installed ROS 2 application clients and their runtime dependencies:

```bash
docker build -f Dockerfile.runtime -t fr3-wave-runtime .
```

The default command runs `wave`:

```bash
docker run --rm --network host fr3-wave-runtime
```

Override the command to run `spin`:

```bash
docker run --rm --network host fr3-wave-runtime ros2 run fr3_wave spin
```

The Control PC must already expose the configured
`joint_trajectory_controller/follow_joint_trajectory` action to the container.
ROS discovery settings, such as `ROS_DOMAIN_ID` and the selected RMW transport,
must match the Control PC. The runtime image does not contain MuJoCo, scene
assets, acceptance tests, or AI model weights.
