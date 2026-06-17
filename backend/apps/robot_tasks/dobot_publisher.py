import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray

# Django 워커(Worker)가 살아있는 동안 rclpy 초기화를 한 번만 수행하기 위한 플래그
_rclpy_initialized = False

def publish_dobot_pick_and_place_task(target1_coords, target2_coords):
    """
    Dobot에게 물건을 집을 위치(Target1)와 놓을 위치(Target2)의 좌표를 전송합니다.
    """
    global _rclpy_initialized
    
    # 1. rclpy가 초기화되지 않았다면 한 번만 초기화 진행
    if not _rclpy_initialized:
        rclpy.init()
        _rclpy_initialized = True

    # 2. 임시 퍼블리셔 노드 생성
    node = Node('django_dobot_publisher')
    
    # 3. 토픽 생성 (큐 사이즈: 10)
    publisher = node.create_publisher(Float64MultiArray, '/dobot_task_targets', 10)
    
    # 4. 전송할 메시지 구성: [T1_x, T1_y, T1_z, T2_x, T2_y, T2_z]
    msg = Float64MultiArray()
    try:
        msg.data = [
            float(target1_coords['x']), float(target1_coords['y']), float(target1_coords['z']),
            float(target2_coords['x']), float(target2_coords['y']), float(target2_coords['z'])
        ]
        
        # 5. 메시지 발행
        publisher.publish(msg)
        node.get_logger().info(f"Dobot Pick and Place 작업 명령 전송 완료: {msg.data}")
        
    except KeyError as e:
        node.get_logger().error(f"좌표 데이터 누락 에러: {e}")
    except ValueError:
        node.get_logger().error("좌표 데이터는 숫자(float) 형식이어야 합니다.")
        
    finally:
        # 6. 사용이 끝난 노드 메모리 해제
        node.destroy_node()
        # 💡 주의: Django 서버가 계속 돌아가야 하므로 rclpy.shutdown()은 호출하지 않습니다.