<template>
  <div class="kiosk-container">
    <header class="kiosk-header">
      <h1>🤖 분실물 무인 반환 시스템</h1>
      <p class="step-indicator">단계: {{ currentStep }} / 4</p>
    </header>

    <main class="kiosk-content">
      <div v-if="currentStep === 1" class="step-box">
        <h2>📷 안내문에 포함된 QR코드를 스캔해 주세요</h2>
        <div class="qr-scanner-mock">
          <div class="laser-line"></div>
          <p class="mock-text">[ OpenCV QRCodeDetector 대기 중 ]</p>
        </div>
        <p class="notice">※ 현재 장비 테스트 중입니다. 아래 임시 버튼을 눌러 스캔을 완료하세요.</p>
        
        <div class="form-group">
          <input type="text" v-model="mockQrData" placeholder="스캔된 QR 데이터 (임시 접수 ID)" class="kiosk-input" />
          <button @click="simulateQrScan" class="btn-next">QR 스캔 완료 처리</button>
        </div>
      </div>

      <div v-if="currentStep === 2" class="step-box">
        <h2>🔒 본인 확인 절차</h2>
        <p class="description">수신하신 안내 메일의 [4자리 인증번호] 를 입력해 주세요. (테스트 인증번호 :1234)</p>
        
        <div class="form-group verification-zone">
          <input 
            type="text" 
            v-model="verificationCode" 
            placeholder="인증번호 4자리 입력" 
            maxlength="4" 
            class="kiosk-input code-input" 
          />
          <button @click="verifyCode" class="btn-verify">인증 확인</button>
        </div>
      </div>

      <div v-if="currentStep === 3" class="step-box">
        <h2>🤖 터틀봇이 물품을 가져오는 중입니다...</h2>
        <div class="robot-animation-box">
          <div class="turtlebot-mock">📦 Robot</div>
          <p class="robot-status">터틀봇이 보관함에서 물품을 꺼내 이송 구역으로 이동하고 있습니다.</p>
        </div>

        <div class="confirmation-zone">
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
          <p class="db-notice">[ DB 상태: 'completed' (수령완료) 변경 완료 ]</p>
        </div>
        <div v-else class="return-message">
          <h2>🔄 물품 회수 및 반송</h2>
          <p>물품이 본인 것이 아니라고 선택하셨습니다.</p>
          <p>터틀봇이 물품을 안전하게 보관함으로 다시 회수합니다. 관리자에게 문의해 주세요.</p>
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
import { ref, onBeforeUnmount } from 'vue';
import axios from 'axios';

// 키오스크 현재 단계 관리 (1: QR, 2: 본인인증, 3: 수령확인, 4: 완료)
const currentStep = ref(1);

// 데이터 바인딩 변수
const reportId = ref('');
const mockQrData = ref('7'); // 임시 테스트용 발급 ID 설정 가능
const verificationCode = ref('');
const isConfirmed = ref(false);
const countdown = ref(5);
let timer = null;

// [1단계] QR 스캔 시뮬레이션 처리 함수
const simulateQrScan = () => {
  if (!mockQrData.value) {
    alert('임시 QR 데이터(신고 ID)를 입력하거나 확인해 주세요.');
    return;
  }
  reportId.value = mockQrData.value;
  // 스캔 성공 후 2단계(본인 인증)로 이동
  currentStep.value = 2;
};

// [2단계] 백엔드 코드 검증 API 연동 함수
const verifyCode = async () => {
  if (verificationCode.value.length < 4) {
    alert('인증번호 4자리를 정확히 입력해 주세요.');
    return;
  }

  try {
    // POST /api/pickup/verify-code/ 호출
    const response = await axios.post('/api/pickup/verify-code/', {
      report_id: reportId.value,
      code: verificationCode.value
    });

    if (response.status === 200) {
      alert('본인 확인이 완료되었습니다. 터틀봇 호출을 시작합니다.');
      currentStep.value = 3; // 3단계(물품 확인)로 이동
    }
  } catch (error) {
    console.error('인증 실패:', error);
    // 임시 테스트 목적으로 백엔드 서버 연결이 없을 때도 프론트 흐름을 볼 수 있도록 방어 코드 추가
    if (error.response && error.response.data && error.response.data.error) {
      alert(error.response.data.error); // 백엔드가 보낸 "인증번호가 일치하지 않습니다." 출력
    } else {
      alert('인증 처리 중 오류가 발생했습니다.');
    }
  }
};

// [3단계] YES / NO 버튼 선택 처리 및 수령 완료 API 연동 함수
const handlePickupDecision = async (isMine) => {
  isConfirmed.value = isMine;

  if (isMine) {
    // 사용자가 'YES'를 선택한 경우 - 최종 수령 처리 연동
    try {
      // POST /api/pickup/confirm/ 호출
      await axios.post('/api/pickup/confirm/', {
        report_id: reportId.value,
        status: 'completed' // 장고 backend models.py 매핑용 상태 값
      });
    } catch (error) {
      console.error('최종 수령 확인 처리 실패:', error);
    }
  } else {
    // 사용자가 'NO'를 선택한 경우 - 터틀봇 복귀 신호 발송 로직 추가 가능 구역
    console.log('물품 불일치: 터틀봇 보관함 복귀 명령 전송');
  }

  // 최종 결과 안내 4단계 화면으로 전환 및 카운트다운 시작
  currentStep.value = 4;
  startCountdown();
};

// [4단계] 자동 초기화를 위한 카운트다운 타이머 구동 함수
const startCountdown = () => {
  countdown.value = 5;
  timer = setInterval(() => {
    countdown.value--;
    if (countdown.value <= 0) {
      resetKiosk();
    }
  }, 1000);
};

// 키오스크 모든 상태 초기화 후 1단계 첫 화면으로 이동하는 함수
const resetKiosk = () => {
  if (timer) clearInterval(timer);
  currentStep.value = 1;
  reportId.value = '';
  verificationCode.value = '';
  isConfirmed.value = false;
};

// 컴포넌트 소멸 시 타이머 해제 안전 장치
onBeforeUnmount(() => {
  if (timer) clearInterval(timer);
});
</script>

<style scoped>
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
.kiosk-header {
  border-bottom: 3px solid #333;
  padding-bottom: 20px;
  margin-bottom: 30px;
}
.kiosk-header h1 {
  font-size: 32px;
  color: #1a1a1a;
  margin: 0 0 10px 0;
}
.step-indicator {
  font-size: 18px;
  font-weight: bold;
  color: #0275d8;
  margin: 0;
}
.step-box h2 {
  font-size: 24px;
  color: #2c3e50;
  margin-bottom: 25px;
}
.description {
  color: #555;
  font-size: 16px;
}
.notice {
  font-size: 13px;
  color: #e0a800;
  margin-top: 15px;
}
.warning-text {
  color: #d9534f;
  font-weight: bold;
  font-size: 14px;
  margin-bottom: 20px;
}
.form-group {
  margin-top: 30px;
  display: flex;
  justify-content: center;
  gap: 10px;
}
.kiosk-input {
  padding: 15px;
  font-size: 18px;
  border: 2px solid #ccc;
  border-radius: 8px;
  width: 250px;
  text-align: center;
}
.code-input {
  font-size: 24px;
  letter-spacing: 5px;
  font-weight: bold;
}
button {
  font-weight: bold;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: background-color 0.15s, transform 0.1s;
}
button:active {
  transform: scale(0.98);
}
.btn-next, .btn-verify {
  padding: 15px 30px;
  font-size: 18px;
  background-color: #42b983;
  color: white;
}
/* QR 스캔 영역 그래픽 가구색 구색 쌓기 */
.qr-scanner-mock {
  position: relative;
  width: 300px;
  height: 200px;
  background-color: #111;
  margin: 0 auto 20px auto;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}
.mock-text {
  color: #00ff00;
  font-family: monospace;
  font-size: 14px;
  z-index: 2;
}
.laser-line {
  position: absolute;
  width: 100%;
  height: 3px;
  background-color: #ff0000;
  top: 0;
  box-shadow: 0 0 8px #ff0000;
  animation: scan-animation 2s infinite linear;
  z-index: 1;
}
@keyframes scan-animation {
  0% { top: 0%; }
  50% { top: 100%; }
  100% { top: 0%; }
}
/* 로봇 연동 컴포넌트 박스 영역 */
.robot-animation-box {
  background-color: #f8fafc;
  border: 2px dashed #cbd5e1;
  padding: 25px;
  border-radius: 12px;
  margin-bottom: 30px;
}
.turtlebot-mock {
  width: 120px;
  height: 60px;
  background-color: #334155;
  color: white;
  font-weight: bold;
  line-height: 60px;
  border-radius: 30px;
  margin: 0 auto 15px auto;
  animation: robot-move 3s infinite ease-in-out;
}
@keyframes robot-move {
  0% { transform: translateX(-30px); }
  50% { transform: translateX(30px); }
  100% { transform: translateX(-30px); }
}
.robot-status {
  font-size: 15px;
  color: #64748b;
  margin: 0;
}
/* 분기 선택 버튼 그룹 레이아웃 */
.btn-group-row {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 15px;
}
.btn-yes {
  padding: 20px 35px;
  font-size: 20px;
  background-color: #5cb85c;
  color: white;
}
.btn-no {
  padding: 20px 35px;
  font-size: 20px;
  background-color: #d9534f;
  color: white;
}
/* 완료 레이아웃 공통 구성 */
.completion-box {
  padding: 20px 0;
}
.success-message h2 { color: #5cb85c; }
.return-message h2 { color: #d9534f; }
.db-notice {
  font-family: monospace;
  color: #0275d8;
  font-weight: bold;
}
.countdown-zone {
  margin-top: 40px;
  border-top: 1px solid #eee;
  padding-top: 20px;
}
.btn-home {
  padding: 12px 24px;
  background-color: #6c757d;
  color: white;
  margin-top: 10px;
  font-size: 15px;
}
</style>