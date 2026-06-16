"""
Launch 파일 — lost_item_detector 패키지.

경로 설정은 config/params.yaml 파일을 수정하세요.

실제 RealSense 버전:
  ros2 launch lost_item_detector detector.launch.py

Mock 이미지 버전:
  ros2 launch lost_item_detector detector.launch.py use_mock:=true
"""

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

PARAMS_FILE = os.path.join(
    get_package_share_directory('lost_item_detector'),
    'config', 'params.yaml',
)


def generate_launch_description():
    use_mock = LaunchConfiguration('use_mock', default='false')

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_mock',
            default_value='false',
            description='true=이미지 파일 Mock, false=RealSense 실제',
        ),

        # RealSense 실제 버전
        Node(
            package='lost_item_detector',
            executable='detector_node',
            name='lost_item_detector',
            parameters=[PARAMS_FILE],
            additional_env={'GMS_KEY': os.environ.get('GMS_KEY', '')},
            output='screen',
            condition=UnlessCondition(use_mock),
        ),

        # Mock 이미지 버전
        Node(
            package='lost_item_detector',
            executable='detector_node_mock',
            name='lost_item_detector_mock',
            parameters=[PARAMS_FILE],
            additional_env={'GMS_KEY': os.environ.get('GMS_KEY', '')},
            output='screen',
            condition=IfCondition(use_mock),
        ),
    ])
