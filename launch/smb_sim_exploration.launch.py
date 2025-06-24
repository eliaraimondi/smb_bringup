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

    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare("smb_gazebo"),
                "launch",
                "gazebo.launch.py"
            ])
        )
    )
    
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
    low_level_controller = Node(
        package="smb_low_level_controller_gazebo",
        executable="smb_low_level_controller_gazebo_node",
        name="smb_low_level_controller_gazebo_node",
        output="screen",
        parameters=[{"use_sim_time": use_sim_time}],
    )

    gmsf_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare("smb_estimator_graph_ros2"),
                "launch",
                "smb_estimator_graph_sim.launch.py"
            ])
        ),
    )

    open3d_slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare("open3d_slam_ros"),
                "launch",
                "summer_school_slam_robot_launch.py"
            ])
        ),
        launch_arguments={
            "use_sim_time": "true"
        }.items(),
    )

    terrain_analysis_launch = IncludeLaunchDescription(
        FrontendLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare("terrain_analysis"),
                "launch",
                "terrain_analysis.launch"
            ])
        ]),
        launch_arguments={
            "use_sim_time": use_sim_time
        }.items(),
    )

    terrain_analysis_ext_launch = IncludeLaunchDescription(
        FrontendLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare("terrain_analysis_ext"),
                "launch",
                "terrain_analysis_ext.launch"
            ])
        ]),
        launch_arguments={
            "use_sim_time": use_sim_time
        }.items(),
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
        FrontendLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare("local_planner"),
                "launch",
                "local_planner.launch"
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

    smb_ui = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare("smb_ui"),
                "launch",
                "smb_ui_sim.launch.py"
            ])
        ),
    )
    
    return LaunchDescription([
        *launch_args,
        gazebo_launch,
        kinematics_controller,
        low_level_controller,
        terrain_analysis_launch,
        terrain_analysis_ext_launch,
        dlio_launch,
        gmsf_launch,
        open3d_slam_launch,
        relay_odom_to_dlio,
        local_odometry,
        static_tf_map_to_odom,
        exploration_launch,
        local_planner_launch,
        twist_pid,
        twist_mux,
        rviz2,
        smb_ui
    ])