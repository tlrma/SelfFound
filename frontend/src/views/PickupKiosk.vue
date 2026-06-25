<template>
  <div class="kiosk-container">
    <header class="kiosk-header">
      <h1>🤖 분실물 무인 반환 시스템 🤖</h1>
    </header>

    <main class="kiosk-content">
      <div v-if="currentStep === 1" class="step-box">
        <h2>👋 무인 반환 시스템에 오신 것을 환영합니다</h2>
        <p class="description">분실물을 찾으러 오셨나요?<br>이메일로 안내받은 <strong>인증 코드(6자리)</strong>를 입력해 주세요.</p>
        
        <div class="form-group verification-zone">
          <input 
            type="text" 
            v-model="verificationCode" 
            placeholder="인증 코드 6자리 입력" 
            maxlength="6" 
            class="kiosk-input code-input" 
          />
          <button @click="verifyCode" class="btn-verify">인증 및 조회</button>
        </div>
      </div>

      <div v-if="currentStep === 2" class="step-box">
        <h2>📷 수령인 확인을 위한 사진 촬영</h2>
        <p class="warning-text">※ 안전한 분실물 반환을 위해 수령인의 페이스 정보를 촬영합니다.</p>
        <p class="description">수집된 데이터는 7일 후 안전하게 자동 폐기됩니다.</p>
        
        <div class="webcam-zone">
          <video ref="videoRef" autoplay playsinline class="webcam-preview"></video>
          <canvas ref="canvasRef" style="display: none;"></canvas>
          <div class="capture-countdown">
            <span class="timer-num">{{ captureCountdown }}</span>초 후 자동 촬영됩니다
          </div>
        </div>
      </div>

      <div v-if="currentStep === 3" class="step-box">
        <h3>물품을 가져오는 중입니다</h3>
        <div class="robot-animation-box">
          <div class="turtlebot-mock">📦 Robot</div>
          <p class="robot-status">잠시만 기다려 주세요</p>
          <ol class="robot-progress-list">
            <li
              v-for="step in robotProgressSteps"
              :key="step.id"
              :class="['robot-progress-item', getRobotProgressState(step.id)]"
            >
              <span class="progress-mark">{{ getRobotProgressMark(step.id) }}</span>
              <span>{{ step.label }}</span>
            </li>
          </ol>
        </div>

        <div v-if="isItemArrived" class="confirmation-zone">
          <h3>도착한 물품이 본인의 분실물이 맞습니까?</h3>
          <p class="warning-text">※ 다른 사람의 물품을 고의로 수령할 경우 법적 책임이 따를 수 있습니다.</p>
          
          <div class="btn-group-row">
            <button @click="handlePickupDecision(true)" class="btn-yes">⭕ 예, 제 물건이 맞습니다</button>
            <button @click="handlePickupDecision(false)" class="btn-no">❌ 아니오, 제 물건이 아닙니다</button>
          </div>
        </div>
      </div>

      <div v-if="currentStep === 4" class="step-box completion-box">
        <div v-if="isConfirmed" class="success-message">
          <h2>🎉 수령 완료</h2>
          <p>분실물 수령 처리가 최종 완료되었습니다. 이용해 주셔서 감사합니다.</p>
        </div>
        <div v-else class="return-message">
          <h2>🔄 물품 회수 및 반송</h2>
          <p>물품이 본인 것이 아니라고 선택하셨습니다.</p>
          <p>터틀봇이 물품을 안전하게 보관함으로 다시 회수합니다. 물품을 원 위치에 올려주세요.</p>
          <p>일치하는 분실물이 들어오면 다시 메일로 알려드리겠습니다.</p>
        </div>

        <div class="countdown-zone">
          <p><strong>{{ countdown }}초 후</strong> 첫 화면으로 자동으로 돌아갑니다.</p>
          <button @click="resetKiosk" class="btn-home">즉시 처음으로 이동</button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue';
import axios from 'axios';
import { useRosStore } from '@/stores/ros';

const currentStep = ref(1);
const rosStore = useRosStore();

// 데이터 관리 변수
const reportId = ref('');
const verificationCode = ref('');
const isConfirmed = ref(false);
const countdown = ref(5);
const captureCountdown = ref(5);
const robotStatus = ref('');
const isItemArrived = ref(false);
const pickupProgressStep = ref(1);

const robotProgressSteps = [
  { id: 1, label: '터틀봇이 보관함으로 이동하고 있어요' },
  { id: 2, label: '물건을 꺼내고 있어요' },
  { id: 3, label: '터틀봇이 카운터로 오고 있어요' },
];

const getRobotProgressState = (stepId) => {
  if (stepId < pickupProgressStep.value || isItemArrived.value) return 'is-done';
  if (stepId === pickupProgressStep.value) return 'is-active';
  return 'is-waiting';
};

const getRobotProgressMark = (stepId) => {
  if (stepId < pickupProgressStep.value || isItemArrived.value) return '✓';
  if (stepId === pickupProgressStep.value) return '●';
  return '○';
};

// 웹캠 객체 참조값
const videoRef = ref(null);
const canvasRef = ref(null);
let streamObject = null;
let mainTimer = null;
let webcamTimer = null;
let turtlebotStatusTopic = null;
let dobotStatusTopic = null;

// Dobot 좌표 (verify_code 응답으로 채워짐)
let dobotPickCoords = [0, 0, 0];
let dobotPlaceCoords = [0, 0, 0];

const speak = (text) => {
  if (!('speechSynthesis' in window)) return;

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = 'ko-KR';
  utterance.rate = 0.95;
  utterance.pitch = 1;
  window.speechSynthesis.speak(utterance);
};

const speakPickupArrivalGuide = () => {
  speak('터틀봇이 물건을 가지고 도착했습니다. 물건을 확인해 주세요. 본인의 물건이 맞으면 예 버튼을 눌러 주세요. 본인의 물건이 아니라면 물건을 원래 위치에 다시 내려놓고 아니오 버튼을 눌러 주세요.');
};

// rosbridge 연결 대기
const waitForRosConnection = () =>
  new Promise((resolve) => {
    if (rosStore.isConnected) { resolve(); return; }
    const unwatch = watch(() => rosStore.isConnected, (connected) => {
      if (connected) { unwatch(); resolve(); }
    });
  });

// TurtleBot 이동 명령 발행
const turtlebotGoto = (poseName) => {
  rosStore.publish('/turtlebot/goto_pose', 'std_msgs/String', { data: poseName });
};

// Dobot 픽업 명령 발행
const dobotPickAndPlace = () => {
  rosStore.publish('/dobot_task_targets', 'std_msgs/Float64MultiArray', {
    data: [...dobotPickCoords, ...dobotPlaceCoords],
  });
};

// TurtleBot 특정 pose 도착 대기 후 콜백 실행
const waitForTurtlebot = (poseName, callback) => {
  turtlebotStatusTopic = rosStore.subscribe(
    '/turtlebot/status',
    'std_msgs/String',
    (msg) => {
      robotStatus.value = msg.data;
      if (msg.data === `arrived:${poseName}`) {
        turtlebotStatusTopic?.unsubscribe();
        turtlebotStatusTopic = null;
        callback();
      }
    },
  );
};

// Dobot 완료 대기 (expectedMsg: 'done:pickup' | 'done:return')
const waitForDobot = (expectedMsg, callback) => {
  dobotStatusTopic = rosStore.subscribe(
    '/dobot_status',
    'std_msgs/String',
    (msg) => {
      if (msg.data === expectedMsg) {
        dobotStatusTopic?.unsubscribe();
        dobotStatusTopic = null;
        callback();
      }
    },
  );
};

// Dobot 재적재 명령 발행 (픽업의 역순: TurtleBot → 창고)
const dobotReturn = () => {
  rosStore.publish('/dobot_task_targets', 'std_msgs/Float64MultiArray', {
    data: [...dobotPlaceCoords, ...dobotPickCoords],
  });
};

// 로봇 시퀀스 시작: TurtleBot → dobot_near → Dobot 픽업 → TurtleBot → return_counter
const startRobotSequence = async () => {
  await waitForRosConnection();
  isItemArrived.value = false;
  pickupProgressStep.value = 1;
  robotStatus.value = 'TurtleBot 이동 중...';
  turtlebotGoto('dobot_near');

  waitForTurtlebot('dobot_near', () => {
    pickupProgressStep.value = 2;
    robotStatus.value = 'Dobot 픽업 중...';
    dobotPickAndPlace();

    waitForDobot('done:pickup', () => {
      pickupProgressStep.value = 3;
      robotStatus.value = 'TurtleBot 수령 구역으로 이동 중...';
      turtlebotGoto('return_counter');

      waitForTurtlebot('return_counter', () => {
        robotStatus.value = '물품이 도착했습니다.';
        isItemArrived.value = true;
        speakPickupArrivalGuide();
      });
    });
  });
};

// [1단계] 6자리 백엔드 코드 검증 API 연동
const verifyCode = async () => {
  if (verificationCode.value.length < 6) {
    alert('인증 코드 6자리를 정확히 입력해 주세요.');
    return;
  }

  try {
    const response = await axios.post('/api/pickup/verify-code/', {
      code: verificationCode.value,
    });

    if (response.status === 200) {
      reportId.value = response.data.report_id;
      dobotPickCoords = response.data.dobot_pick_coords;
      dobotPlaceCoords = response.data.dobot_place_coords;

      currentStep.value = 2;
      initWebcam();
    }
  } catch (error) {
    console.error('인증 실패:', error);
    if (error.response && error.response.data && error.response.data.error) {
      alert(error.response.data.error);
    } else {
      alert('인증 확인 중 오류가 발생했습니다. 다시 시도해 주세요.');
    }
  }
};

// [2단계] 미디어 장치 제어 및 자동 카운트다운 촬영 처리
const initWebcam = async () => {
  captureCountdown.value = 5;
  try {
    // 사용자의 웹캠 스트림 활성화
    streamObject = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
    if (videoRef.value) {
      videoRef.value.srcObject = streamObject;
    }

    // 5초 자동 촬영 타이머 트리거
    webcamTimer = setInterval(() => {
      captureCountdown.value--;
      if (captureCountdown.value <= 0) {
        clearInterval(webcamTimer);
        captureAndUpload();
      }
    }, 1000);
  } catch (err) {
    console.error('카메라 디바이스를 접근할 수 없습니다:', err);
    alert('카메라 장치 오류가 발생하여 시뮬레이션을 위해 다음 단계로 강제 전환합니다.');
    currentStep.value = 3;
    startRobotSequence();
  }
};

// 캔버스 드로잉을 통한 이미지 바이너리 캡처 및 전송
const captureAndUpload = async () => {
  if (!videoRef.value || !canvasRef.value) return;

  const video = videoRef.value;
  const canvas = canvasRef.value;
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;

  const ctx = canvas.getContext('2d');
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  // image_b64 형태의 base64 인코딩 데이터 추출
  const imageDataB64 = canvas.toDataURL('image/jpeg');

  // 웹캠 장치 자원 즉시 해제
  stopWebcam();

  try {
    // 수령인 사진 업로드 전용 엔드포인트 연동 (동작 명확성을 위해 분리 또는 연계 가능)
    await axios.post('/api/pickup/confirm/', {
      report_id: reportId.value,
      image_b64: imageDataB64,
      status: 'processing' // 로봇 배송 대기 중 상태 전환
    });
  } catch (error) {
    console.error('이미지 바이너리 백엔드 전송 실패:', error);
  }

  // 데이터 전송 완료 후 로봇 호출(3단계) 화면 전환 및 로봇 시퀀스 시작
  currentStep.value = 3;
  startRobotSequence();
};

const stopWebcam = () => {
  if (streamObject) {
    streamObject.getTracks().forEach(track => track.stop());
    streamObject = null;
  }
  if (webcamTimer) clearInterval(webcamTimer);
};

// [3단계] 최종 수령 수락 / 반송 여부 결정 처리 (기존 구조 보존)
const handlePickupDecision = async (isMine) => {
  isConfirmed.value = isMine;

  if (isMine) {
    turtlebotGoto('waiting');
    try {
      await axios.post('/api/pickup/confirm/', {
        report_id: reportId.value,
        status: 'completed',
      });
    } catch (error) {
      console.error('최종 확정 처리 에러:', error);
    }
  } else {
    currentStep.value = 4;
    startCountdown();

    // --- ✅ [추가] '아니오'를 눌렀을 때 백엔드로 'returned' 상태 전송 ---
    try {
      await axios.post('/api/pickup/confirm/', {
        report_id: reportId.value,
        status: 'returned', // views.py에서 이 값을 받아 처리합니다.
      });
    } catch (error) {
      console.error('반송 상태 업데이트 에러:', error);
    }

    robotStatus.value = 'TurtleBot 창고로 복귀 중...';
    turtlebotGoto('dobot_near');
    waitForTurtlebot('dobot_near', () => {
      robotStatus.value = 'Dobot 재적재 중...';
      dobotReturn();
      waitForDobot('done:return', () => {
        turtlebotGoto('waiting');
      });
    });
    return;
  }

  currentStep.value = 4;
  startCountdown();
};

const startCountdown = () => {
  countdown.value = 5;
  mainTimer = setInterval(() => {
    countdown.value--;
    if (countdown.value <= 0) {
      resetKiosk();
    }
  }, 1000);
};

const resetKiosk = () => {
  if (mainTimer) clearInterval(mainTimer);
  if ('speechSynthesis' in window) window.speechSynthesis.cancel();
  stopWebcam();
  //turtlebotStatusTopic?.unsubscribe();
  //turtlebotStatusTopic = null;
  //dobotStatusTopic?.unsubscribe();
  //dobotStatusTopic = null;
  robotStatus.value = '';
  isItemArrived.value = false;
  pickupProgressStep.value = 1;
  currentStep.value = 1;
  reportId.value = '';
  verificationCode.value = '';
  isConfirmed.value = false;
};

onMounted(() => {
  rosStore.connect();
});

onBeforeUnmount(() => {
  if (mainTimer) clearInterval(mainTimer);
  if ('speechSynthesis' in window) window.speechSynthesis.cancel();
  stopWebcam();
});
</script>

<style scoped>
/* 기존 스타일 하단 유지 및 추가 디자인 구성 */
.kiosk-container {
  max-width: 800px;
  margin: 40px auto;
  padding: 30px;
  border: 4px solid #333;
  border-radius: 16px;
  background-color: #ffffff;
  box-shadow: 0 10px 25px rgba(0,0,0,0.15);
  font-family: sans-serif;
  text-align: center;
}
.kiosk-header { border-bottom: 3px solid #333; padding-bottom: 20px; margin-bottom: 30px; }
.kiosk-header h1 { font-size: 32px; color: #1a1a1a; margin: 0 0 10px 0; }
.step-indicator { font-size: 18px; font-weight: bold; color: #0275d8; margin: 0; }
.step-box h2 { font-size: 24px; color: #2c3e50; margin-bottom: 25px; }
.description { color: #555; font-size: 16px; }
.warning-text { color: #d9534f; font-weight: bold; font-size: 14px; margin-bottom: 20px; }
.form-group { margin-top: 30px; display: flex; justify-content: center; gap: 10px; }
.kiosk-input { padding: 15px; font-size: 18px; border: 2px solid #ccc; border-radius: 8px; width: 250px; text-align: center; }
.code-input { font-size: 20px; letter-spacing: 2px; font-weight: bold; color: #2c3e50; }
button { font-weight: bold; border-radius: 8px; border: none; cursor: pointer; transition: background-color 0.15s, transform 0.1s; }
button:active { transform: scale(0.98); }
.btn-verify { padding: 15px 30px; font-size: 18px; background-color: #42b983; color: white; }

/* 📷 웹캠 컴포넌트 프레임 전용 UI 클래스 구성 */
.webcam-zone {
  position: relative;
  width: 480px;
  margin: 20px auto;
  border: 4px solid #1e293b;
  border-radius: 12px;
  overflow: hidden;
  background-color: #000;
}
.webcam-preview {
  width: 100%;
  height: auto;
  display: block;
  transform: rotateY(180deg); /* 거울 모드 반전 효과 */
}
.capture-countdown {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  background: rgba(0, 0, 0, 0.7);
  color: #fff;
  padding: 12px 0;
  font-size: 16px;
}
.timer-num {
  color: #ff4d4d;
  font-size: 24px;
  font-weight: bold;
  margin-right: 4px;
}

.robot-animation-box { background-color: #f8fafc; border: 2px dashed #cbd5e1; padding: 24px 28px 28px; border-radius: 12px; margin-bottom: 30px; }
.turtlebot-mock { width: 112px; height: 52px; background-color: #334155; color: white; font-weight: bold; line-height: 52px; border-radius: 26px; margin: 0 auto 12px auto; animation: robot-move 3s infinite ease-in-out; }
@keyframes robot-move { 0% { transform: translateX(-30px); } 50% { transform: translateX(30px); } 100% { transform: translateX(-30px); } }
.robot-status { font-size: 14px; color: #64748b; margin: 0; }
.robot-progress-list {
  width: min(560px, 100%);
  margin: 24px auto 0;
  padding: 0;
  list-style: none;
  text-align: left;
}
.robot-progress-item {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 40px;
  color: #94a3b8;
  font-size: 18px;
  font-weight: 700;
}
.robot-progress-item.is-active {
  color: #1d3557;
  font-size: 19px;
  font-weight: 800;
}
.robot-progress-item.is-done {
  color: #2a9d8f;
}
.progress-mark {
  width: 28px;
  flex: 0 0 28px;
  text-align: center;
  font-size: 19px;
  font-weight: 900;
}
.btn-group-row { display: flex; justify-content: center; gap: 20px; margin-top: 15px; }
.btn-yes { padding: 20px 35px; font-size: 20px; background-color: #5cb85c; color: white; }
.btn-no { padding: 20px 35px; font-size: 20px; background-color: #d9534f; color: white; }
.completion-box { padding: 20px 0; }
.success-message h2 { color: #5cb85c; }
.return-message h2 { color: #d9534f; }
.db-notice { font-family: monospace; color: #0275d8; font-weight: bold; }
.countdown-zone { margin-top: 40px; border-top: 1px solid #eee; padding-top: 20px; }
.btn-home { padding: 12px 24px; background-color: #6c757d; color: white; margin-top: 10px; font-size: 15px; }
</style>
