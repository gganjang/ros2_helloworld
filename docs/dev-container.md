# Shared FR3 development container

The team development image is
`harbor.keti.xrds.kr/physical_ai_hub/ros2-fr3-dev:jazzy`. It contains ROS 2
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
[the app guide](../src/fr3_wave/README.md#franka-fake-hardware-interface-check).

## Use it in this repository

The group owner should provide a separate **pull-only** Harbor robot account for
development servers. Keep the CI robot with push permission in CI secrets.

1. Log in to `harbor.keti.xrds.kr` with **pull-only** Harbor credentials on the
   Ubuntu development server. For example, use `docker login
   harbor.keti.xrds.kr`; do not put credentials in `devcontainer.json`.
2. Open this repository on that server with VS Code Remote SSH, then choose
   **Dev Containers: Reopen in Container**. The configuration at
   [`.devcontainer/devcontainer.json`](../.devcontainer/devcontainer.json)
   pulls the shared image, mounts the repository, and builds `fr3_wave` with
   `colcon --symlink-install`.
3. In the container terminal, run `source install/setup.bash`, then, for a
   headless simulation, run `ros2 launch fr3_wave mujoco.launch.py
   headless:=true`. The scene path comes from the mounted repository.

To check the ROS control interface without a robot, run this in the dev container:

```bash
ros2 launch franka_bringup franka.launch.py \
  robot_type:=fr3 robot_ip:=dont-care use_fake_hardware:=true \
  load_gripper:=false load_franka_robot_state_broadcaster:=false
```

This should start `franka_hardware` through ROS 2 mock components and activate
`joint_state_broadcaster`. It checks package loading and controller wiring. It
does not open an FCI connection, establish firmware compatibility, meet real-time
timing, or move an arm. Stop the launch with Ctrl-C.

Each developer repository can use the same image in its own `devcontainer.json`
and add project-specific setup there. A tag `jazzy-<commit SHA>` is also
published for an exact, reproducible base version; use that tag when pinning a
project. The `jazzy` tag follows the most recently published base.

## Share the workspace with Samba

Samba is installed but does not start automatically. To make the share reachable
from another machine, add a port mapping to this repository's
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

In the dev container terminal, run this from the repository root:

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
