from pymodbus.client.sync import ModbusTcpClient
import time

# --- 설정값 (같은 컴퓨터 내부 통신) ---
SERVER_IP = '127.0.0.1'  # 자기 자신(로컬호스트)을 가리키는 IP
SERVER_PORT = 5020       # 서버가 열려있는 포트 번호

def run_test_client():
    print(f"[{SERVER_IP}:{SERVER_PORT}] 서버에 연결을 시도합니다...")
    
    # 1. 클라이언트 객체 생성 및 연결
    client = ModbusTcpClient(SERVER_IP, port=SERVER_PORT)
    
    if client.connect():
        print("✅ 서버 연결 성공!")
        
        # 2. 레지스터[0]에 값 1을 쓰기 (명령 하달)
        print("레지스터[0]의 값을 1로 변경하는 신호를 전송합니다.")
        write_result = client.write_register(address=0, value=1)
        
        # 3. 전송 결과 확인
        if not write_result.isError():
            print("✅ 레지스터 값 변경 완료! 서버 측 터미널(로그)을 확인해 보세요.")
        else:
            print("❌ 레지스터 값 변경 실패:", write_result)
            
        # 4. 연결 안전하게 종료
        client.close()
        print("연결을 종료합니다.")
        
    else:
        print("❌ 서버에 연결할 수 없습니다. 서버 프로그램(server.py)이 실행 중인지 확인하세요.")

if __name__ == "__main__":
    run_test_client()