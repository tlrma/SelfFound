"""
분실물 감지 노드 — 이미지 파일 Mock 버전 (RealSense 없이 테스트).

트리거: /item_ready (std_msgs/String) 토픽 수신
흐름:  Modbus Mock(항상 완료) → 파일 이미지 로드 → VisionPipeline → POST /api/items/
결과:  /detection_result (std_msgs/String, JSON) 퍼블리시

실행 예시:
  ros2 run lost_item_detector detector_node_mock \
    --ros-args -p image_path:=/path/to/test.jpg

테스트 트리거:
  ros2 topic pub --once /item_ready std_msgs/msg/String "{data: '1층 로비, 오후 2시'}"
"""

import sys
import os
import json
import cv2
import requests

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

VISION_PATH = '/home/ssafy/finalPJT/SelfFound/vision'
VISION_VENV_SITE = '/home/ssafy/finalPJT/SelfFound/vision/.venv/lib/python3.10/site-packages'
sys.path.insert(0, VISION_VENV_SITE)
sys.path.insert(0, VISION_PATH)
from pipeline.pipeline import VisionPipeline


class ModbusMock:
    """컨베이어 완료 신호 Mock — 항상 완료(True) 반환."""

    def is_conveyor_done(self) -> bool:
        return True


class LostItemDetectorMockNode(Node):

    def __init__(self):
        super().__init__('lost_item_detector_mock')

        self.declare_parameter('model_path', os.path.join(VISION_PATH, 'best.pt'))
        self.declare_parameter('backend_url', 'http://localhost:8000/api/items/')
        self.declare_parameter('image_path', '')

        model_path = os.path.abspath(self.get_parameter('model_path').value)
        self.backend_url = self.get_parameter('backend_url').value
        self.image_path = self.get_parameter('image_path').value

        self.modbus = ModbusMock()
        self.vision = VisionPipeline(model_path=model_path)

        self.sub = self.create_subscription(String, '/item_ready', self.on_item_ready, 10)
        self.result_pub = self.create_publisher(String, '/detection_result', 10)

        self.get_logger().info('LostItemDetector (Mock 이미지) 노드 시작')
        self.get_logger().info(f'모델: {model_path}')
        self.get_logger().info(f'백엔드: {self.backend_url}')

        if self.image_path:
            self.get_logger().info(f'테스트 이미지: {self.image_path}')
        else:
            self.get_logger().warn(
                'image_path 파라미터 미설정. '
                '--ros-args -p image_path:=/path/to/image.jpg 로 지정하세요.'
            )

    # ── 콜백 ──────────────────────────────────────────────────────────────

    def on_item_ready(self, msg: String):
        stt_text = msg.data
        self.get_logger().info(f'/item_ready 수신: "{stt_text}"')

        if not self.modbus.is_conveyor_done():
            self.get_logger().warn('Modbus: 컨베이어 미완료 신호 — 처리 건너뜀')
            return
        self.get_logger().info('Modbus: 컨베이어 완료 확인 (Mock)')

        image = self._load_image()
        if image is None:
            return

        result = self.vision.run(image)
        if 'error' in result:
            self.get_logger().error(f'VisionPipeline 오류: {result["error"]}')
            return

        self.get_logger().info(
            f'분류: {result["category"]} (confidence={result["confidence"]:.2f})'
        )
        self._post_to_backend(result, stt_text, self.image_path)

    # ── 내부 메서드 ────────────────────────────────────────────────────────

    def _load_image(self):
        if not self.image_path:
            self.get_logger().error('image_path 파라미터가 비어 있습니다.')
            return None
        image = cv2.imread(self.image_path)
        if image is None:
            self.get_logger().error(f'이미지 로드 실패: {self.image_path}')
        return image

    def _post_to_backend(self, result: dict, stt_text: str, photo_path: str):
        colors = ', '.join(c['name'] for c in result.get('colors', []))
        payload = {
            'category': result['category'],
            'confidence': result['confidence'],
            'description': f'색상: {colors}',
            'photo_path': photo_path,
            'found_location': stt_text,
        }
        try:
            resp = requests.post(self.backend_url, json=payload, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            item_id = data.get('item', {}).get('id', '?')
            self.get_logger().info(f'백엔드 저장 완료 (item_id={item_id})')
            self.result_pub.publish(String(data=json.dumps(data.get('item', {}))))
        except Exception as e:
            self.get_logger().error(f'백엔드 POST 실패: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = LostItemDetectorMockNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
