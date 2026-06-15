"""
Launch 파일 — lost_item_detector 패키지.

실제 RealSense 버전:
  ros2 launch lost_item_detector detector.launch.py

Mock 이미지 버전:
  ros2 launch lost_item_detector detector.launch.py \
    use_mock:=true image_path:=/path/to/test.jpg
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_mock = LaunchConfiguration('use_mock', default='false')
    image_path = LaunchConfiguration('image_path', default='')
    backend_url = LaunchConfiguration('backend_url', default='http://localhost:8000/api/items/')
    model_path = LaunchConfiguration(
        'model_path',
        default='/home/ssafy/finalPJT/SelfFound/vision/best.pt',
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_mock', default_value='false',
                              description='true=이미지 파일 Mock, false=RealSense 실제'),
        DeclareLaunchArgument('image_path', default_value='',
                              description='Mock 버전에서 사용할 테스트 이미지 경로'),
        DeclareLaunchArgument('backend_url', default_value='http://localhost:8000/api/items/'),
        DeclareLaunchArgument('model_path',
                              default_value='/home/ssafy/finalPJT/SelfFound/vision/best.pt'),

        # RealSense 실제 버전
        Node(
            package='lost_item_detector',
            executable='detector_node',
            name='lost_item_detector',
            parameters=[{
                'backend_url': backend_url,
                'model_path': model_path,
            }],
            output='screen',
            condition=UnlessCondition(use_mock),
        ),

        # Mock 이미지 버전
        Node(
            package='lost_item_detector',
            executable='detector_node_mock',
            name='lost_item_detector_mock',
            parameters=[{
                'backend_url': backend_url,
                'model_path': model_path,
                'image_path': image_path,
            }],
            output='screen',
            condition=IfCondition(use_mock),
        ),
    ])
