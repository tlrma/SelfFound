import gpiod
import time
from fastapi import FastAPI, BackgroundTasks
import uvicorn
from contextlib import asynccontextmanager

# --- 1. 하드웨어 설정 ---
DIR_PIN = 17
STEP_PIN = 27
ENABLE_PIN = 22

chip = None
dir_line = None
step_line = None
enable_line = None

# --- 2. 서버 실행/종료 시 GPIO 관리 ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global chip, dir_line, step_line, enable_line
    
    print("[시스템] GPIO 초기화 및 서버 대기 중...")
    chip = gpiod.Chip('gpiochip0')
    dir_line = chip.get_line(DIR_PIN)
    step_line = chip.get_line(STEP_PIN)
    enable_line = chip.get_line(ENABLE_PIN)

    dir_line.request(consumer="dir", type=gpiod.LINE_REQ_DIR_OUT)
    step_line.request(consumer="step", type=gpiod.LINE_REQ_DIR_OUT)
    enable_line.request(consumer="enable", type=gpiod.LINE_REQ_DIR_OUT)
    
    enable_line.set_value(1) # 대기 상태에서는 모터 비활성화
    
    yield  # 서버가 켜져 있는 동안 여기 머뭄
    
    print("\n[시스템] 서버 종료. 자원을 해제합니다.")
    enable_line.set_value(1)
    dir_line.release()
    step_line.release()
    enable_line.release()

app = FastAPI(lifespan=lifespan)

# --- 3. 실제 모터 구동 함수 ---
def run_motor(steps: int, direction: int, delay: float):
    print(f"[동작] 컨베이어 벨트 {steps} 스텝 이동 시작")
    dir_line.set_value(direction)
    enable_line.set_value(0) # 모터 활성화
    
    for _ in range(steps):
        step_line.set_value(1)
        time.sleep(delay)
        step_line.set_value(0)
        time.sleep(delay)
        
    enable_line.set_value(1) # 모터 비활성화
    print("[완료] 이동 완료")

# --- 4. 메인 서버가 호출할 API 엔드포인트 ---
@app.post("/api/move")
def trigger_conveyor(background_tasks: BackgroundTasks):
    TARGET_STEPS = 2000  # 스텝 수, 이동 거리 조절
    DIRECTION = 0
    DELAY = 0.001
    
    # 모터가 도는 동안 API 응답이 지연되지 않도록 백그라운드로 실행
    background_tasks.add_task(run_motor, TARGET_STEPS, DIRECTION, DELAY)
    
    return {"status": "success", "message": "컨베이어 이동 명령을 수신했습니다."}

if __name__ == "__main__":
    # 라즈베리파이의 IP로 접근할 수 있게 0.0.0.0 포트 8000으로 실행
    uvicorn.run("pi_server:app", host="0.0.0.0", port=8000)