<template>
  <div class="kiosk-container">
    <header class="kiosk-header">
      <h1>🤖 분실물 무인 접수 시스템</h1>
      <p class="step-indicator" v-if="currentStep > 1 && currentStep < 4">단계: {{ currentStep - 1 }} / 2</p>
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
        <p class="notice" v-if="isRecording">음성 인식이 활성화되어 기록 중입니다.</p>
        <p class="notice-idle" v-else>마이크를 눌러 말씀을 시작해 주세요.</p>

        <div class="mic-zone">
          <button class="mic-circle" :class="{ 'is-recording': isRecording }" @click="toggleRecording">
            <span class="mic-icon">🎙️</span>
          </button>
          <div class="wave-container" v-if="isRecording">
            <span class="bar"></span>
            <span class="bar"></span>
            <span class="bar"></span>
            <span class="bar"></span>
            <span class="bar"></span>
          </div>
        </div>

        <div class="stt-result-box" :class="{ 'has-text': sttText }">
          <p class="stt-result-label">{{ sttText ? '인식된 내용' : '음성 인식 대기 중...' }}</p>
          <p class="stt-result-text" v-if="sttText">{{ sttText }}</p>
        </div>

        <div class="form-group">
          <button @click="completeRegistration" class="btn-complete">💬 말씀 완료 (다음 단계)</button>
        </div>
      </div>

      <div v-if="currentStep === 3" class="step-box instruction-box">
        <h2>물건을 올려놓아 주세요</h2>
        
        <div class="conveyor-instruction">
          <p class="instruction-text">🤖 <strong>키오스크 앞의 컨베이어 벨트</strong> 위에 물건을 올려놓으신 후,<br>아래의 확인 버튼을 눌러주세요.</p>
          <div class="conveyor-graphic">
            <div class="arrow-animation">👇</div>
            <div class="belt-line"></div>
          </div>
        </div>

        <div class="form-group">
          <button @click="confirmAndRunConveyor" class="btn-complete confirm-btn" :disabled="isProcessing">
            {{ isProcessing ? '컨베이어 작동 중...' : '✅ 물건을 올려놓았습니다 (확인)' }}
          </button>
        </div>
      </div>

      <div v-if="currentStep === 4" class="step-box completion-box">
        <div class="success-icon">💖</div>
        <h2>접수가 완벽하게 끝났습니다!</h2>
        <p class="description">소중한 물건을 맡겨주셔서 진심으로 감사드립니다.<br>주인이 꼭 찾을 수 있도록 안전하게 보관하겠습니다.</p>

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

const currentStep = ref(1);
const isRecording = ref(false);
const isProcessing = ref(false);
const countdown = ref(5);
const sttText = ref('');

let timer = null;
let recognition = null;

// Web Speech API 초기화
const initRecognition = () => {
  const SR = window['SpeechRecognition'] || window['webkitSpeechRecognition'];
  if (!SR) return null;
  const r = new SR();
  r.lang = 'ko-KR';
  r.continuous = true;
  r.interimResults = true;
  r.onresult = (e) => {
    let text = '';
    for (const result of e.results) {
      text += result[0].transcript;
    }
    sttText.value = text;
  };
  r.onerror = (e) => {
    if (e.error === 'no-speech') return; // 무음 감지는 무시하고 재시작
    console.error('STT 오류:', e.error);
    isRecording.value = false;
  };
  r.onend = () => {
    // Chrome은 일정 시간 후 자동 중단 → 녹음 중이면 재시작
    if (isRecording.value) recognition?.start();
  };
  return r;
};

const toggleRecording = () => {
  if (isRecording.value) {
    recognition?.stop();
    isRecording.value = false;
  } else {
    recognition = initRecognition();
    if (!recognition) {
      alert('이 브라우저는 음성 인식을 지원하지 않습니다.');
      return;
    }
    sttText.value = '';
    recognition.start();
    isRecording.value = true;
  }
};

// [1단계 → 2단계]
const nextStep = () => {
  currentStep.value = 2;
};

// [2단계 → 3단계]
const completeRegistration = () => {
  recognition?.stop();
  isRecording.value = false;
  currentStep.value = 3;
};

// [3단계 → 4단계] found_info 포함해서 컨베이어 API 호출
const confirmAndRunConveyor = async () => {
  isProcessing.value = true;
  try {
    await fetch('/api/robot_tasks/conveyor/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ found_info: sttText.value }),
    });
  } catch (error) {
    console.error('API 통신 에러:', error);
  } finally {
    isProcessing.value = false;
    currentStep.value = 4;
    startCountdown();
  }
};

const startCountdown = () => {
  countdown.value = 5;
  timer = setInterval(() => {
    countdown.value--;
    if (countdown.value <= 0) resetKiosk();
  }, 1000);
};

const resetKiosk = () => {
  if (timer) clearInterval(timer);
  recognition?.stop();
  currentStep.value = 1;
  isRecording.value = false;
  isProcessing.value = false;
  sttText.value = '';
  countdown.value = 5;
};

onBeforeUnmount(() => {
  if (timer) clearInterval(timer);
  recognition?.stop();
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
  line-height: 1.5;
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
.notice-idle {
  font-size: 14px;
  color: #457b9d;
  font-weight: bold;
}
.mic-circle {
  cursor: pointer;
  border: 4px solid #457b9d;
  background-color: #f1faee;
}
.stt-result-box {
  margin: 20px auto 0;
  width: 100%;
  min-height: 80px;
  border: 2px dashed #cbd5e1;
  border-radius: 12px;
  background: #f8fafc;
  padding: 16px 20px;
  transition: border-color 0.3s, background 0.3s;
}
.stt-result-box.has-text {
  border-color: #2563eb;
  background: #eff6ff;
}
.stt-result-label {
  margin: 0 0 6px;
  font-size: 12px;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.stt-result-box.has-text .stt-result-label {
  color: #2563eb;
}
.stt-result-text {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1e3a5f;
  line-height: 1.5;
  word-break: keep-all;
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
  transition: transform 0.1s, background-color 0.2s;
}
.btn-complete:active {
  transform: scale(0.97);
}
.btn-complete:disabled {
  background-color: #a8dadc;
  cursor: not-allowed;
  transform: none;
}
.confirm-btn {
  background-color: #2a9d8f;
  margin-top: 10px;
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

/* ✅ 3단계 & 4단계: 안내 및 완료 그래픽 스타일 */
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
  line-height: 1.5;
}
.conveyor-graphic {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 20px;
}
.arrow-animation {
  font-size: 30px;
  margin-bottom: 10px;
  animation: bounce 1s infinite alternate;
}
.belt-line {
  width: 200px;
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