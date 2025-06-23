from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, GroupAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node, ComposableNodeContainer
from launch_ros.descriptions import ComposableNode
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # Declare all launch arguments
    declared_arguments = [
        DeclareLaunchArgument("launch_lidar", default_value="true", description="Launch LiDAR"),
        DeclareLaunchArgument("launch_tracking_cam", default_value="false", description="Launch Tracking Camera"),
        DeclareLaunchArgument("launch_depth_cam", default_value="false", description="Launch Depth Camera"),
        # FIXME: launch_imu_interface needs rosserial_python, but it does not exist in ros2, need to find another option
        DeclareLaunchArgument("launch_imu_interface", default_value="false", description="Launch IMU Interface"),
        DeclareLaunchArgument("launch_rgb_cam", default_value="false", description="Launch RGB Camera"),
        DeclareLaunchArgument("launch_powerstatus", default_value="false", description="Launch Power Status"),
        DeclareLaunchArgument("tracking_cam_calib_odom_file", default_value="$(find smb)/config/tracking_camera_config.json", description="Path to config for odometry input to tracking camera"),
        DeclareLaunchArgument("smb_name", default_value="$(env SMB_NAME)", description="Name of the SMB in the format smb26x (relevant for calibrations)"),
        DeclareLaunchArgument("GPU_user", default_value="$(env USER)", description="Username to use on the Jetson Xavier GPU"),
    ]

    # Robosense LiDAR
    rslidar_config_file = get_package_share_directory('smb_bringup') + '/config/rslidar_config.yaml'
    lidar_group = GroupAction([
        Node(
            package="rslidar_sdk",
            executable="rslidar_sdk_node",
            name="rslidar_sdk_node",
            output="screen",
            parameters=[{'config_path': rslidar_config_file}]
        )
    ], condition=IfCondition(LaunchConfiguration("launch_lidar")))

    # # Intel RealSense Tracking Camera T265
    # tracking_camera_group = GroupAction([
    #     Node(
    #         package="realsense2_camera",
    #         executable="realsense2_camera_node",
    #         namespace="tracking_camera",
    #         parameters=[{
    #             "tracking_module.enable_mapping": False,
    #             "tracking_module.enable_pose_jumping": False,
    #             "tracking_module.enable_relocalization": False,
    #             "device_type": "t265",
    #             "enable_pose": True,
    #             "enable_accel": True,
    #             "enable_gyro": True,
    #             "publish_tf": False,
    #             "publish_odom_tf": False,
    #             "topic_odom_in": "/control/smb_diff_drive/odom",
    #             "unite_imu_method": "linear_interpolation",
    #             "calib_odom_file": LaunchConfiguration("tracking_cam_calib_odom_file"),
    #         }],
    #         output="screen",
    #     )
    # ], condition=IfCondition(LaunchConfiguration("launch_tracking_cam")))

    # # Intel RealSense Depth Camera D435
    # depth_camera_group = GroupAction([
    #     IncludeLaunchDescription(
    #         PythonLaunchDescriptionSource(
    #             PathJoinSubstitution([
    #                 FindPackageShare("realsense2_camera"), "launch", "rs_launch.py"
    #             ])
    #         ),
    #         launch_arguments={"camera": "depth_camera", "device_type": "d435"}.items(),
    #     )
    # ], condition=IfCondition(LaunchConfiguration("launch_depth_cam")))

    # # IMU Interface
    # imu_interface_group = GroupAction([
    #     Node(
    #         # FIXME:rosserial does not exist in ros2, need to find another option
    #         package="rosserial_python",
    #         executable="serial_node",
    #         name="rosserial_python",
    #         parameters=[{"_port": "/dev/versavis", "_baud": 250000}],
    #         output="screen",
    #         respawn=True,
    #     ),
    #     Node(
    #         package="versavis_adis16448_receiver",
    #         executable="versavis_imu_receiver",
    #         name="versavis_imu_receiver",
    #         parameters=[{
    #             "imu_accelerator_sensitivity": 0.000833,
    #             "imu_gyro_sensitivity": 0.04,
    #             "imu_acceleration_covariance": 0.043864908,
    #             "imu_gyro_covariance": 6e-9,
    #             "imu_sub_topic": "/versavis/imu_micro",
    #             "imu_pub_topic": "/imu",
    #         }],
    #         output="screen",
    #     ),
    # ], condition=IfCondition(LaunchConfiguration("launch_imu_interface")))

    # RGB Camera (FLIR Driver)
    # rgb_camera_group = GroupAction([
    #     ComposableNodeContainer(
    #         name="camera_container",
    #         namespace="rgb_camera",
    #         package="rclcpp_components",
    #         executable="component_container",
    #         composable_node_descriptions=[
    #             ComposableNode(
    #                 package="spinnaker_camera_driver",
    #                 plugin="spinnaker_camera_driver::CameraDriver",
    #                 name="rgb_camera_node",
    #                 parameters=[{
    #                     "frame_id": "rgb_camera_optical_link",
    #                     "serial_number": "0",
    #                     "parameter_file": "/smb_ros2_workspace/src/core/smb_bringup/config/smb261.cam0.yaml",
    #                     "acquisition_frame_rate": 4,
    #                     "acquisition_frame_rate_enable": True,
    #                     "image_format_color_coding": "BayerRG8",
    #                     "color_processing_algorithm": "HQ_LINEAR",
    #                     # "camerainfo_url": "file:///smb_ros2_workspace/src/core/smb_bringup/config/smb261.cam0.yaml",
    #                     "acquisition_mode": "Continuous",
    #                     "enable_trigger": "Off",
    #                     "exposure_mode": "Timed",
    #                     "exposure_auto": "Continuous",
    #                     "auto_exposure_time_upper_limit": 5000,
    #                     "auto_exposure_time_lower_limit": 300,
    #                     "auto_gain": "Continuous",
    #                     "auto_white_balance": "Continuous",
    #                 }],
    #             ),
    #             ComposableNode(
    #                 package="image_proc",
    #                 plugin="image_proc::DebayerNode",
    #                 name="image_proc_debayer",
    #             ),
    #         ],
    #         output="screen",
    #     )
    # ], condition=IfCondition(LaunchConfiguration("launch_rgb_cam")))
    # rgb_camera_group = GroupAction([
    #     IncludeLaunchDescription(
    #         PythonLaunchDescriptionSource(
    #             PathJoinSubstitution([
    #                 FindPackageShare("smb_bringup"), "launch", "rgb_camera_driver.launch.py"
    #             ])
    #         ),
    #         launch_arguments={
    #             'serial': "'20010195'" # for Jetson only
    #         }.items()
    #     )
    # ], condition=IfCondition(LaunchConfiguration("launch_rgb_cam")))

    # # Power Status
    # power_status_group = GroupAction([
    #     IncludeLaunchDescription(
    #         PythonLaunchDescriptionSource(
    #             PathJoinSubstitution([
    #                 FindPackageShare("smb_powerstatus"), "launch", "smb_powerstatus.launch.py"
    #             ])
    #         )
    #     )
    # ], condition=IfCondition(LaunchConfiguration("launch_powerstatus")))

        
    # Visualize in Rviz
    # rviz_config = get_package_share_directory('smb_bringup')+'/config/smb_vis.rviz'
    
    # rviz_group = GroupAction([
    #     Node(namespace='rviz2', 
    #         package='rviz2', 
    #         executable='rviz2', 
    #         arguments=['-d',rviz_config]
    #     )
    # ])


    return LaunchDescription(
        declared_arguments +
        [
            lidar_group,
            # tracking_camera_group,
            # depth_camera_group,
            # imu_interface_group,
            #rgb_camera_group,
            # power_status_group,
            #rviz_group
        ]
    )