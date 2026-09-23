"""Joint data and trajectory helpers shared by the FR3 action clients."""

import rclpy
from builtin_interfaces.msg import Duration
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint

JOINTS = [f'fr3v2_joint{i}' for i in range(1, 8)]

# Limits from assets/models/franka_fr3_v2/fr3v2.xml.
LIMITS = {
    'fr3v2_joint1': (-2.7437, 2.7437),
    'fr3v2_joint2': (-1.7837, 1.7837),
    'fr3v2_joint3': (-2.9007, 2.9007),
    'fr3v2_joint4': (-3.0421, -0.1518),
    'fr3v2_joint5': (-2.8065, 2.8065),
    'fr3v2_joint6': (0.5445, 4.5169),
    'fr3v2_joint7': (-3.0159, 3.0159),
}

HOME = [0.0, 0.0, 0.0, -1.57079, 0.0, 1.57079, -0.7853]
MARGIN = 0.05
DEFAULT_ACTION = 'joint_trajectory_controller/follow_joint_trajectory'


def clamp(name, value):
    low, high = LIMITS[name]
    return min(max(value, low + MARGIN), high - MARGIN)


def point(positions, seconds):
    result = JointTrajectoryPoint()
    result.positions = [float(value) for value in positions]
    result.velocities = [0.0] * len(positions)
    result.time_from_start = Duration(
        sec=int(seconds), nanosec=int((seconds % 1.0) * 1e9))
    return result


def send_trajectory(node, client, trajectory, label):
    node.get_logger().info('waiting for joint_trajectory_controller...')
    if not client.wait_for_server(timeout_sec=10.0):
        node.get_logger().error('action server not available -- is the controller spawned?')
        return False

    goal = FollowJointTrajectory.Goal()
    goal.trajectory = trajectory
    node.get_logger().info(f'sending {label} ({len(trajectory.points)} points)')

    future = client.send_goal_async(goal)
    rclpy.spin_until_future_complete(node, future)
    handle = future.result()
    if not handle.accepted:
        node.get_logger().error('goal rejected by controller')
        return False

    result_future = handle.get_result_async()
    rclpy.spin_until_future_complete(node, result_future)
    result = result_future.result().result
    if result.error_code == FollowJointTrajectory.Result.SUCCESSFUL:
        node.get_logger().info(f'{label} complete')
        return True

    node.get_logger().error(
        f'{label} failed: {result.error_code} {result.error_string}')
    return False
