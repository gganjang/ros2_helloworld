# FR3 development image and sample application

This repository prototypes a shared ROS 2 Jazzy development image and shows
how one application can use it. The `fr3_wave` application is a **sample**;
team members develop their own applications in their own repositories.

| Path | Purpose |
| --- | --- |
| [`Dockerfile.dev-base`](Dockerfile.dev-base) | Shared ROS 2, MuJoCo, Franka, and development tools image. |
| [`.devcontainer/devcontainer.json`](.devcontainer/devcontainer.json) | This sample repository's VS Code configuration using the published shared image. |
| [`examples/fr3_wave/`](examples/fr3_wave/) | Standalone ROS workspace for the `wave` and `spin` sample clients, acceptance tests, and sample Dockerfiles. |
| [`assets/models/franka_fr3_v2/`](assets/models/franka_fr3_v2/) | Licensed FR3 reference scene used by the shared image and the sample. |
| [`docs/dev-container.md`](docs/dev-container.md) | Developer setup, Harbor pull access, and optional Samba share. |

## Try the sample

Open this repository with VS Code Remote SSH and **Dev Containers: Reopen in
Container**. The repository's devcontainer config builds the sample workspace
under `examples/fr3_wave`. In a container terminal:

```bash
cd examples/fr3_wave
source install/setup.bash
ros2 launch fr3_wave mujoco.launch.py headless:=true
```

Run `ros2 run fr3_wave wave` or `ros2 run fr3_wave spin` in another terminal
that has sourced the same workspace. See the [sample guide](examples/fr3_wave/README.md)
for local builds, fake-hardware checks, and the client-only runtime image.

For a different application, commit a `.devcontainer/devcontainer.json` in its
own repository that uses the shared image and that project's setup command.
The shared image does not contain `fr3_wave` source. Its immutable published
tag is `harbor.keti.xrds.kr/physical_ai_hub/ros2-fr3-dev:jazzy-0c84c486a85aed0a8cb18114f82ab89b964c0af9`.

GitHub Actions is the active CI platform while the GitLab runner environment
is being repaired. Changes to this sample do not rebuild or republish the
shared development image.
