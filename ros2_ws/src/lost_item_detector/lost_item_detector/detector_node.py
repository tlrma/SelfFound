"""
분실물 감지 노드 — RealSense 카메라 실제 사용 버전.

트리거: /item_ready (std_msgs/String) 토픽 수신
흐름:  Modbus Mock(항상 완료) → RealSense 캡처 → VisionPipeline → POST /api/items/
결과:  /detection_result (std_msgs/String, JSON) 퍼블리시

테스트 트리거 방법:
  ros2 topic pub --once /item_ready std_msgs/msg/String "{data: '1층 로비, 오후 2시'}"
"""

import sys
import os
import glob
import json
import cv2
import numpy as np
import requests
from datetime import datetime

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

# vision_path: 환경변수 SELFFOUND_VISION_PATH 또는 기본값
# params.yaml 의 vision_path 와 맞춰서 설정하세요
VISION_PATH = os.environ.get(
    'SELFFOUND_VISION_PATH',
    '/home/ssafy/finalPJT/SelfFound/vision',
)

# .venv site-packages 자동 탐색 (Python 버전 무관)
_venv_sites = glob.glob(os.path.join(VISION_PATH, '.venv/lib/python3*/site-packages'))
if _venv_sites:
    sys.path.insert(0, _venv_sites[0])
sys.path.insert(0, VISION_PATH)
from pipeline.pipeline import VisionPipeline


class ModbusMock:
    """컨베이어 완료 신호 Mock — 항상 완료(True) 반환."""

    def is_conveyor_done(self) -> bool:
        return True


class LostItemDetectorNode(Node):

    def __init__(self):
        super().__init__('lost_item_detector')

        self.declare_parameter('model_path', os.path.join(VISION_PATH, 'best.pt'))
        self.declare_parameter('backend_url', 'http://localhost:8000/api/items/')
        self.declare_parameter('photo_save_dir', '/tmp/lost_items')

        model_path = os.path.abspath(self.get_parameter('model_path').value)
        self.backend_url = self.get_parameter('backend_url').value
        self.photo_dir = self.get_parameter('photo_save_dir').value
        os.makedirs(self.photo_dir, exist_ok=True)

        self.modbus = ModbusMock()
        self.vision = VisionPipeline(model_path=model_path)

        self.sub = self.create_subscription(String, '/item_ready', self.on_item_ready, 10)
        self.result_pub = self.create_publisher(String, '/detection_result', 10)

        self.get_logger().info('LostItemDetector (RealSense) 노드 시작')
        self.get_logger().info(f'모델: {model_path}')
        self.get_logger().info(f'백엔드: {self.backend_url}')

    # ── 콜백 ──────────────────────────────────────────────────────────────

    def on_item_ready(self, msg: String):
        stt_text = msg.data
        self.get_logger().info(f'/item_ready 수신: "{stt_text}"')

        if not self.modbus.is_conveyor_done():
            self.get_logger().warn('Modbus: 컨베이어 미완료 신호 — 처리 건너뜀')
            return
        self.get_logger().info('Modbus: 컨베이어 완료 확인')

        image = self._capture_realsense()
        if image is None:
            return

        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        photo_path = os.path.join(self.photo_dir, f'item_{ts}.jpg')
        cv2.imwrite(photo_path, image)
        self.get_logger().info(f'이미지 저장: {photo_path}')

        result = self.vision.run(image)
        if 'error' in result:
            self.get_logger().error(f'VisionPipeline 오류: {result["error"]}')
            return

        self.get_logger().info(
            f'분류: {result["category"]} (confidence={result["confidence"]:.2f})'
        )
        self._post_to_backend(result, stt_text, photo_path)

    # ── 내부 메서드 ────────────────────────────────────────────────────────

    def _capture_realsense(self):
        try:
            import pyrealsense2 as rs

            pipe = rs.pipeline()
            cfg = rs.config()
            cfg.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
            pipe.start(cfg)

            self.get_logger().info('RealSense 카메라 안정화 중...')
            for _ in range(30):
                pipe.wait_for_frames()

            frames = pipe.wait_for_frames()
            color_frame = frames.get_color_frame()
            image = np.asanyarray(color_frame.get_data())
            pipe.stop()
            return image

        except Exception as e:
            self.get_logger().error(f'RealSense 캡처 실패: {e}')
            return None

    def _post_to_backend(self, result: dict, stt_text: str, photo_path: str):
        payload = {
            'category': result['category'],
            'confidence': result['confidence'],
            'description': result.get('description', ''),
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
    node = LostItemDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
