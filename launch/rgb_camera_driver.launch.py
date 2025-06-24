# -----------------------------------------------------------------------------
# Copyright 2022 Bernd Pfrommer <bernd.pfrommer@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument as LaunchArg
from launch.actions import OpaqueFunction
from launch.substitutions import LaunchConfiguration as LaunchConfig
from launch.substitutions import PathJoinSubstitution, PythonExpression
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

import os

blackfly_s_param = {
    'debug': False,
    'compute_brightness': False,
    'adjust_timestamp': True,
    'dump_node_map': False,
    # set parameters defined in blackfly_s.yaml
    'gain_auto': 'Continuous',
    # 'pixel_format': 'BayerRG8',
    'pixel_format': 'RGB8',
    'exposure_auto': 'Continuous',
    # to use a user set, do this:
    # 'user_set_selector': 'UserSet0',
    # 'user_set_load': 'Yes',
    # These are useful for GigE cameras
    # 'device_link_throughput_limit': 380000000,
    # 'gev_scps_packet_size': 9000,
    # ---- to reduce the sensor width and shift the crop
    # 'image_width': 1408,
    # 'image_height': 1080,
    # 'offset_x': 16,
    # 'offset_y': 0,
    # 'binning_x': 1,
    # 'binning_y': 1,
    # 'connect_while_subscribed': True,
    'frame_rate_auto': 'Off',
    'frame_rate': 5.0,
    'frame_rate_enable': True,
    'buffer_queue_size': 10,
    'trigger_mode': 'Off',
    'chunk_mode_active': True,
    'chunk_selector_frame_id': 'FrameID',
    'chunk_enable_frame_id': True,
    'chunk_selector_exposure_time': 'ExposureTime',
    'chunk_enable_exposure_time': True,
    'chunk_selector_gain': 'Gain',
    'chunk_enable_gain': True,
    'chunk_selector_timestamp': 'Timestamp',
    'chunk_enable_timestamp': True,
}

def launch_setup(context, *args, **kwargs):
    """Launch camera driver node."""
    parameter_file = LaunchConfig('parameter_file').perform(context)
    camera_type = LaunchConfig('camera_type').perform(context)
    robot_id = os.environ.get('ROBOT_ID', 'sim')
    calibration_file = PathJoinSubstitution(
        [FindPackageShare('smb_bringup'), 'config', 'smb' + robot_id + '_cam0.yaml']
    )
    
    calibration_file_url = 'file://' + calibration_file.perform(context)
    
    if not parameter_file:
        parameter_file = PathJoinSubstitution(
            [FindPackageShare('spinnaker_camera_driver'), 'config', camera_type + '.yaml']
        )
    node = Node(
        package='spinnaker_camera_driver',
        executable='camera_driver_node',
        output='screen',
        name=[LaunchConfig('camera_name')],
        parameters=[
            blackfly_s_param,
            {
                'ffmpeg_image_transport.encoding': 'hevc_nvenc',
                'parameter_file': parameter_file,
                'serial_number': [LaunchConfig('serial')],
                'camerainfo_url': calibration_file_url,
            },
        ],
        remappings=[
            ('~/control', '/exposure_control/control'),
        ],
    )

    return [node]


def generate_launch_description():
    """Create composable node by calling opaque function."""
    return LaunchDescription(
        [
            LaunchArg(
                'camera_name',
                default_value=['rgb_camera'],
                description='camera name (ros node name)',
            ),
            LaunchArg(
                'camera_type',
                default_value='blackfly_s',
                description='type of camera (blackfly_s, chameleon...)',
            ),
            LaunchArg(
                'serial',
                default_value="'20010195'",
                description='FLIR serial number of camera (in quotes!!)',
            ),
            LaunchArg(
                'parameter_file',
                default_value='',
                description='path to ros parameter definition file (override camera type)',
            ),
            OpaqueFunction(function=launch_setup),
        ]
    )
