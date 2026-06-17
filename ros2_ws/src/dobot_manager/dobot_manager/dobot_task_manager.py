import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from std_msgs.msg import Float64MultiArray
from dobot_msgs.action import PointToPoint
from dobot_msgs.srv import SuctionCupControl
import time

class DobotTaskManager(Node):
    def __init__(self):
        super().__init__('dobot_task_manager')
        
        # 1. Django 웹 서버로부터 좌표를 받는 Subscriber
        self.subscription = self.create_subscription(
            Float64MultiArray, '/dobot_task_targets', self.target_callback, 10)
            
        # 2. 로봇 이동 제어용 Action Client
        self.motion_client = ActionClient(self, PointToPoint, '/PTP_action')
        
        # 3. 흡착 컵 제어용 Service Client
        self.suction_client = self.create_client(SuctionCupControl, '/dobot_suction_cup_service')
        
        self.is_working = False
        self.target1 = []
        self.target2 = []
        self.home_pose = [200.0, 0.0, 100.0, 0.0]  # 초기 위치 좌표 (실제 환경에 맞춰 수정 필요)

    def target_callback(self, msg):
        if self.is_working:
            self.get_logger().warn("현재 작업 중입니다. 새 명령을 무시합니다.")
            return

        self.is_working = True
        coords = msg.data
        
        # 수신된 [T1_x, T1_y, T1_z, T2_x, T2_y, T2_z] 데이터를 파싱 (회전각 r은 0.0으로 고정)
        self.target1 = [coords[0], coords[1], coords[2], 0.0]
        self.target2 = [coords[3], coords[4], coords[5], 0.0]

        self.get_logger().info("작업 시퀀스를 시작합니다.")
        self.step_1_move_to_target1()

    # --- 순차 동작 (Sequence) 로직 ---

    def step_1_move_to_target1(self):
        self.get_logger().info(f"Target1 이동: {self.target1}")
        self.send_motion_goal(self.target1, self.step_2_suction_on)

    def step_2_suction_on(self, future):
        self.get_logger().info("Suction ON")
        self.send_suction_request(True, self.step_3_move_to_target2)

    def step_3_move_to_target2(self, future):
        self.get_logger().info(f"Target2 이동: {self.target2}")
        self.send_motion_goal(self.target2, self.step_4_suction_off)

    def step_4_suction_off(self, future):
        self.get_logger().info("Suction OFF")
        self.send_suction_request(False, self.step_5_move_to_home)

    def step_5_move_to_home(self, future):
        self.get_logger().info("초기 위치 복귀")
        self.send_motion_goal(self.home_pose, self.finish_task)

    def finish_task(self, future):
        self.get_logger().info("모든 작업이 완료되었습니다.")
        self.is_working = False

    # --- ROS 2 통신 유틸리티 함수 ---

    def send_motion_goal(self, pose, callback):
        self.motion_client.wait_for_server()
        goal_msg = PointToPoint.Goal()
        goal_msg.motion_type = 1  # 1: Cartesian 좌표계 기준 선형 이동
        goal_msg.target_pose = pose
        
        send_goal_future = self.motion_client.send_goal_async(goal_msg)
        
        # 목표 도달이 완료되면 전달받은 다음 단계(callback) 함수를 실행합니다.
        send_goal_future.add_done_callback(
            lambda f: f.result().get_result_async().add_done_callback(callback) 
            if f.result().accepted else self.get_logger().error("목표가 거부되었습니다.")
        )

    def send_suction_request(self, enable, callback):
        self.suction_client.wait_for_server()
        req = SuctionCupControl.Request()
        req.enable_suction = enable
        
        future = self.suction_client.call_async(req)
        # 서비스 호출이 완료되면 다음 단계 함수 실행 전 잠시 대기하여 하드웨어 안정화 보장
        future.add_done_callback(lambda f: (time.sleep(0.5), callback(f)))

def main(args=None):
    rclpy.init(args=args)
    node = DobotTaskManager()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("노드를 종료합니다.")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()