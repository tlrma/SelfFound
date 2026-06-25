"""
TurtleBot 내비게이션 서버 노드.

Django(rosbridge)에서 토픽으로 목적지 이름을 받아 Nav2로 이동 명령을 실행한다.

토픽:
  Subscribe  /turtlebot/goto_pose  (std_msgs/String)  - 이동할 pose 이름 수신
  Publish    /turtlebot/status     (std_msgs/String)  - 상태 전송 (Django에서 구독)

상태 메시지 형식:
  "moving:<pose_name>"      이동 시작
  "arrived:<pose_name>"     도착 완료
  "error:<사유>"            오류 발생
"""

import math
import os
import yaml

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String
from ament_index_python.packages import get_package_share_directory

class NavigationServer(Node):
    def __init__(self):
        super().__init__('navigation_server')

        # named_poses.yaml 로드
        config_path = os.path.join(
            get_package_share_directory('turtlebot_manager'),
            'config',
            'named_poses.yaml'
        )
        with open(config_path, 'r') as f:
            self.named_poses = yaml.safe_load(f)['named_poses']
        self.get_logger().info(f'로드된 poses: {list(self.named_poses.keys())}')

        # Nav2 액션 클라이언트
        self._nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        # Django → TurtleBot: 이동 명령 수신
        self._cmd_sub = self.create_subscription(
            String, '/turtlebot/goto_pose', self._on_goto_pose, 10
        )

        # TurtleBot → Django: 상태 전송
        self._status_pub = self.create_publisher(String, '/turtlebot/status', 10)

        self._current_pose = None
        self.get_logger().info('NavigationServer 준비 완료')

    # ── 명령 수신 ──────────────────────────────────────────────────────────────

    def _on_goto_pose(self, msg: String):
        pose_name = msg.data.strip()

        if pose_name not in self.named_poses:
            self._publish_status(f'error:unknown_pose:{pose_name}')
            self.get_logger().error(f'알 수 없는 pose: {pose_name}')
            return

        self._current_pose = pose_name
        self._publish_status(f'moving:{pose_name}')
        self.get_logger().info(f'{pose_name} 으로 이동 시작')
        self._send_nav_goal(pose_name)

    # ── Nav2 목표 전송 ─────────────────────────────────────────────────────────

    def _send_nav_goal(self, pose_name: str):
        pose_data = self.named_poses[pose_name]

        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = self.get_clock().now().to_msg()
        goal.pose.pose.position.x = pose_data['x']
        goal.pose.pose.position.y = pose_data['y']

        yaw = pose_data['yaw']
        goal.pose.pose.orientation.z = math.sin(yaw / 2)
        goal.pose.pose.orientation.w = math.cos(yaw / 2)

        self._nav_client.wait_for_server()
        send_future = self._nav_client.send_goal_async(
            goal, feedback_callback=self._on_feedback
        )
        send_future.add_done_callback(self._on_goal_response)

    def _on_goal_response(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self._publish_status(f'error:goal_rejected:{self._current_pose}')
            self.get_logger().warn('목표 거부됨')
            return
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._on_result)

    def _on_result(self, future):
        self._publish_status(f'arrived:{self._current_pose}')
        self.get_logger().info(f'{self._current_pose} 도착 완료')

    def _on_feedback(self, feedback_msg):
        dist = feedback_msg.feedback.distance_remaining
        self.get_logger().info(f'남은 거리: {dist:.2f}m')

    # ── 상태 발행 ──────────────────────────────────────────────────────────────

    def _publish_status(self, status: str):
        msg = String()
        msg.data = status
        self._status_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = NavigationServer()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
