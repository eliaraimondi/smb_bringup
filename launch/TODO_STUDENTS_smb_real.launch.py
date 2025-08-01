from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource, FrontendLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import PythonExpression
from ament_index_python.packages import get_package_share_directory
from launch.conditions import UnlessCondition, IfCondition
import os



def generate_launch_description():
    default_config_topics = os.path.join(get_package_share_directory('smb_bringup'), 'config', 'twist_mux_topics.yaml')
    launch_args = [
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation (Gazebo) clock if true'
        ),
        DeclareLaunchArgument(
            'use_ground_truth',
            default_value='true',
            description='Use ground truth odometry (true/false). If false, launches DLIO.'
        ),
        DeclareLaunchArgument(
            'config_topics',
            default_value=default_config_topics,
            description='Default topics config file'
        ),
    ]

    use_sim_time = LaunchConfiguration('use_sim_time')
    use_ground_truth = LaunchConfiguration('use_ground_truth')
    
    static_tf_map_to_odom = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="static_map_to_odom",
        arguments=["0", "0", "0", "0", "0", "0", "map", "odom"],
        output="log",
    )

    # Kinematics controller node
    kinematics_controller = Node(
        package="smb_kinematics",
        executable="smb_kinematics_node",
        name="smb_kinematics_node",
        output="screen",
        parameters=[{"use_sim_time": use_sim_time}],
    )

    # Low-level gazebo controller node
    # low_level_controller = Node(
    #     package="smb_low_level_controller",
    #     executable="smb_low_level_controller_gazebo_node",
    #     name="smb_low_level_controller_gazebo_node",
    #     output="screen",
    #     parameters=[{"use_sim_time": use_sim_time}],
    # )

    low_level_controller = Node(
        package="smb_low_level_controller",
        executable="speed_control_node",
        name="speed_control_node",
        output="screen",
        # parameters=[
        #         {"port": "/dev/ttyUSB0"},
        #         {"baudrate": 115200},
        #         {"motor_1_channel": 1},
        #         {"motor_2_channel": 2},
        #         {"send_cmd": 1},
        #         {"rc_channel_1": rc_channel_1},
        #         {"rc_channel_2": rc_channel_2},
        #         {"use_sim_time": False},
        #     ],
    )

    terrain_analysis = Node(
        package="terrain_analysis",
        executable="terrainAnalysis",
        name="terrainAnalysis",
        output="screen",
        parameters=[{"use_sim_time": use_sim_time}],
    )

    terrain_analysis_ext = Node(
        package="terrain_analysis_ext",
        executable="terrainAnalysisExt",
        name="terrainAnalysisExt",
        output="screen",
        parameters=[{"use_sim_time": use_sim_time}],
    )

    dlio_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare("direct_lidar_inertial_odometry"),
                "launch",
                "dlio.launch.py"
            ])
        ]),
        launch_arguments={
            "rviz": "false",
            "pointcloud_topic": "/rslidar/points",
            "imu_topic": "/imu/data_raw",
            "odom_topic": "/state_estimation",
            "registered_pointcloud_topic": "/registered_scan",
        }.items(),
        condition=UnlessCondition(use_ground_truth),
    )
    
    relay_odom_to_dlio = Node(
        package="topic_tools",
        executable="relay",
        name="relay_odom_to_dlio",
        arguments=["/odom", "/state_estimation"],
        output="screen",
        condition=IfCondition(use_ground_truth)
    )

    local_odometry = Node(
        package="smb_kinematics",
        executable="smb_global_to_local_odometry",
        name="smb_global_to_local_odometry",
        output="screen",
        parameters=[
            {"use_sim_time": use_sim_time},
            {"use_ground_truth": use_ground_truth}
        ],
    )
    
    exploration_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [get_package_share_directory('tare_planner'), '/explore_robotx.launch']),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "rviz": "true",
        }.items(),
    )
    
    local_planner_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare("local_planner"),
                "launch",
                "local_planner.launch.py"
            ])
        ]),
        launch_arguments={
            "use_sim_time": use_sim_time
        }.items(),
    )
    
    twist_pid = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare("twist_pid_controller"),
                "launch",
                "twist_pid_controller.launch.py"
            ])
        ),
    )
    
    rviz2 = Node(
        package='rviz2',
        executable='rviz2',
        name='far_rviz',
        arguments=[
            '-d',
            PathJoinSubstitution([
                get_package_share_directory('smb_bringup'),
                'rviz',
                'debug.rviz'
            ])
        ],
        respawn=False,
    )

    twist_mux = Node(
        package='twist_mux',
        executable='twist_mux',
        output='screen',
        remappings={('/cmd_vel_out', '/cmd_vel')},
        parameters=[
            {'use_sim_time': use_sim_time},
            LaunchConfiguration('config_topics')]
    )
    
    return LaunchDescription([
        *launch_args,
        gazebo_launch,
        kinematics_controller,
        low_level_controller,
        terrain_analysis,
        terrain_analysis_ext,
        dlio_launch,
        relay_odom_to_dlio,
        local_odometry,
        static_tf_map_to_odom,
        exploration_launch,
        local_planner_launch,
        twist_pid,
        twist_mux,
        rviz2,
    ])