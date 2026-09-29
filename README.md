# FR3 development image and sample application

This repository prototypes a shared ROS 2 Jazzy development image and shows
how one application can use it. The `fr3_wave` application is a **sample**;
team members develop their own applications in their own repositories.

| Path | Purpose |
| --- | --- |
| [`Dockerfile.dev-base`](Dockerfile.dev-base) | Shared ROS 2, MuJoCo, Franka, and development tools image. |
| [`.devcontainer/devcontainer.json`](.devcontainer/devcontainer.json) | Reusable VS Code configuration using the pinned shared image; no sample-specific setup. |
| [`examples/fr3_wave/`](examples/fr3_wave/) | Standalone ROS workspace for the `wave` and `spin` sample clients, acceptance tests, and sample Dockerfiles. |
| [`assets/models/franka_fr3_v2/`](assets/models/franka_fr3_v2/) | Licensed FR3 reference scene used by the shared image and the sample. |
| [`docs/dev-container.md`](docs/dev-container.md) | Developer setup, Harbor pull access, and optional Samba share. |

To run the bundled FR3 MuJoCo simulator from any project opened in the shared
dev image, use `ros2 launch /opt/franka/fr3v2/launch/mujoco.launch.py
headless:=true`. The sample repository is only needed for its application
clients and tests.

## Try the sample

Open this repository with VS Code Remote SSH and **Dev Containers: Reopen in
Container**. The generic devcontainer opens the shared image and mounts this
repository. Build the optional sample in a container terminal:

```bash
cd examples/fr3_wave
colcon build --symlink-install --packages-select fr3_wave
source install/setup.bash
ros2 launch fr3_wave mujoco.launch.py headless:=true
```

Run `ros2 run fr3_wave wave` or `ros2 run fr3_wave spin` in another terminal
that has sourced the same workspace. See the [sample guide](examples/fr3_wave/README.md)
for local builds, fake-hardware checks, and the client-only runtime image.

For a new application, create an empty project folder or open its own Git
repository, then copy this generic `.devcontainer/devcontainer.json` into it.
No `fr3_wave` checkout or `postCreateCommand` is required. The shared image
does not contain `fr3_wave` source. Its immutable published
tag is `harbor.keti.xrds.kr/physical_ai_hub/ros2-fr3-dev:jazzy-17887f598440ce4106c1bbd068d04ee560fd9709`.

GitHub Actions is the active CI platform while the GitLab runner environment
is being repaired. Changes to this sample do not rebuild or republish the
shared development image.
