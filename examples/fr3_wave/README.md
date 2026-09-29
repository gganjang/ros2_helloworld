# FR3 wave sample: two ROS 2 clients, one MuJoCo controller

This workspace is an example application. The shared development image is
maintained at the repository root and contains no `fr3_wave` source.

`mujoco.launch.py` starts one FR3 MuJoCo simulation and one
`joint_trajectory_controller`. It does not start an application client.
`wave` and `spin` are independent ROS 2 nodes and action clients. Both send
`control_msgs/action/FollowJointTrajectory` goals to the same controller.

`spin` sweeps the base joint in both directions and returns home. The FR3
joint limit does not permit continuous 360-degree rotation.

## Run locally

From the repository root:

```bash
cd examples/fr3_wave
source /opt/ros/jazzy/setup.bash
colcon build --packages-select fr3_wave
source install/setup.bash
export FR3_MUJOCO_SCENE="$(realpath ../../assets/models/franka_fr3_v2/scene.xml)"
ros2 launch fr3_wave mujoco.launch.py scene:="$FR3_MUJOCO_SCENE" headless:=false
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

## Franka fake-hardware interface check

The MuJoCo scene uses `fr3v2_joint1` through `fr3v2_joint7`. The pinned Franka
robot description uses `fr3_joint1` through `fr3_joint7`. The clients keep the
MuJoCo names by default. For the Franka profile, set `joint_prefix:=fr3`; `wave`
also needs `wave_joint:=fr3_joint5` (or another FR3 joint name).

The shared dev image contains Franka's core ROS packages and `libfranka`. Run
`/repo/examples/fr3_wave/scripts/test-franka-fake-client.sh` in that image with this repository
mounted at `/repo` to build the app, start Franka fake hardware, load a
`joint_trajectory_controller`, and send short `wave` and `spin` goals. GitHub CI runs
this check on the main branch before publishing the app runtime image. Franka's
standard bringup does not load this sample trajectory controller by itself.

This check confirms ROS joint naming, action wiring, and controller activation.
It uses mock hardware. The current runtime image contains the client only;
real-robot operation still requires a validated controller configuration, a
matching robot-system/libfranka version, Control PC network and real-time setup,
and supervised hardware commissioning. The sample trajectory home pose and
limits come from the MuJoCo model and require review against the actual robot
before any physical motion.

## Docker and CI

Build this sample's developer/test image from the repository root:

```bash
docker build -f examples/fr3_wave/Dockerfile.dev -t fr3-wave-dev .
docker run --rm -it --name fr3-dev fr3-wave-dev bash
```

Inside the container, start the simulator. The scene is included in the image:

```bash
source /workspace/examples/fr3_wave/install/setup.bash
ros2 launch fr3_wave mujoco.launch.py headless:=true
```

In a second host terminal, run either application in that same container:

```bash
docker exec -it fr3-dev bash -lc 'source /workspace/examples/fr3_wave/install/setup.bash && ros2 run fr3_wave wave'
docker exec -it fr3-dev bash -lc 'source /workspace/examples/fr3_wave/install/setup.bash && ros2 run fr3_wave spin'
```

The Docker image contains ROS 2, MuJoCo, the FR3 simulation assets, and the
project code. It contains no AI model weights. GUI mode requires a host display
connection; the headless commands above work without one.

GitHub Actions currently runs package, MuJoCo, and Franka fake-hardware
acceptance jobs before publishing the sample runtime image to Harbor. The
GitLab pipeline is retained for when its runner environment is repaired.
The [shared dev container guide](../../docs/dev-container.md) explains the
reusable team base image; the bundled image above is specific to this sample.
See [the acceptance test guide](tests/acceptance/README.md).

## Client-only runtime prototype

After the headless acceptance tests pass, CI builds a smaller image containing
only the installed ROS 2 application clients and their runtime dependencies:

```bash
docker build -f examples/fr3_wave/Dockerfile.runtime -t fr3-wave-runtime .
```

The default command runs `wave`:

```bash
docker run --rm --network host fr3-wave-runtime
```

Override the command to run `spin`:

```bash
docker run --rm --network host fr3-wave-runtime ros2 run fr3_wave spin
```

The Control PC or simulator must already expose the configured
`joint_trajectory_controller/follow_joint_trajectory` action to the container.
This image has not been commissioned for real-robot execution.
ROS discovery settings, such as `ROS_DOMAIN_ID` and the selected RMW transport,
must match the Control PC. The runtime image does not contain MuJoCo, scene
assets, acceptance tests, or AI model weights.
