import math

import rclpy
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionClient
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory

from fr3_wave.arm import DEFAULT_ACTION, HOME, JOINTS, LIMITS, clamp, point, send_trajectory


class Waver(Node):

    def __init__(self):
        super().__init__('waver')
        self.declare_parameter('wave_joint', 'fr3v2_joint5')
        self.declare_parameter('amplitude', 0.6)
        self.declare_parameter('cycles', 4)
        self.declare_parameter('period', 1.5)
        self.declare_parameter('settle_time', 3.0)
        self.declare_parameter('trajectory_action', DEFAULT_ACTION)

        self.client = ActionClient(
            self, FollowJointTrajectory,
            self.get_parameter('trajectory_action').value)

    def build_trajectory(self):
        joint = self.get_parameter('wave_joint').value
        amplitude = self.get_parameter('amplitude').value
        cycles = self.get_parameter('cycles').value
        period = self.get_parameter('period').value
        settle = self.get_parameter('settle_time').value

        if joint not in LIMITS:
            raise ValueError(f'unknown joint {joint}; expected one of {JOINTS}')

        index = JOINTS.index(joint)
        centre = HOME[index]

        traj = JointTrajectory()
        traj.joint_names = JOINTS

        # Settle at home first so the wave starts from a known pose.
        traj.points.append(point(HOME, settle))

        t = settle
        steps_per_cycle = 4
        for step in range(cycles * steps_per_cycle + 1):
            phase = 2.0 * math.pi * step / steps_per_cycle
            positions = list(HOME)
            positions[index] = clamp(joint, centre + amplitude * math.sin(phase))
            t += period / steps_per_cycle
            traj.points.append(point(positions, t))

        traj.points.append(point(HOME, t + settle))
        return traj

    def send(self):
        return send_trajectory(
            self, self.client, self.build_trajectory(),
            f'wave on {self.get_parameter("wave_joint").value}')


def main(args=None):
    rclpy.init(args=args)
    node = Waver()
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
