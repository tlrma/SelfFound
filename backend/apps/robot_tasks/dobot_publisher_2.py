import roslibpy

ROS_HOST = 'localhost'  # ROS2 노트북 IP로 변경 (예: '192.168.0.10')
ROS_PORT = 9090


def publish_dobot_pick_and_place_task(target1_coords, target2_coords):
    """
    Dobot에게 물건을 집을 위치(Target1)와 놓을 위치(Target2)의 좌표를 전송합니다.
    roslibpy를 사용해 rosbridge WebSocket을 통해 발행합니다. (Windows 호환)
    """
    client = roslibpy.Ros(host=ROS_HOST, port=ROS_PORT)
    client.run()

    try:
        topic = roslibpy.Topic(client, '/dobot_task_targets', 'std_msgs/Float64MultiArray')
        msg = roslibpy.Message({
            'data': [
                float(target1_coords['x']), float(target1_coords['y']), float(target1_coords['z']),
                float(target2_coords['x']), float(target2_coords['y']), float(target2_coords['z']),
            ]
        })
        topic.publish(msg)
        print(f'[dobot_publisher_2] 전송 완료: {msg}')

    except KeyError as e:
        print(f'[dobot_publisher_2] 좌표 데이터 누락: {e}')
    except ValueError:
        print('[dobot_publisher_2] 좌표는 숫자(float) 형식이어야 합니다.')
    finally:
        client.terminate()
