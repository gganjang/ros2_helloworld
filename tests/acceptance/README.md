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

The GitLab pipeline runs ROS package tests and headless acceptance tests in
separate stages. On the default branch, it builds the runtime image with
rootless BuildKit, pushes a commit-tagged candidate to Harbor, runs a smoke
test from that exact image, and promotes it to the final runtime tag only after
the smoke test passes. See [the CI setup guide](../../docs/gitlab-harbor.md)
for Harbor access. The GitHub Actions workflow runs the same ROS tests as
separate jobs, then builds and smoke tests the runtime image locally with
BuildKit. On pushes to `main`, it publishes that tested image to Harbor as
`runtime-<commit SHA>` after the smoke test. Set the `HARBOR_USERNAME` and
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
