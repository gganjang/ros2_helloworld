# Platform acceptance tests

These tests belong to the platform. They start one real headless MuJoCo
simulation, run both ROS 2 clients, inspect measured joint states, and verify
that a second trajectory goal preempts the first. A client log message alone
cannot satisfy the motion checks.

Run from the repository root after building `fr3_wave`:

```bash
source /opt/ros/jazzy/setup.bash
colcon build --packages-select fr3_wave
source install/setup.bash
/usr/bin/python3 -m pytest -q tests/acceptance
```

Use the system Python that matches the installed ROS 2 distribution. The test
assigns a separate ROS domain and writes the simulator log to a temporary
directory, or to `CI_ARTIFACT_DIR` when that variable is set.

The GitLab pipeline builds the development/test image, runs package tests and
these acceptance tests inside it, and only then builds and checks the Control
PC runtime image. A matching GitHub Actions workflow supports GitHub mirrors.
Configure the repository branch rules to require the `acceptance` job before
merging; the workflow alone does not enforce a merge gate.

The headless MuJoCo job requires an x86-64 runner that exposes AVX in
`/proc/cpuinfo`. Containers use the runner host CPU instruction set, so a
Docker image cannot supply a missing CPU feature. For a virtual-machine runner,
enable host CPU passthrough; otherwise assign the job to an AVX-capable runner.
The GitLab and GitHub Actions jobs check this requirement before building the
images and report a clear error when the runner is incompatible.
