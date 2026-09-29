# Shared FR3 development container

The team development image is
`harbor.keti.xrds.kr/physical_ai_hub/ros2-fr3-dev:jazzy`. It contains ROS 2
Jazzy on Ubuntu 24.04, colcon/rosdep, C++ and Python development tools,
MuJoCo `ros2_control`, the controllers used for FR3 simulation, and an
Apache-2.0 licensed FR3 reference scene. It runs as the non-root `ubuntu` user.
Application source, project-specific scenes, model weights, and credentials
are not baked into this shared image.

The full `franka_ros2`/`libfranka` hardware stack is a separate runtime-image
concern in the planned platform: the Control PC host supplies real-time and
driver infrastructure, while the experiment's runtime container supplies
robot-control software. This dev base
supports local FR3 simulation and ROS client development; it does not certify
real-robot control.

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

Each developer repository can use the same image in its own `devcontainer.json`
and add project-specific setup there. A tag `jazzy-<commit SHA>` is also
published for an exact, reproducible base version; use that tag when pinning a
project. The `jazzy` tag follows the most recently published base.

## Maintain the image

`Dockerfile.dev-base` is the prototype source in this repository. On changes to
that file, [the GitHub workflow](../.github/workflows/dev-base.yml) builds the
image with BuildKit, checks ROS and MuJoCo tools, and pushes both tags to Harbor
only after the smoke test. It uses the existing `HARBOR_USERNAME` and
`HARBOR_PASSWORD` GitHub Actions secrets. To build locally:

```bash
docker build -f Dockerfile.dev-base -t ros2-fr3-dev:local .
```

Changes to this base should be reviewed as team-wide environment changes.
Project-specific packages should remain in each developer repository or its
derived image.
