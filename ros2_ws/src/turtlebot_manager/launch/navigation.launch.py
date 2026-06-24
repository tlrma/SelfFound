import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_dir = get_package_share_directory('turtlebot_manager')
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')
    turtlebot3_gazebo = get_package_share_directory('turtlebot3_gazebo')

    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    use_sim = LaunchConfiguration('use_sim', default='false')
    world = os.path.join(pkg_dir, 'worlds', 'lost_and_found.world')
    map_file = os.path.expanduser('~/finalPJTMap.yaml')

    gzserver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gzserver.launch.py')
        ),
        launch_arguments={'world': world}.items(),
        condition=IfCondition(use_sim),
    )

    gzclient = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gzclient.launch.py')
        ),
        condition=IfCondition(use_sim),
    )

    robot_state_publisher = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(turtlebot3_gazebo, 'launch', 'robot_state_publisher.launch.py')
        ),
        launch_arguments={'use_sim_time': use_sim_time}.items(),
        condition=IfCondition(use_sim),
    )

    spawn_turtlebot = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(turtlebot3_gazebo, 'launch', 'spawn_turtlebot3.launch.py')
        ),
        launch_arguments={
            'x_pose': '-1.5',
            'y_pose': '-1.0'
        }.items(),
        condition=IfCondition(use_sim),
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
            'params_file': os.path.join(pkg_dir, 'config', 'nav2_params.yaml'),
        }.items()
    )

    navigation_server = Node(
        package='turtlebot_manager',
        executable='navigation_server',
        name='navigation_server',
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim', default_value='false',
                              description='true=Gazebo 시뮬레이션, false=실제 로봇'),
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        gzserver,
        gzclient,
        robot_state_publisher,
        spawn_turtlebot,
        TimerAction(period=5.0, actions=[nav2]),
        TimerAction(period=8.0, actions=[navigation_server]),
    ])
