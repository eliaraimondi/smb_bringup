import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, GroupAction, LogInfo
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node, ComposableNodeContainer
from launch_ros.descriptions import ComposableNode
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    robot_id = os.environ.get('ROBOT_ID', '000')  # default to '000' if not set

    # Mapping of robot_id to serial numbers
    serial_map = {
        '261': '20010195',
        '262': '20023239',
        '263': '20010198',
        '264': '20023237',
    }

    # Handle missing or unrecognized robot_id
    if robot_id == '000':
        return LaunchDescription([
            LogInfo(msg="Environment variable ROBOT_ID is not set or is default '000', exiting...")
        ])

    serial_ = serial_map.get(robot_id)
    if serial_ is None:
        return LaunchDescription([
            LogInfo(msg=f"ROBOT_ID '{robot_id}' not recognized. No serial configured.")
        ])

    # Define the RGB camera group using the serial from the environment
    rgb_camera_group = GroupAction([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare("smb_bringup"), "launch", "rgb_camera_driver.launch.py"
                ])
            ),
            launch_arguments={
                'serial': f"'{serial_}'"
            }.items()
        )
    ])

    # Define the image processing container
    container = ComposableNodeContainer(
        name='image_proc_container',
        namespace='rgb_camera',
        package='rclcpp_components',
        executable='component_container',
        composable_node_descriptions=[
            ComposableNode(
                package='image_proc',
                plugin='image_proc::DebayerNode',
                name='debayer_node',
                remappings=[
                    ('image_raw', 'rgb_camera/image_raw'),
                    ('image_color', 'rgb_camera/image_debayered')
                ]
            )
        ],
        output='screen',
        parameters=[
            {"use_sim_time": False},
        ],
    )

    return LaunchDescription([
        LogInfo(msg=f"Launching with ROBOT_ID: {robot_id} and serial: {serial_}"),
        rgb_camera_group,
        container
    ])
