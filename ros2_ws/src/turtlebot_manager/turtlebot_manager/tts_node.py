"""
TTS 노드 - 터틀봇에서 실행.

/turtlebot/status 토픽을 구독하여 'arrived:return_counter' 수신 시
한국어 음성을 재생한다.
"""

import subprocess
import tempfile
import threading

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

TTS_MESSAGE = '본인의 물건이 맞는지 확인하시고 키오스크의 확인 버튼을 눌러 주세요'


class TTSNode(Node):
    def __init__(self):
        super().__init__('tts_node')

        self._audio_path = self._prepare_audio()

        self._status_sub = self.create_subscription(
            String, '/turtlebot/status', self._on_status, 10
        )
        self.get_logger().info('TTSNode 준비 완료')

    def _prepare_audio(self) -> str | None:
        try:
            from gtts import gTTS
            tmp = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
            gTTS(TTS_MESSAGE, lang='ko').save(tmp.name)
            self.get_logger().info(f'TTS 오디오 생성 완료: {tmp.name}')
            return tmp.name
        except Exception as e:
            self.get_logger().error(f'TTS 오디오 생성 실패: {e}')
            return None

    def _on_status(self, msg: String):
        if msg.data == 'arrived:return_counter':
            self.get_logger().info('반환창구 도착 — TTS 재생')
            self._play()

    def _play(self):
        if not self._audio_path:
            self.get_logger().warn('오디오 파일 없음 - 재생 건너뜀')
            return

        def _run():
            try:
                subprocess.run(['mpg123', '-q', self._audio_path], check=True)
            except FileNotFoundError:
                self.get_logger().error('mpg123 미설치 — sudo apt install mpg123')
            except subprocess.CalledProcessError as e:
                self.get_logger().error(f'재생 오류: {e}')

        threading.Thread(target=_run, daemon=True).start()


def main(args=None):
    rclpy.init(args=args)
    node = TTSNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
