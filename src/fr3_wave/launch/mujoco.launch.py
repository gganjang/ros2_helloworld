"""Start one shared FR3 MuJoCo ros2_control server, without application clients."""

import os
import xml.etree.ElementTree as ET

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, OpaqueFunction, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


DEFAULT_SCENE = os.environ.get(
    'FR3_MUJOCO_SCENE',
    os.path.join(
        os.path.expanduser('~'), 'workspace', 'ros2_helloworld',
        'assets', 'models', 'franka_fr3_v2', 'scene.xml'))


def start_simulator(context):
    share = get_package_share_directory('fr3_wave')
    urdf = os.path.join(share, 'urdf', 'fr3v2.urdf')
    controllers = os.path.join(share, 'config', 'controllers.yaml')
    scene = LaunchConfiguration('scene').perform(context)
    headless = LaunchConfiguration('headless').perform(context).lower()
    if headless not in ('true', 'false'):
        raise ValueError('headless must be true or false')
    if not os.path.isfile(scene):
        raise FileNotFoundError(f'MuJoCo scene not found: {scene}')

    # The hardware plugin reads these parameters from robot_description.
    # Populate them at launch so an installed simulator can use mounted assets.
    robot = ET.parse(urdf).getroot()
    hardware = robot.find('./ros2_control/hardware')
    if hardware is None:
        raise ValueError('ros2_control hardware declaration missing from URDF')
    for name, value in (('mujoco_model', scene), ('headless', headless)):
        param = hardware.find(f"./param[@name='{name}']")
        if param is None:
            raise ValueError(f'{name} hardware parameter missing from URDF')
        param.text = value
    robot_description = ET.tostring(robot, encoding='unicode')

    control_node = Node(
        package='mujoco_ros2_control',
        executable='ros2_control_node',
        output='screen',
        parameters=[
            {'robot_description': robot_description},
            {'mujoco_model': scene},
            {'use_sim_time': True},
            controllers,
        ],
    )

    state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description}, {'use_sim_time': True}],
    )

    spawn_broadcaster = ExecuteProcess(
        cmd=['ros2', 'run', 'controller_manager', 'spawner',
             'joint_state_broadcaster'],
        output='screen',
    )

    spawn_trajectory = ExecuteProcess(
        cmd=['ros2', 'run', 'controller_manager', 'spawner',
             'joint_trajectory_controller'],
        output='screen',
    )

    return [
        control_node,
        state_publisher,
        spawn_broadcaster,
        RegisterEventHandler(
            OnProcessExit(
                target_action=spawn_broadcaster,
                on_exit=[spawn_trajectory],
            )
        ),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'scene', default_value=DEFAULT_SCENE,
            description='Path to the MuJoCo scene XML.'),
        DeclareLaunchArgument(
            'headless', default_value='false',
            description='Run simulation without the MuJoCo viewer.'),
        OpaqueFunction(function=start_simulator),
    ])
