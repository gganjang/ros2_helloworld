# FR3 wave sample acceptance tests

These tests belong to the `fr3_wave` sample. They start one real headless MuJoCo
simulation, run both ROS 2 clients, inspect measured joint states, and verify
that a second trajectory goal preempts the first. A client log message alone
cannot satisfy the motion checks.

From the repository root, enter the sample workspace and run:

```bash
cd examples/fr3_wave
source /opt/ros/jazzy/setup.bash
colcon build --packages-select fr3_wave
source install/setup.bash
/usr/bin/python3 -m pytest -q tests/acceptance
```

Use the system Python that matches the installed ROS 2 distribution. The test
assigns a separate ROS domain and writes the simulator log to a temporary
directory, or to `CI_ARTIFACT_DIR` when that variable is set.

GitHub Actions is the active CI while the GitLab runner is being repaired. It
runs the ROS package, headless MuJoCo, and Franka fake-hardware checks as
separate jobs. On pushes to `main`, it builds and smoke-tests the sample runtime
image, then publishes `runtime-<commit SHA>` to Harbor. The GitLab pipeline
retains its staged BuildKit candidate/smoke/promotion flow for later use; see
[the CI setup guide](../../../../docs/gitlab-harbor.md). Set the `HARBOR_USERNAME` and
`HARBOR_PASSWORD` GitHub Actions repository secrets to the Harbor robot account
credentials; pull requests run the tests without those secrets.
Configure the repository branch rules to require the `headless-acceptance` job
before merging; the workflow alone does not enforce a merge gate.

The headless MuJoCo job requires an x86-64 runner that exposes AVX in
`/proc/cpuinfo`. Containers use the runner host CPU instruction set, so a
Docker image cannot supply a missing CPU feature. For a virtual-machine runner,
enable host CPU passthrough; otherwise assign the job to an AVX-capable runner.
The GitLab and GitHub Actions jobs check this requirement before running the
headless acceptance tests and report a clear error when the runner is incompatible.
