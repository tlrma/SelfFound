import time
import subprocess
from pymodbus.client import ModbusTcpClient

# --- 설정값 ---
SERVER_IP = '192.168.110.241'
SERVER_PORT = 502  # Modbus TCP 기본 포트
POLL_INTERVAL = 0.5  # 레지스터 확인 주기 (0.5초)

def run_modbus_client():
    # Modbus 서버 연결 설정
    client = ModbusTcpClient(SERVER_IP, port=SERVER_PORT)

    if not client.connect():
        print(f"[{SERVER_IP}:{SERVER_PORT}] Modbus 서버에 연결할 수 없습니다. IP와 네트워크 상태를 확인하세요.")
        return

    print(f"[{SERVER_IP}:{SERVER_PORT}] Modbus 서버 연결 성공. 레지스터[0] 감시를 시작합니다.")

    try:
        while True:
            # Holding Register 0번 주소에서 1개의 값을 읽어옴
            response = client.read_holding_registers(address=0, count=1)

            if not response.isError():
                reg_value = response.registers[0]

                # 레지스터 값이 1일 때 동작 수행
                if reg_value == 1:
                    print("\n[감지] 레지스터[0] 값이 1입니다. move.py 실행을 시작합니다.")

                    # 1. move.py 실행
                    try:
                        # subprocess.run은 move.py의 실행이 완전히 끝날 때까지 대기합니다.
                        subprocess.run(["python", "move.py"], check=True)
                        print("[완료] move.py 실행이 성공적으로 종료되었습니다.")
                    except subprocess.CalledProcessError as e:
                        print(f"[오류] move.py 실행 중 문제 발생: {e}")
                    except FileNotFoundError:
                        print("[오류] 현재 폴더에서 move.py 파일을 찾을 수 없습니다.")

                    # 2. 실행 완료 후 레지스터[0] 값을 다시 0으로 초기화
                    write_response = client.write_register(address=0, value=0)
                    
                    if not write_response.isError():
                        print("[초기화] 레지스터[0] 값을 0으로 정상 변경했습니다. 다시 감시를 시작합니다.")
                    else:
                        print("[오류] 레지스터 값을 0으로 초기화하는 데 실패했습니다.")

            else:
                print(f"[통신 오류] 레지스터를 읽어오지 못했습니다: {response}")

            # 서버에 과부하를 주지 않기 위해 지정된 시간만큼 대기
            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\n사용자에 의해 프로그램이 정지되었습니다.")
    finally:
        # 프로그램 종료 시 연결 해제
        client.close()
        print("Modbus 연결이 안전하게 해제되었습니다.")

if __name__ == "__main__":
    run_modbus_client()