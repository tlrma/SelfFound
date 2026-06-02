import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped
import yaml
import os
import math
from ament_index_python.packages import get_package_share_directory

class NamedPoseNavigator(Node):
    def __init__(self):
        super().__init__('named_pose_navigator')
        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        # named_poses.yaml 로드
        config_path = os.path.join(
            get_package_share_directory('turtlebot_manager'),
            'config',
            'named_poses.yaml'
        )
        with open(config_path, 'r') as f:
            self.named_poses = yaml.safe_load(f)['named_poses']

        self.get_logger().info(f'로드된 named poses: {list(self.named_poses.keys())}')

    def navigate_to(self, pose_name):
        if pose_name not in self.named_poses:
            self.get_logger().error(f'알 수 없는 pose: {pose_name}')
            return

        pose_data = self.named_poses[pose_name]
        self.get_logger().info(f'{pose_name} 으로 이동 시작!')

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = PoseStamped()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = pose_data['x']
        goal_msg.pose.pose.position.y = pose_data['y']

        # yaw → quaternion 변환
        yaw = pose_data['yaw']
        goal_msg.pose.pose.orientation.z = math.sin(yaw / 2)
        goal_msg.pose.pose.orientation.w = math.cos(yaw / 2)

        self._action_client.wait_for_server()
        self._send_goal_future = self._action_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        )
        self._send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info('목표 거부됨!')
            return
        self.get_logger().info('목표 수락됨!')
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        self.get_logger().info('목표 도착 완료!')

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        self.get_logger().info(
            f'남은 거리: {feedback.distance_remaining:.2f}m'
        )

def main(args=None):
    rclpy.init(args=args)
    navigator = NamedPoseNavigator()

    # 테스트할 pose 이름 입력
    import sys
    pose_name = sys.argv[1] if len(sys.argv) > 1 else 'waiting'
    navigator.navigate_to(pose_name)

    rclpy.spin(navigator)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
