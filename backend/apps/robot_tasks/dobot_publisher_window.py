import math
import time

import roslibpy


ROS_HOST = "192.168.110.241"
ROS_PORT = 9091

_ros_client = None
_dobot_topic = None


def is_within_workspace(x, y, z):
    """
    Dobot의 물리적 작업 영역(Workspace) 안에 좌표가 존재하는지 검사합니다.
    """
    radius = math.sqrt(x**2 + y**2)

    MIN_RADIUS = 70.0
    MAX_RADIUS = 240.0
    MIN_Z = -98.0
    MAX_Z = 148.0

    if radius < MIN_RADIUS or radius > MAX_RADIUS:
        return (
            False,
            f"작업 반경 제한 초과 (현재 반경: {radius:.1f}mm, 허용: {MIN_RADIUS}~{MAX_RADIUS}mm)",
        )

    if z < MIN_Z or z > MAX_Z:
        return (
            False,
            f"Z축 높이 제한 초과 (현재 Z: {z:.1f}mm, 허용: {MIN_Z}~{MAX_Z}mm)",
        )

    return True, "OK"


def _get_dobot_topic():
    """
    Django worker가 살아있는 동안 rosbridge 연결과 topic을 재사용합니다.
    """
    global _ros_client, _dobot_topic

    if _ros_client is None:
        _ros_client = roslibpy.Ros(host=ROS_HOST, port=ROS_PORT)
        _ros_client.run()
        time.sleep(1.0)
        print("[dobot_publisher_window] rosbridge 연결 및 publisher topic 생성 완료")

    if not _ros_client.is_connected:
        _ros_client.run()
        time.sleep(1.0)
        print("[dobot_publisher_window] rosbridge 재연결 완료")

    if _dobot_topic is None:
        _dobot_topic = roslibpy.Topic(
            _ros_client,
            "/dobot_task_targets",
            "std_msgs/Float64MultiArray",
        )

    return _dobot_topic


def publish_dobot_pick_and_place_task(target1_coords, target2_coords):
    """
    Dobot에게 물건을 집을 위치(Target1)와 놓을 위치(Target2)의 좌표를 전송합니다.
    Windows에서는 rosbridge WebSocket을 통해 Linux rclpy publisher와 같은 topic에 발행합니다.
    """
    try:
        t1_x = float(target1_coords["x"])
        t1_y = float(target1_coords["y"])
        t1_z = float(target1_coords["z"])

        t2_x = float(target2_coords["x"])
        t2_y = float(target2_coords["y"])
        t2_z = float(target2_coords["z"])

        is_t1_valid, t1_msg = is_within_workspace(t1_x, t1_y, t1_z)
        if not is_t1_valid:
            print(f"[dobot_publisher_window] T1 좌표 오류: {t1_msg}")
            return False

        is_t2_valid, t2_msg = is_within_workspace(t2_x, t2_y, t2_z)
        if not is_t2_valid:
            print(f"[dobot_publisher_window] T2 좌표 오류: {t2_msg}")
            return False

        data = [t1_x, t1_y, t1_z, t2_x, t2_y, t2_z]
        msg = roslibpy.Message({"data": data})
        topic = _get_dobot_topic()
        topic.publish(msg)

        print(f"[dobot_publisher_window] Dobot Pick and Place 작업 명령 전송 완료: {data}")
        return True

    except KeyError as e:
        print(f"[dobot_publisher_window] 좌표 데이터 누락 오류: {e}")
        return False
    except ValueError:
        print("[dobot_publisher_window] 좌표 데이터는 숫자(float) 형식이어야 합니다.")
        return False
    except Exception as e:
        print(f"[dobot_publisher_window] rosbridge 발행 실패: {e}")
        return False
