"""Rotate the FR3 base joint in both directions within its joint limits."""

import rclpy
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionClient
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory

from fr3_wave.arm import DEFAULT_ACTION, HOME, JOINTS, LIMITS, MARGIN, clamp, point, send_trajectory

SPIN_JOINT = 'fr3v2_joint1'


class Spinner(Node):

    def __init__(self):
        super().__init__('spinner')
        self.declare_parameter('amplitude', 1.5)
        self.declare_parameter('segment_time', 2.0)
        self.declare_parameter('settle_time', 3.0)
        self.declare_parameter('trajectory_action', DEFAULT_ACTION)
        self.client = ActionClient(
            self, FollowJointTrajectory,
            self.get_parameter('trajectory_action').value)

    def build_trajectory(self):
        amplitude = float(self.get_parameter('amplitude').value)
        segment = float(self.get_parameter('segment_time').value)
        settle = float(self.get_parameter('settle_time').value)
        if amplitude <= 0 or segment <= 0 or settle <= 0:
            raise ValueError('amplitude, segment_time, and settle_time must be positive')
        if amplitude > LIMITS[SPIN_JOINT][1] - MARGIN:
            raise ValueError('amplitude exceeds the base joint travel limit')

        index = JOINTS.index(SPIN_JOINT)
        positive = list(HOME)
        negative = list(HOME)
        positive[index] = clamp(SPIN_JOINT, HOME[index] + amplitude)
        negative[index] = clamp(SPIN_JOINT, HOME[index] - amplitude)

        trajectory = JointTrajectory()
        trajectory.joint_names = JOINTS
        # This joint cannot rotate continuously; sweep each direction and return home.
        trajectory.points = [
            point(HOME, settle),
            point(positive, settle + segment),
            point(negative, settle + 3 * segment),
            point(HOME, settle + 4 * segment),
        ]
        return trajectory

    def send(self):
        return send_trajectory(self, self.client, self.build_trajectory(), 'base spin')


def main(args=None):
    rclpy.init(args=args)
    node = Spinner()
    success = False
    try:
        success = node.send()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
    raise SystemExit(0 if success else 1)


if __name__ == '__main__':
    main()
