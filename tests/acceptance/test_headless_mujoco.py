"""Platform acceptance checks against the real headless MuJoCo controller."""

import os
import signal
import subprocess
import threading
import time
from pathlib import Path

import pytest
import rclpy
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionClient
from rclpy.executors import SingleThreadedExecutor
from sensor_msgs.msg import JointState

REPO = Path(__file__).resolve().parents[2]
SCENE = REPO / 'assets/models/franka_fr3_v2/scene.xml'
ACTION = 'joint_trajectory_controller/follow_joint_trajectory'
JOINT_1 = 'fr3v2_joint1'
JOINT_5 = 'fr3v2_joint5'


class Simulation:
    def __init__(self, environment, log_path):
        self.environment = environment
        self.log_path = log_path
        self.samples = []
        self.lock = threading.Lock()
        self.first_state = threading.Event()
        self.log_file = log_path.open('w')
        self.process = subprocess.Popen(
            ['ros2', 'launch', 'fr3_wave', 'mujoco.launch.py',
             f'scene:={SCENE}', 'headless:=true'],
            env=environment, stdout=self.log_file, stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        rclpy.init()
        self.node = rclpy.create_node('platform_acceptance')
        self.node.create_subscription(JointState, '/joint_states', self.record_state, 10)
        self.action_client = ActionClient(
            self.node, FollowJointTrajectory, ACTION)
        self.executor = SingleThreadedExecutor()
        self.executor.add_node(self.node)
        self.spin_thread = threading.Thread(target=self.executor.spin, daemon=True)
        self.spin_thread.start()

    def record_state(self, message):
        positions = dict(zip(message.name, message.position))
        with self.lock:
            self.samples.append(positions)
        self.first_state.set()

    def start_index(self):
        with self.lock:
            return len(self.samples)

    def values_since(self, index, joint):
        with self.lock:
            return [
                sample[joint] for sample in self.samples[index:]
                if joint in sample
            ]

    def wait_for(self, predicate, timeout=15):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate():
                return
            if self.process.poll() is not None:
                pytest.fail(
                    f'MuJoCo exited early with {self.process.returncode}\n'
                    f'{self.log_path.read_text()[-5000:]}')
            time.sleep(0.05)
        pytest.fail(
            f'Timed out waiting for simulator state\n'
            f'{self.log_path.read_text()[-5000:]}')

    def client(self, executable, *ros_args):
        return subprocess.Popen(
            ['ros2', 'run', 'fr3_wave', executable, *ros_args],
            env=self.environment, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True,
        )

    def finish_client(self, process, timeout=35):
        try:
            output, _ = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            output, _ = process.communicate()
            pytest.fail(f'Client timed out:\n{output}')
        return process.returncode, output

    def close(self):
        self.executor.shutdown()
        self.spin_thread.join(timeout=5)
        self.node.destroy_node()
        rclpy.shutdown()
        if self.process.poll() is None:
            os.killpg(self.process.pid, signal.SIGINT)
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(self.process.pid, signal.SIGKILL)
                self.process.wait(timeout=5)
        self.log_file.close()


@pytest.fixture(scope='module')
def sim(tmp_path_factory):
    # Isolate this test's DDS graph from any ROS processes on the CI runner.
    previous_domain = os.environ.get('ROS_DOMAIN_ID')
    domain = str(50 + os.getpid() % 100)
    os.environ['ROS_DOMAIN_ID'] = domain
    environment = os.environ.copy()
    artifact_dir = Path(
        os.environ.get('CI_ARTIFACT_DIR', tmp_path_factory.mktemp('mujoco')))
    artifact_dir.mkdir(parents=True, exist_ok=True)
    simulation = Simulation(environment, artifact_dir / 'mujoco-launch.log')
    try:
        simulation.wait_for(
            lambda: simulation.first_state.is_set()
            and simulation.action_client.wait_for_server(timeout_sec=0.1),
            timeout=45,
        )
        yield simulation
    finally:
        simulation.close()
        if previous_domain is None:
            os.environ.pop('ROS_DOMAIN_ID', None)
        else:
            os.environ['ROS_DOMAIN_ID'] = previous_domain


def assert_motion(sim, index, joint, positive, negative, final_tolerance=0.15):
    values = sim.values_since(index, joint)
    assert values, f'No state samples received for {joint}'
    assert max(values) > positive, f'{joint} did not move positive: {max(values)}'
    assert min(values) < negative, f'{joint} did not move negative: {min(values)}'
    assert abs(values[-1]) < final_tolerance, (
        f'{joint} did not return home: {values[-1]}')


def test_wave_moves_joint_five_and_returns_home(sim):
    index = sim.start_index()
    process = sim.client(
        'wave', '--ros-args', '-p', 'cycles:=1',
        '-p', 'period:=4.0', '-p', 'settle_time:=1.0',
    )
    code, output = sim.finish_client(process)
    assert code == 0, output
    assert 'complete' in output
    assert_motion(sim, index, JOINT_5, positive=0.3, negative=-0.3)


def test_spin_moves_base_joint_and_returns_home(sim):
    index = sim.start_index()
    process = sim.client(
        'spin', '--ros-args', '-p', 'amplitude:=1.0',
        '-p', 'segment_time:=1.5', '-p', 'settle_time:=1.0',
    )
    code, output = sim.finish_client(process)
    assert code == 0, output
    assert 'complete' in output
    assert_motion(sim, index, JOINT_1, positive=0.6, negative=-0.6)


def test_new_client_preempts_active_goal(sim):
    index = sim.start_index()
    wave = sim.client(
        'wave', '--ros-args', '-p', 'cycles:=8',
        '-p', 'period:=2.0', '-p', 'settle_time:=1.0',
    )
    try:
        sim.wait_for(
            lambda: any(abs(value) > 0.15 for value in
                        sim.values_since(index, JOINT_5)),
            timeout=12,
        )
        spin = sim.client(
            'spin', '--ros-args', '-p', 'amplitude:=1.0',
            '-p', 'segment_time:=1.5', '-p', 'settle_time:=1.0',
        )
        spin_code, spin_output = sim.finish_client(spin)
        wave_code, wave_output = sim.finish_client(wave)
        assert spin_code == 0, spin_output
        assert wave_code != 0, wave_output
        assert 'preempted' in wave_output.lower(), wave_output
    finally:
        if wave.poll() is None:
            wave.kill()
            wave.communicate(timeout=5)
