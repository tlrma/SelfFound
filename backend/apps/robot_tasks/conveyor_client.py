import requests

# 라즈베리파이의 실제 고정 IP 주소로 변경
RASPBERRY_PI_URL = "http://192.168.110.148:8000/api/move" 

def trigger_conveyor_belt():
    """
    라즈베리파이 서버로 컨베이어 벨트 구동 명령(POST)을 전송합니다.
    """
    try:
        # timeout=2.0을 주어 라즈베리파이가 꺼져있어도 Django 서버가 멈추지 않게 보호합니다.
        response = requests.post(RASPBERRY_PI_URL, timeout=2.0)
        
        if response.status_code == 200:
            print("컨베이어 벨트 구동 명령 전송 성공!")
            return True
        else:
            print(f"컨베이어 에러 응답: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"라즈베리파이 연결 실패 (기기 꺼짐 또는 네트워크 오류): {e}")
        return False