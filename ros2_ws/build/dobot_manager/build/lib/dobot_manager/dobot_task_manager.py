import sys
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from action_msgs.msg import GoalStatus
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from std_msgs.msg import Float64MultiArray
from dobot_msgs.action import PointToPoint
from dobot_msgs.srv import SuctionCupControl
import time

class DobotTaskManager(Node):
    def __init__(self):
        super().__init__('dobot_task_manager')

        # 통신이 막히지 않도록(Deadlock 방지) 도와주는 콜백 그룹
        self.cb_group = ReentrantCallbackGroup()

        # 1. Django Subscriber
        self.subscription = self.create_subscription(
            Float64MultiArray, '/dobot_task_targets', self.target_callback, 10, callback_group=self.cb_group)

        # 2. Action Client (이동)
        self._action_client = ActionClient(
            self, PointToPoint, '/PTP_action', callback_group=self.cb_group)

        # 3. Service Client (흡착)
        self.suction_client = self.create_client(
            SuctionCupControl, '/dobot_suction_cup_service', callback_group=self.cb_group)

        while not self.suction_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Suction service not available, waiting again...')

        self.req = SuctionCupControl.Request()

        self.tasks_list = []
        self.goal_num = 0
        self.is_working = False
        self.home_pose = [200.0, 0.0, 100.0, 0.0]

    def target_callback(self, msg):
        if self.is_working:
            self.get_logger().warn("현재 작업 중입니다. 새 명령을 무시합니다.")
            return

        self.is_working = True
        coords = msg.data

        # 경유지 포함 9단계 좌표 계산 (Z축 100.0)
        t1 = [coords[0], coords[1], coords[2], 0.0]
        t1_via = [coords[0], coords[1], 100.0, 0.0]
        t2 = [coords[3], coords[4], coords[5], 0.0]
        t2_via = [coords[3], coords[4], 100.0, 0.0]

        # 원본 코드 구조를 활용한 작업 리스트 생성 (모든 motion_type은 1)
        self.tasks_list = [
            ["move", t1_via, 1],
            ["move", t1, 1],
            ["suction", True],
            ["move", t1_via, 1],
            ["move", t2_via, 1],
            ["move", t2, 1],
            ["suction", False],
            ["move", t2_via, 1],
            ["move", self.home_pose, 1]
        ]

        self.goal_num = 0
        self.get_logger().info("작업 시퀀스를 시작합니다.")
        self.execute()

    def execute(self):
        if self.goal_num > len(self.tasks_list) - 1:
            self.get_logger().info("모든 작업이 완료되었습니다. 대기 모드로 전환합니다.")
            self.is_working = False
            return

        current_task = self.tasks_list[self.goal_num]
        self.get_logger().info(f'*** TASK NUM ***: {self.goal_num} -> {current_task}')

        if current_task[0] == "suction":
            self.send_suction_request(current_task[1])
            # 서비스 호출 완료를 대기하기 위한 타이머
            self.timer = self.create_timer(0.5, self.timer_callback, callback_group=self.cb_group)
            self.goal_num += 1
            
        elif current_task[0] == "move":
            self.send_goal(current_task[1], current_task[2])
            self.goal_num += 1

    def timer_callback(self):
        if self.srv_future.done():
            result = self.srv_future.result()
            self.get_logger().info(f'Suction call result: {result}')
            self.timer.cancel()
            self.execute() # 다음 작업 실행

    def send_suction_request(self, enable):
        self.req.enable_suction = enable
        self.srv_future = self.suction_client.call_async(self.req)

    def send_goal(self, _target, _type):
        goal_msg = PointToPoint.Goal()
        goal_msg.target_pose = _target
        goal_msg.motion_type = _type

        self._action_client.wait_for_server()
        self._send_goal_future = self._action_client.send_goal_async(
            goal_msg, feedback_callback=self.feedback_callback)
        self._send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Goal rejected :(')
            return

        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        status = future.result().status
        if status == GoalStatus.STATUS_SUCCEEDED:
            self.execute() # 이동 성공 시 다음 작업 실행

    def feedback_callback(self, feedback_msg):
        pass # 로그 도배 방지


def main(args=None):
    rclpy.init(args=args)
    node = DobotTaskManager()
    
    # 통신 병목을 막아주는 멀티스레드 실행기
    executor = MultiThreadedExecutor()
    try:
        rclpy.spin(node, executor=executor)
    except KeyboardInterrupt:
        node.get_logger().info("노드를 종료합니다.")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()