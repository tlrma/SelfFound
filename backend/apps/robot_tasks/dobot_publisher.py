import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
import time
import math

# Django 워커(Worker)가 살아있는 동안 rclpy 초기화 및 노드/퍼블리셔를 한 번만 유지하기 위한 전역 변수
_rclpy_initialized = False
_dobot_node = None
_dobot_publisher = None

def is_within_workspace(x, y, z):
    """
    Dobot의 물리적 작업 영역(Workspace) 내에 좌표가 존재하는지 검사합니다.
    """
    # 원점(Base)으로부터의 수평 거리(반경) 계산
    radius = math.sqrt(x**2 + y**2)
    
    # [설정 필요] 실제 로봇 환경에 맞게 한계 수치를 조절해 주십시오.
    MIN_RADIUS = 90.0  # 로봇 몸체와의 충돌을 막기 위한 최소 여유 공간
    MAX_RADIUS = 240.0  # 확인된 최대 안전 반경을 절대 한계치로 설정 (약 219mm 기준)
    MIN_Z = -98.0       # 확인된 최저 Z축 높이 (-98.315 기준)
    MAX_Z = 148.0       # 확인된 최고 Z축 높이 (148.942 기준)

    if radius < MIN_RADIUS or radius > MAX_RADIUS:
        return False, f"작업 반경 제한 초과 (현재 반경: {radius:.1f}mm, 허용: {MIN_RADIUS}~{MAX_RADIUS}mm)"
    
    if z < MIN_Z or z > MAX_Z:
        return False, f"Z축 높이 제한 초과 (현재 Z: {z:.1f}mm, 허용: {MIN_Z}~{MAX_Z}mm)"
        
    return True, "OK"

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

    # 3. 전송할 메시지 구성 및 안전 검사
    msg = Float64MultiArray()
    try:
        t1_x = float(target1_coords['x'])
        t1_y = float(target1_coords['y'])
        t1_z = float(target1_coords['z'])
        
        t2_x = float(target2_coords['x'])
        t2_y = float(target2_coords['y'])
        t2_z = float(target2_coords['z'])

        # 전송 전 T1, T2 좌표 안전성 검사
        is_t1_valid, t1_msg = is_within_workspace(t1_x, t1_y, t1_z)
        if not is_t1_valid:
            _dobot_node.get_logger().error(f"T1 좌표 오류: {t1_msg}")
            return False  # 전송 중단
            
        is_t2_valid, t2_msg = is_within_workspace(t2_x, t2_y, t2_z)
        if not is_t2_valid:
            _dobot_node.get_logger().error(f"T2 좌표 오류: {t2_msg}")
            return False  # 전송 중단

        msg.data = [t1_x, t1_y, t1_z, t2_x, t2_y, t2_z]
        
        # 4. 메시지 발행
        _dobot_publisher.publish(msg)
        _dobot_node.get_logger().info(f"Dobot Pick and Place 작업 명령 전송 완료: {msg.data}")
        return True
        
    except KeyError as e:
        if _dobot_node:
            _dobot_node.get_logger().error(f"좌표 데이터 누락 에러: {e}")
        return False
    except ValueError:
        if _dobot_node:
            _dobot_node.get_logger().error("좌표 데이터는 숫자(float) 형식이어야 합니다.")
        return False
            
    # 주의: Django 서버가 계속 돌아가야 하고 노드를 재사용해야 하므로,
    # 기존에 있던 node.destroy_node() 와 rclpy.shutdown()은 절대 호출하지 않습니다.