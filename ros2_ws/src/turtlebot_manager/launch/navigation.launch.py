import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_dir = get_package_share_directory('turtlebot_manager')
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')
    turtlebot3_gazebo = get_package_share_directory('turtlebot3_gazebo')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    world = os.path.join(pkg_dir, 'worlds', 'lost_and_found.world')
    map_file = os.path.join(pkg_dir, 'maps', 'pjt_map.yaml')

    gzserver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gzserver.launch.py')
        ),
        launch_arguments={'world': world}.items()
    )

    gzclient = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gzclient.launch.py')
        )
    )

    robot_state_publisher = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(turtlebot3_gazebo, 'launch', 'robot_state_publisher.launch.py')
        ),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )

    spawn_turtlebot = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(turtlebot3_gazebo, 'launch', 'spawn_turtlebot3.launch.py')
        ),
        launch_arguments={
            'x_pose': '-1.5',
            'y_pose': '-1.0'
        }.items()
    )

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('turtlebot3_navigation2'),
                'launch',
                'navigation2.launch.py'
            )
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'map': map_file,
            'params_file': os.path.join(
                get_package_share_directory('turtlebot3_navigation2'),
                'param',
                'waffle_pi.yaml'
            )
        }.items()
    )

    rviz2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('nav2_bringup'),
                'launch',
                'rviz_launch.py'
            )
        )
    )

    navigation_server = Node(
        package='turtlebot_manager',
        executable='navigation_server',
        name='navigation_server',
        output='screen',
    )

    return LaunchDescription([
        gzserver,
        gzclient,
        robot_state_publisher,
        spawn_turtlebot,
        TimerAction(period=5.0, actions=[nav2]),
        TimerAction(period=8.0, actions=[navigation_server]),
        #TimerAction(period=7.0, actions=[rviz2]),
    ])