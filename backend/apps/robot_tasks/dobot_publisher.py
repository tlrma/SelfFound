import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
import time

# Django 워커(Worker)가 살아있는 동안 rclpy 초기화 및 노드/퍼블리셔를 한 번만 유지하기 위한 전역 변수
_rclpy_initialized = False
_dobot_node = None
_dobot_publisher = None

def publish_dobot_pick_and_place_task(target1_coords, target2_coords):
    """
    Dobot에게 물건을 집을 위치(Target1)와 놓을 위치(Target2)의 좌표를 전송합니다.
    """
    global _rclpy_initialized, _dobot_node, _dobot_publisher
    
    # 1. rclpy가 초기화되지 않았다면 한 번만 초기화 진행
    if not _rclpy_initialized and not rclpy.ok():
        rclpy.init()
        _rclpy_initialized = True

    # 2. 노드 및 퍼블리셔 최초 1회 생성 (단일 노드 유지)
    if _dobot_node is None:
        _dobot_node = Node('django_dobot_persistent_publisher')
        _dobot_publisher = _dobot_node.create_publisher(Float64MultiArray, '/dobot_task_targets', 10)
        
        # 최초 연결 시에만 네트워크망 형성을 위해 1초 대기
        time.sleep(1.0)
        _dobot_node.get_logger().info("퍼블리셔 노드가 최초 생성 및 연결되었습니다.")

    # 3. 전송할 메시지 구성: [T1_x, T1_y, T1_z, T2_x, T2_y, T2_z]
    msg = Float64MultiArray()
    try:
        msg.data = [
            float(target1_coords['x']), float(target1_coords['y']), float(target1_coords['z']),
            float(target2_coords['x']), float(target2_coords['y']), float(target2_coords['z'])
        ]
        
        # 4. 메시지 발행
        _dobot_publisher.publish(msg)
        _dobot_node.get_logger().info(f"Dobot Pick and Place 작업 명령 전송 완료: {msg.data}")
        
    except KeyError as e:
        if _dobot_node:
            _dobot_node.get_logger().error(f"좌표 데이터 누락 에러: {e}")
    except ValueError:
        if _dobot_node:
            _dobot_node.get_logger().error("좌표 데이터는 숫자(float) 형식이어야 합니다.")
            
    # 💡 주의: Django 서버가 계속 돌아가야 하고 노드를 재사용해야 하므로,
    # 기존에 있던 node.destroy_node() 와 rclpy.shutdown()은 절대 호출하지 않습니다.