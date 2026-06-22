import time
from conveyor_client import trigger_conveyor_belt
from dobot_publisher import publish_dobot_pick_and_place_task

def test_conveyor():
    print("\n--- [테스트 1] 컨베이어 벨트 구동 테스트 ---")
    print("라즈베리파이로 이동 신호를 전송합니다...")
    success = trigger_conveyor_belt()
    if success:
        print("✅ 컨베이어 신호 전송 성공! 벨트가 움직이는지 확인하세요.")
    else:
        print("❌ 컨베이어 신호 전송 실패. 라즈베리파이 연결 상태를 확인하세요.")

def test_dobot():
    print("\n--- [테스트 2] 두봇(Dobot) Pick & Place 테스트 ---")
    
    # 임의의 테스트 좌표 (실제 환경에 맞춰 안전한 위치의 값으로 변경하세요)
    test_target1 = {'x': 250.0, 'y': 0.0, 'z': 50.0}   # 집는 위치(Pick)
    test_target2 = {'x': 150.0, 'y': 150.0, 'z': 50.0} # 놓는 위치(Place), 성공시 warehouse 의 좌표 업데이트
    
    print(f"Target 1 (Pick): {test_target1}")
    print(f"Target 2 (Place): {test_target2}")
    print("두봇으로 ROS 2 제어 명령을 전송합니다...")
    
    publish_dobot_pick_and_place_task(test_target1, test_target2)
    print("✅ 두봇 명령 전송 완료! 로봇 팔이 목표 좌표로 이동하는지 확인하세요.")

if __name__ == '__main__':
    print("=== 하드웨어 연동 점검을 시작합니다 ===")
    
    # 1. 컨베이어 벨트 테스트 실행
    test_conveyor()
    
    # 2. 두봇 테스트 실행
    #test_dobot()
    
    print("\n=== 모든 테스트가 종료되었습니다 ===")