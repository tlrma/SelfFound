import sys
import os
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from action_msgs.msg import GoalStatus
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from std_msgs.msg import Float64MultiArray, String  # ✅ String 타입 추가
from dobot_msgs.action import PointToPoint
from dobot_msgs.srv import SuctionCupControl
from pymodbus.client.sync import ModbusTcpClient
import time

MODBUS_HOST = os.environ.get('MODBUS_HOST', 'localhost')
MODBUS_PORT = int(os.environ.get('MODBUS_PORT', 5020))
REG_DOBOT_BUSY = 2


class DobotTaskManager(Node):
    def __init__(self):
        super().__init__('dobot_task_manager')

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

        # 4. Status Publisher (작업 완료 상태 발행용)
        self.status_publisher = self.create_publisher(
            String, '/dobot_status', 10, callback_group=self.cb_group)

        self.req = SuctionCupControl.Request()
        self.modbus = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
        self.modbus.connect()

        self.tasks_list = []
        self.goal_num = 0
        self.is_working = False
        self.home_pose = [200.0, 0.0, 100.0, 0.0]
        
        # 터틀봇 고정 좌표
        self.turtle_xyz = [228.862, -46.082, -101.127]
        self.current_task_type = ""
        self._set_dobot_busy(False)

    def target_callback(self, msg):
        if self.is_working:
            self.get_logger().warn("현재 작업 중입니다. 새 명령을 무시합니다.")
            return

        self.is_working = True
        self._set_dobot_busy(True)
        coords = msg.data
        if len(coords) < 6:
            self.get_logger().error(f'Invalid target coordinates length: {len(coords)}')
            self._finish_task()
            return

        # 9단계 좌표 계산 (Z축 100.0)
        t1 = [coords[0], coords[1], coords[2], 0.0]
        t1_via = [coords[0], coords[1], 100.0, 0.0]
        t2 = [coords[3], coords[4], coords[5], 0.0]
        t2_via = [coords[3], coords[4], 100.0, 0.0]

        # --- 작업 목적(Pickup or Return) 판별 로직 ---
        # float 정밀도 오차를 감안하여 좌표 차이가 1.0mm 미만인지 확인
        def is_turtlebot(target, turtle):
            return all(abs(t - tr) < 1.0 for t, tr in zip(target[:3], turtle))

        if is_turtlebot(t1, self.turtle_xyz):
            self.current_task_type = "return"  # 터틀봇 -> 창고
        elif is_turtlebot(t2, self.turtle_xyz):
            self.current_task_type = "pickup"  # 창고 -> 터틀봇
        else:
            self.current_task_type = "unknown" # 판별 불가 (또는 수동 작업)

        self.get_logger().info(f"작업 목적 판별: {self.current_task_type}")

        # 작업 리스트 생성
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

    def _set_reg(self, address, value):
        try:
            self.modbus.write_register(address, value)
        except Exception as e:
            self.get_logger().warn(f'Modbus write failed reg[{address}]={value}: {e}')

    def _set_dobot_busy(self, is_busy):
        value = 1 if is_busy else 0
        self._set_reg(REG_DOBOT_BUSY, value)
        self.get_logger().info(f'Modbus reg[{REG_DOBOT_BUSY}] = {value} (Dobot busy)')

    def _finish_task(self):
        self.is_working = False
        self._set_dobot_busy(False)

    def execute(self):
        if self.goal_num > len(self.tasks_list) - 1:
            self.get_logger().info("모든 작업이 완료되었습니다.")
            
            # ✅ 작업 완료 토픽 발행
            if self.current_task_type in ["pickup", "return"]:
                status_msg = String()
                status_msg.data = f"done:{self.current_task_type}"
                self.status_publisher.publish(status_msg)
                self.get_logger().info(f"상태 토픽 발행 완료: {status_msg.data}")

            self._finish_task()
            return

        current_task = self.tasks_list[self.goal_num]
        self.get_logger().info(f'*** TASK NUM ***: {self.goal_num} -> {current_task}')

        if current_task[0] == "suction":
            self.send_suction_request(current_task[1])
            self.timer = self.create_timer(0.5, self.timer_callback, callback_group=self.cb_group)
            self.goal_num += 1
            
        elif current_task[0] == "move":
            self.send_goal(current_task[1], current_task[2])
            self.goal_num += 1

    def timer_callback(self):
        if self.srv_future.done():
            try:
                result = self.srv_future.result()
            except Exception as e:
                self.get_logger().error(f'Suction call failed: {e}')
                self.timer.cancel()
                self._finish_task()
                return

            self.get_logger().info(f'Suction call result: {result}')
            self.timer.cancel()
            self.execute()

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
        try:
            goal_handle = future.result()
        except Exception as e:
            self.get_logger().error(f'Goal request failed: {e}')
            self._finish_task()
            return

        if not goal_handle.accepted:
            self.get_logger().error('Goal rejected :(')
            self._finish_task()
            return

        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        try:
            status = future.result().status
        except Exception as e:
            self.get_logger().error(f'Goal result failed: {e}')
            self._finish_task()
            return

        if status == GoalStatus.STATUS_SUCCEEDED:
            self.execute()
        else:
            self.get_logger().error(f'Goal failed with status: {status}')
            self._finish_task()

    def feedback_callback(self, feedback_msg):
        pass

    def destroy_node(self):
        self._set_dobot_busy(False)
        try:
            self.modbus.close()
        except Exception as e:
            self.get_logger().warn(f'Modbus close failed: {e}')
        return super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = DobotTaskManager()
    
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
