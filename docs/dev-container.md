# Shared FR3 development container

The team development image is pinned below to the immutable
`jazzy-0c84c486a85aed0a8cb18114f82ab89b964c0af9` tag. It contains ROS 2
Jazzy on Ubuntu 24.04, colcon/rosdep, C++ and Python development tools,
MuJoCo `ros2_control`, the controllers used for FR3 simulation, an
Apache-2.0 licensed FR3 reference scene, and the core Franka ROS 2 packages
(`franka_msgs`, `franka_hardware`, `franka_bringup`, and `franka_description`).
It also has `tmux`, `nano`, Vim, `rg`, `jq`, `less`, `tree`, `htop`, and
basic process/network diagnostics (`ps`, `ip`, `ping`, `lsof`). Samba server
and client tools are installed for sharing a development workspace. It runs as
the non-root `ubuntu` user.
Application source, project-specific scenes, model weights, and credentials
are not baked into this shared image.

The Franka packages come from `franka_ros2` v3.5.3, with `libfranka` 0.20.5
and `franka_description` 2.9.0. These pinned versions let developers build
against Franka APIs and start the ROS controller stack with fake hardware.
Other upstream packages, including gripper, examples, MoveIt, and Gazebo
integration, are outside this base. Optional RViz and joystick/teleoperation
dependencies are also omitted from the shared headless image. The future
runtime image must contain the packages its application needs. The Control PC
host will provide the real-time, network, and driver infrastructure. No robot or firmware compatibility has yet
been verified. The sample app still defaults to the MuJoCo `fr3v2_joint*`
names; the Franka mock integration check uses its `fr3_joint*` profile. See
[the sample app guide](../examples/fr3_wave/README.md#franka-fake-hardware-interface-check).

## Start a new application

The group owner provides developers with **pull-only** Harbor credentials. On
the remote Ubuntu development server that runs Docker, log in once:

```bash
docker login harbor.keti.xrds.kr
```

Create an empty project folder or open the developer's own Git repository. Add
`.devcontainer/devcontainer.json` with this content (also available as
[the generic config in this repository](../.devcontainer/devcontainer.json)):

```json
{
  "name": "FR3 shared ROS 2 Jazzy development",
  "image": "harbor.keti.xrds.kr/physical_ai_hub/ros2-fr3-dev:jazzy-0c84c486a85aed0a8cb18114f82ab89b964c0af9",
  "remoteUser": "ubuntu",
  "workspaceFolder": "/workspaces/${localWorkspaceFolderBasename}"
}
```

In VS Code, connect to the development server with Remote SSH, open that
project folder, and choose **Dev Containers: Reopen in Container**. VS Code
mounts the folder into the image. The developer can create source files and
build their own ROS package there. There is no sample-specific
`postCreateCommand`; the image contains no application source. Keep Harbor
credentials on the development server, outside the config file.

For a terminal-only start, from an empty or existing project directory on the
development server:

```bash
docker run --rm -it \
  --mount "type=bind,src=$PWD,dst=/workspaces/app" \
  --workdir /workspaces/app \
  harbor.keti.xrds.kr/physical_ai_hub/ros2-fr3-dev:jazzy-0c84c486a85aed0a8cb18114f82ab89b964c0af9 \
  bash
```

The bind mount keeps application files on the development server. With the
terminal-only command, ensure the container's `ubuntu` user can write to that
host directory. VS Code Dev Containers can adjust the container user's UID for
this case.

## Try the optional sample

Clone this repository only to try `fr3_wave`. Open it with the generic
configuration above, then in the container terminal run:

```bash
cd examples/fr3_wave
colcon build --symlink-install --packages-select fr3_wave
source install/setup.bash
ros2 launch fr3_wave mujoco.launch.py headless:=true
```

The sample uses the reference scene already in the image. See
[the sample app guide](../examples/fr3_wave/README.md) for its clients and
acceptance tests.

To check the Franka ROS control interface without a robot, run:

```bash
ros2 launch franka_bringup franka.launch.py \
  robot_type:=fr3 robot_ip:=dont-care use_fake_hardware:=true \
  load_gripper:=false load_franka_robot_state_broadcaster:=false
```

This starts `franka_hardware` through ROS 2 mock components and activates
`joint_state_broadcaster`. It checks package loading and controller wiring. It
does not open an FCI connection, establish firmware compatibility, meet real-time
timing, or move an arm. Stop the launch with Ctrl-C.

## Keep development and runtime compatible

This published dev image fixes Ubuntu 24.04, ROS 2 Jazzy, Python 3.12, and its
installed Franka/MuJoCo packages for the team. The shared dev image **does not
provide CUDA**. Installing packages interactively with `sudo` changes only one
developer's container; record project dependencies in a Dockerfile or other
versioned dependency files and build them in CI.

Each application needs its own tested runtime image for the Control PC. Its
runtime Dockerfile must include the application's code and pinned runtime
dependencies. Developers who need CUDA add the required CUDA user-space
libraries to their own runtime image. If they also need CUDA while developing,
they can define a project-specific dev image based on the shared image; that
does not change the team's base. CI should build and test the runtime image
before publishing it to Harbor. The Control PC supplies a compatible NVIDIA
driver, GPU, real-time and network infrastructure. A common dev base alone
does not guarantee runtime compatibility, and the current `fr3_wave` runtime
has not been validated with a physical arm.

## Share the workspace with Samba

Samba is installed but does not start automatically. To make the share reachable
from another machine, add a port mapping to the project's
`.devcontainer/devcontainer.json` **before** reopening the container. Bind to
an address on the trusted development network, for example:

```json
"runArgs": ["--publish", "10.0.0.15:445:445"]
```

Replace `10.0.0.15` with the development server's own private IP. Docker must
be able to bind TCP 445 on that server; a host Samba service using the port
must be stopped or a different host arrangement chosen. Limit access to the
trusted network with the server firewall. The shared image does not publish a
port by itself.

In the dev container terminal, run this from the project directory to share:

```bash
start-samba-share "$PWD"
```

The script creates the authenticated `workspace` share for that directory,
asks for a Samba password for the container's `ubuntu` user, and starts `smbd`.
It does not enable guest access or save the password in the repository. Connect
from another machine to `//10.0.0.15/workspace` (or
`\\10.0.0.15\workspace` on Windows) as `ubuntu` with that Samba password.
The share permits writes as the container's `ubuntu` user. Run the setup again
if the container is recreated, since its Samba account database is stored in
the container filesystem.

## Maintain the image

`Dockerfile.dev-base` is the prototype source in this repository. On changes to
that file or the bundled FR3 model assets,
[the GitHub workflow](../.github/workflows/dev-base.yml) builds the image with
BuildKit, checks ROS, MuJoCo, Franka packages, and fake-hardware launch, then
pushes both tags to Harbor only after the smoke test. It uses the existing
`HARBOR_USERNAME` and `HARBOR_PASSWORD` GitHub Actions secrets. To build locally:

```bash
docker build -f Dockerfile.dev-base -t ros2-fr3-dev:local .
```

Changes to this base should be reviewed as team-wide environment changes.
Project-specific packages should remain in each developer repository or its
derived image.
