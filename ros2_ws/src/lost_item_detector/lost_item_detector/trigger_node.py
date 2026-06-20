"""
라즈베리파이 트리거 노드.

흐름: GPIO 버튼 감지 → 음성 녹음 → STT → /item_ready 토픽 발행

실행:
  ros2 run lost_item_detector trigger_node

의존성 (라즈베리파이에서 설치):
  pip install RPi.GPIO sounddevice faster-whisper numpy
  # Whisper API 방식 사용 시: pip install requests
"""

import time
import threading
import numpy as np

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

# ── GPIO 설정 ──────────────────────────────────────────────────────────────────
# 핀 번호는 BCM 기준 (GPIO.setmode(GPIO.BCM))
BUTTON_PIN = 23          # ← [수정] 버튼 GPIO 핀 번호 (Button 1: 23, Button 2: 24)
BUTTON_BOUNCE_MS = 300   # 디바운스 시간 (ms)

# ── 오디오 설정 ────────────────────────────────────────────────────────────────
SAMPLE_RATE  = 16000     # Whisper 권장 샘플링 레이트
RECORD_SEC   = 5         # ← [수정] 버튼 누른 후 녹음할 초
CHANNELS     = 1

# ── STT 설정 ──────────────────────────────────────────────────────────────────
# [방식 1] faster-whisper 로컬 모델 (오프라인, 라즈베리파이 권장)
WHISPER_MODEL_SIZE = "base"   # ← [수정] tiny / base / small 중 선택
                               #   tiny: 가장 빠름, 정확도 낮음
                               #   base: 속도·정확도 균형 (권장)
                               #   small: 정확도 높음, 느림

# [방식 2] OpenAI Whisper API (온라인, GMS 사용 가능)
# GMS_KEY = os.environ.get("GMS_KEY")
# WHISPER_API_URL = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/audio/transcriptions"


class TriggerNode(Node):

    def __init__(self):
        super().__init__('item_trigger')

        self.pub = self.create_publisher(String, '/item_ready', 10)
        self.get_logger().info('TriggerNode 시작 — 버튼 대기 중')

        # faster-whisper 모델 로드 (처음 실행 시 다운로드)
        self._load_whisper()

        # GPIO 초기화 (라즈베리파이에서만 동작)
        self._setup_gpio()

    # ── 초기화 ────────────────────────────────────────────────────────────────

    def _load_whisper(self):
        try:
            from faster_whisper import WhisperModel
            self.get_logger().info(f'Whisper 모델 로드 중 ({WHISPER_MODEL_SIZE})...')
            # device="cpu", compute_type="int8" → 라즈베리파이 최적화
            self.whisper = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
            self.get_logger().info('Whisper 모델 로드 완료')
        except ImportError:
            self.get_logger().error('faster-whisper 미설치: pip install faster-whisper')
            self.whisper = None

    def _setup_gpio(self):
        try:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            # 버튼 누름(FALLING) 감지 → 콜백
            GPIO.add_event_detect(
                BUTTON_PIN,
                GPIO.FALLING,
                callback=self._on_button_pressed,
                bouncetime=BUTTON_BOUNCE_MS,
            )
            self.get_logger().info(f'GPIO {BUTTON_PIN}번 핀 감지 대기 중')
        except (ImportError, RuntimeError) as e:
            self.get_logger().warn(f'GPIO 초기화 실패 (라즈베리파이 아닌 환경): {e}')
            self.GPIO = None

    # ── 콜백 ──────────────────────────────────────────────────────────────────

    def _on_button_pressed(self, channel):
        # GPIO 콜백은 별도 스레드에서 실행되므로 threading으로 처리
        self.get_logger().info(f'버튼 감지 (GPIO {channel})')
        threading.Thread(target=self._record_and_publish, daemon=True).start()

    def _record_and_publish(self):
        try:
            stt_text = self._record_and_transcribe()
            if not stt_text:
                self.get_logger().warn('STT 결과 없음 — 토픽 발행 건너뜀')
                return
            self.get_logger().info(f'STT 결과: "{stt_text}"')
            self.pub.publish(String(data=stt_text))
            self.get_logger().info('/item_ready 발행 완료')
        except Exception as e:
            self.get_logger().error(f'처리 중 오류: {e}')

    # ── STT ───────────────────────────────────────────────────────────────────

    def _record_and_transcribe(self) -> str:
        """마이크 녹음 후 STT 실행. 결과 문자열 반환."""
        audio = self._record_audio()

        # [방식 1] faster-whisper 로컬 추론
        return self._transcribe_local(audio)

        # [방식 2] OpenAI Whisper API 사용 시 아래로 교체
        # return self._transcribe_api(audio)

    def _record_audio(self) -> np.ndarray:
        import sounddevice as sd
        self.get_logger().info(f'녹음 시작 ({RECORD_SEC}초)...')
        audio = sd.rec(
            int(RECORD_SEC * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype='float32',
        )
        sd.wait()
        self.get_logger().info('녹음 완료')
        return audio.flatten()

    def _transcribe_local(self, audio: np.ndarray) -> str:
        """faster-whisper로 로컬 STT."""
        if self.whisper is None:
            return ""
        segments, _ = self.whisper.transcribe(audio, language="ko")
        return " ".join(seg.text.strip() for seg in segments)

    # def _transcribe_api(self, audio: np.ndarray) -> str:
    #     """OpenAI Whisper API (GMS) 사용 시."""
    #     import io, wave, requests
    #     buf = io.BytesIO()
    #     with wave.open(buf, 'wb') as wf:
    #         wf.setnchannels(CHANNELS)
    #         wf.setsampwidth(2)
    #         wf.setframerate(SAMPLE_RATE)
    #         wf.writeframes((audio * 32767).astype(np.int16).tobytes())
    #     buf.seek(0)
    #     resp = requests.post(
    #         WHISPER_API_URL,
    #         headers={"Authorization": f"Bearer {GMS_KEY}"},
    #         files={"file": ("audio.wav", buf, "audio/wav")},
    #         data={"model": "whisper-1", "language": "ko"},
    #     )
    #     resp.raise_for_status()
    #     return resp.json().get("text", "")

    # ── 종료 ──────────────────────────────────────────────────────────────────

    def destroy_node(self):
        if self.GPIO:
            self.GPIO.cleanup()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = TriggerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
