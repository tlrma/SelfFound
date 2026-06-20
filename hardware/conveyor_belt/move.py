# pi_server.py 가 정상 작동하면 삭제
import gpiod
import time

# --- 1. GPIO 핀 번호 설정 ---
DIR_PIN = 17
STEP_PIN = 27
ENABLE_PIN = 22

# --- 2. GPIO 초기화 및 설정 ---
chip = gpiod.Chip('gpiochip0')

dir_line = chip.get_line(DIR_PIN)
step_line = chip.get_line(STEP_PIN)
enable_line = chip.get_line(ENABLE_PIN)

dir_line.request(consumer="dir", type=gpiod.LINE_REQ_DIR_OUT)
step_line.request(consumer="step", type=gpiod.LINE_REQ_DIR_OUT)
enable_line.request(consumer="enable", type=gpiod.LINE_REQ_DIR_OUT)

# --- 3. 동작 설정 변수 ---
# 이 값을 조절하여 실제 이동 거리를 맞추시면 됩니다.
TARGET_STEPS = 1000  

# 방향 설정 (0 또는 1)
DIRECTION = 0 

# 모터 속도 (펄스 간 대기 시간)
DELAY = 0.001 

try:
    print(f"컨베이어 벨트를 {TARGET_STEPS} 스텝만큼 이동합니다.")
    
    # 방향 설정 및 모터 활성화
    dir_line.set_value(DIRECTION)
    enable_line.set_value(0)
    
    # 지정된 스텝 수만큼 펄스 생성하여 모터 구동
    for _ in range(TARGET_STEPS):
        step_line.set_value(1)
        time.sleep(DELAY)
        step_line.set_value(0)
        time.sleep(DELAY)
        
    print("이동이 완료되었습니다.")

except KeyboardInterrupt:
    print("\n사용자에 의해 프로그램이 강제 정지되었습니다.")

finally:
    # 프로그램 종료 시 모터 비활성화 및 리소스 해제
    enable_line.set_value(1)
    dir_line.release()
    step_line.release()
    enable_line.release()
    print("GPIO 자원이 안전하게 해제되었습니다.")