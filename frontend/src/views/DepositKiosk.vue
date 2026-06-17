<template>
  <div class="kiosk-container">
    <header class="kiosk-header">
      <h1>🤖 분실물 무인 접수 시스템</h1>
      <p class="step-indicator" v-if="currentStep > 1">단계: {{ currentStep - 1 }} / 2</p>
    </header>

    <main class="kiosk-content">
      <div v-if="currentStep === 1" class="step-box welcome-box" @click="nextStep">
        <div class="welcome-icon">📦</div>
        <h2>따뜻한 마음에 감사드립니다</h2>
        <p class="description main-prompt">길에서 주인 없는 물건을 발견하셨나요?</p>
        <p class="sub-description">화면을 터치하거나 클릭하시면 접수가 시작됩니다.</p>
        <div class="touch-prompt">👉 화면을 터치해 주세요</div>
      </div>

      <div v-if="currentStep === 2" class="step-box stt-box">
        <h2 class="stt-title">🎤 "언제, 어디서, 무엇을" 주우셨나요?</h2>
        <p class="description">습득하신 상황과 물품에 대해 자유롭게 말씀해 주세요.</p>
        <p class="notice">음성 인식이 활성화되어 기록 중입니다.</p>

        <div class="mic-zone">
          <div class="mic-circle" :class="{ 'is-recording': isRecording }">
            <span class="mic-icon">🎙️</span>
          </div>
          <div class="wave-container" v-if="isRecording">
            <span class="bar"></span>
            <span class="bar"></span>
            <span class="bar"></span>
            <span class="bar"></span>
            <span class="bar"></span>
          </div>
          <p class="mock-stt-preview">[ 음성 인식 대기 중... ]</p>
        </div>

        <div class="form-group">
          <button @click="completeRegistration" class="btn-complete">💬 말씀 완료 (접수하기)</button>
        </div>
      </div>

      <div v-if="currentStep === 3" class="step-box completion-box">
        <div class="success-icon">✅</div>
        <h2>접수가 완료되었습니다!</h2>
        
        <div class="conveyor-instruction">
          <p class="instruction-text">🤖 <strong>키오스크 앞의 컨베이어 벨트</strong> 위에 물건을 올려놓아 주세요.</p>
          <div class="conveyor-graphic">
            <div class="arrow-animation">👇</div>
            <div class="belt-line"></div>
          </div>
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

// 단계 관리 (1: 초기화면, 2: 음성인식, 3: 접수완료 및 컨베이어)
const currentStep = ref(1);
const isRecording = ref(false);
const countdown = ref(5);

let timer = null;

// [1단계 -> 2단계] 화면 전환 및 마이크 활성화 시뮬레이션
const nextStep = () => {
  currentStep.value = 2;
  isRecording.value = true;
};

// [2단계 -> 3단계] 음성인식 완료 및 5초 타이머 구동
const completeRegistration = () => {
  isRecording.value = false;
  currentStep.value = 3;
  startCountdown();
};

// [3단계] 자동 복귀 카운트다운 타이머
const startCountdown = () => {
  countdown.value = 5;
  timer = setInterval(() => {
    countdown.value--;
    if (countdown.value <= 0) {
      resetKiosk();
    }
  }, 1000);
};

// 모든 상태 초기화 후 첫 화면으로 이동
const resetKiosk = () => {
  if (timer) clearInterval(timer);
  currentStep.value = 1;
  isRecording.value = false;
  countdown.value = 5;
};

onBeforeUnmount(() => {
  if (timer) clearInterval(timer);
});
</script>

<style scoped>
.kiosk-container {
  max-width: 800px;
  margin: 40px auto;
  padding: 30px;
  border: 4px solid #2b2d42;
  border-radius: 16px;
  background-color: #ffffff;
  box-shadow: 0 10px 25px rgba(0,0,0,0.15);
  font-family: sans-serif;
  text-align: center;
  user-select: none;
}
.kiosk-header {
  border-bottom: 3px solid #2b2d42;
  padding-bottom: 20px;
  margin-bottom: 30px;
}
.kiosk-header h1 {
  font-size: 32px;
  color: #2b2d42;
  margin: 0 0 10px 0;
}
.step-indicator {
  font-size: 18px;
  font-weight: bold;
  color: #ef233c;
  margin: 0;
}
.step-box h2 {
  font-size: 26px;
  color: #2b2d42;
  margin-bottom: 20px;
}
.description {
  color: #4a4e69;
  font-size: 18px;
  margin-bottom: 10px;
}

/* 📦 1단계: 초기 화면 스타일 */
.welcome-box {
  padding: 50px 20px;
  cursor: pointer;
  background-color: #f8f9fa;
  border-radius: 12px;
  transition: background-color 0.2s;
}
.welcome-box:hover {
  background-color: #edf2f4;
}
.welcome-icon {
  font-size: 80px;
  margin-bottom: 20px;
}
.main-prompt {
  font-size: 22px;
  font-weight: bold;
  color: #2b2d42;
}
.sub-description {
  color: #8d99ae;
  font-size: 15px;
  margin-top: 5px;
}
.touch-prompt {
  margin-top: 50px;
  font-size: 20px;
  font-weight: bold;
  color: #ef233c;
  animation: blink 1.5s infinite;
}

/* 🎤 2단계: STT 및 마이크 스타일 */
.stt-title {
  color: #1d3557 !important;
}
.notice {
  font-size: 14px;
  color: #ef233c;
  font-weight: bold;
}
.mic-zone {
  margin: 40px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}
.mic-circle {
  width: 120px;
  height: 120px;
  background-color: #f1faee;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 4px solid #457b9d;
}
.mic-icon {
  font-size: 50px;
}
.is-recording {
  animation: pulse 1.8s infinite ease-in-out;
  border-color: #e63946;
  background-color: #ffe3e3;
}
.mock-stt-preview {
  font-family: monospace;
  color: #457b9d;
  font-size: 16px;
  font-weight: bold;
}
.btn-complete {
  padding: 20px 40px;
  font-size: 22px;
  font-weight: bold;
  background-color: #1d3557;
  color: white;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.1s;
}
.btn-complete:active {
  transform: scale(0.97);
}

/* 🔊 음성 오디오 파형 그래픽 모크 */
.wave-container {
  display: flex;
  align-items: center;
  gap: 4px;
  height: 30px;
}
.wave-container .bar {
  width: 4px;
  height: 100%;
  background-color: #e63946;
  border-radius: 2px;
  animation: wave 1s infinite ease-in-out;
}
.wave-container .bar:nth-child(2) { animation-delay: 0.15s; }
.wave-container .bar:nth-child(3) { animation-delay: 0.3s; }
.wave-container .bar:nth-child(4) { animation-delay: 0.45s; }
.wave-container .bar:nth-child(5) { animation-delay: 0.6s; }

/* ✅ 3단계: 컨베이어 벨트 투입 안내 스타일 */
.success-icon {
  font-size: 70px;
  margin-bottom: 10px;
}
.conveyor-instruction {
  background-color: #f1faee;
  border: 3px dashed #457b9d;
  padding: 30px;
  border-radius: 16px;
  margin: 30px 0;
}
.instruction-text {
  font-size: 20px;
  color: #1d3557;
  margin: 0;
}
.conveyor-graphic {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 20px; /* 텍스트와 그래픽 사이의 여백 추가 */
}
.arrow-animation {
  font-size: 30px;
  margin-bottom: 10px; /* 벨트와의 간격 추가 */
  animation: bounce 1s infinite alternate;
}
.belt-line {
  width: 200px; /* 벨트 길이를 고정하여 중앙 정렬 유지 */
  height: 12px;
  background: repeating-linear-gradient(90deg, #1d3557, #1d3557 15px, #457b9d 15px, #457b9d 30px);
  border-radius: 6px;
  animation: belt-move 1s infinite linear;
}

/* 🕒 하단 공통 카운트다운 레이아웃 */
.countdown-zone {
  margin-top: 40px;
  border-top: 2px solid #edf2f4;
  padding-top: 20px;
}
.btn-home {
  padding: 12px 24px;
  background-color: #6c757d;
  color: white;
  margin-top: 10px;
  font-size: 15px;
  font-weight: bold;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

/* 🎬 애니메이션 정의 키프레임 */
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
@keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(230, 57, 70, 0.5); } 70% { box-shadow: 0 0 0 25px rgba(230, 57, 70, 0); } 100% { box-shadow: 0 0 0 0 rgba(230, 57, 70, 0); } }
@keyframes wave { 0%, 100% { transform: scaleY(0.3); } 50% { transform: scaleY(1); } }
@keyframes bounce { 0% { transform: translateY(0); } 100% { transform: translateY(-10px); } }
@keyframes belt-move { 0% { background-position: 0 0; } 100% { background-position: 30px 0; } }
</style>