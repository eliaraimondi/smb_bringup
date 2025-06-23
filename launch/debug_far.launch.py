from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource, FrontendLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration, Command, FindExecutable
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue
from launch.substitutions import PythonExpression
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    
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
        parameters=[{"use_sim_time": False}],
    )

    # Path to the URDF file
    description_file = PathJoinSubstitution(
        [FindPackageShare("smb_description"), "urdf", "smb.urdf.xacro"]
    )

    # Generate the robot description using xacro
    robot_description = ParameterValue(
        Command([FindExecutable(name="xacro"), " ", description_file]),
        value_type=str
    )

    # Robot State Publisher node
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[{"robot_description": robot_description, "use_sim_time": False}],    
    )

    rslidar_config_file = get_package_share_directory('smb_bringup') + '/config/rslidar_config.yaml'
    rslidar = Node(
            package="rslidar_sdk",
            executable="rslidar_sdk_node",
            name="rslidar_sdk_node",
            output="screen",
            parameters=[{'config_path': rslidar_config_file}]
        )

    # # Low-level gazebo controller node
    # low_level_controller = Node(
    #     package="smb_low_level_controller_gazebo",
    #     executable="smb_low_level_controller_gazebo_node",
    #     name="smb_low_level_controller_gazebo_node",
    #     output="screen",
    #     parameters=[{"use_sim_time": False}],
    # )
    
    low_level_controller = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare("smb_low_level_controller"),
                "launch",
                "speed_control_node.launch.py"
            ])
        ]),
    )
    
    
    
    
    joy_to_cmd_vel = Node(
        package="smb_kinematics",
        executable="smb_cmd_vel",
        name="smb_cmd_vel",
        output="screen",
        parameters=[{"use_sim_time": False}],
    )
    
    joy = Node(
        package="joy",
        executable="joy_node",
        name="joy_node",
        output="log",
        parameters=[{"use_sim_time": False}],
    )

    # Terrain analysis node
    terrain_analysis = Node(
        package="terrain_analysis",
        executable="terrainAnalysis",
        name="terrainAnalysis",
        output="screen",
        parameters=[{"use_sim_time": False}],
    )

    # Terrain analysis ext node
    terrain_analysis_ext = Node(
        package="terrain_analysis_ext",
        executable="terrainAnalysisExt",
        name="terrainAnalysisExt",
        output="screen",
        parameters=[{"use_sim_time": False}],
    )

    # teleop_twist_joy launch include
    teleop_twist_joy_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare("teleop_twist_joy"),
                "launch",
                "teleop-launch.py"
            ])
        ]),
        launch_arguments={"publish_stamped_twist": "true"}.items(),
        # output="log",
    )

    # dlio launch include
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
            "imu_topic": "/imu/data_raw"
        }.items(),
        # output="log",
    )
    
    local_odometry = Node(
        package="smb_kinematics",
        executable="smb_global_to_local_odometry",
        name="smb_global_to_local_odometry",
        output="screen",
        parameters=[{"use_sim_time": False}],
    )
    
    far_planner_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare("far_planner"),
                "launch",
                "far_planner.launch"
            ])
        ]),
    )
    
    local_planner_launch = IncludeLaunchDescription(
        FrontendLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare("local_planner"),
                "launch",
                "local_planner.launch"
            ])
        ]),
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

    default_config_topics = os.path.join(get_package_share_directory('smb_bringup'), 'config', 'twist_mux_topics.yaml')
    
    config_topics = DeclareLaunchArgument(
            'config_topics',
            default_value=default_config_topics,
            description='Default topics config file'
    )

    twist_mux = Node(
        package='twist_mux',
        executable='twist_mux',
        output='screen',
        remappings={('/cmd_vel_out', '/cmd_vel')},
        parameters=[
            {'use_sim_time': False},
            LaunchConfiguration('config_topics')]
    )
    
    # ros2 launch open3d_slam_ros summer_school_slam_robot_launch.py

    # ros2 launch smb_estimator_graph_ros2 smb_estimator_graph.launch.py

    graph_msf_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare("smb_estimator_graph_ros2"),
                "launch",
                "smb_estimator_graph.launch.py"
            ])
        ),
    )
    
    open_slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare("open3d_slam_ros"),
                "launch",
                "summer_school_slam_robot_launch.py"
            ])
        ),
    )
        
    
    return LaunchDescription([
        # gazebo_launch,
        # robot_state_publisher_node,
        # rslidar,
        # kinematics_controller,
        # low_level_controller,
        # joy_to_cmd_vel,
        # joy,
        # terrain_analysis,
        # terrain_analysis_ext,
        # teleop_twist_joy_launch,
        # dlio_launch,
        # graph_msf_launch,
        # open_slam_launch,
        # local_odometry,
        # static_tf_map_to_odom,
        far_planner_launch,
        local_planner_launch,
        # twist_pid,
        # config_topics,
        # twist_mux,
        # rviz2,
    ])