"""
분실물 감지 노드 — RealSense 카메라 실제 사용 버전.

흐름:  Modbus reg[1]=1 감지 → RealSense 캡처 → VisionPipeline → POST /api/items/
       완료 후 reg[1]=0, /dobot_task_targets 퍼블리시 (Dobot 직접 트리거)
결과:  /detection_result (std_msgs/String, JSON) 퍼블리시

Modbus 레지스터:
  reg[0]  컨베이어   0=대기  1=활성
  reg[1]  RealSense  0=대기  1=활성   ← 이 노드가 감시
"""

import sys
import os
import glob
import json
import base64
import cv2
import numpy as np
import requests

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from pymodbus.client.sync import ModbusTcpClient

VISION_PATH = os.environ.get(
    'SELFFOUND_VISION_PATH',
    '/home/ssafy/finalPJT/SelfFound/vision',
)

_venv_sites = glob.glob(os.path.join(VISION_PATH, '.venv/lib/python3*/site-packages'))
if _venv_sites:
    sys.path.insert(0, _venv_sites[0])
sys.path.insert(0, VISION_PATH)
from pipeline.pipeline import VisionPipeline

MODBUS_HOST = os.environ.get('MODBUS_HOST', 'localhost')
MODBUS_PORT = int(os.environ.get('MODBUS_PORT', 5020))

REG_REALSENSE = 1


class LostItemDetectorNode(Node):

    def __init__(self):
        super().__init__('lost_item_detector')

        self.declare_parameter('model_path', os.path.join(VISION_PATH, 'best.pt'))
        self.declare_parameter('backend_url', 'http://192.168.110.119:8000/api/items/')
        self.declare_parameter('alert_url', 'http://192.168.110.119:8000/api/admin_panel/alerts/')
        self.declare_parameter('poll_interval', 0.5)

        model_path       = os.path.abspath(self.get_parameter('model_path').value)
        self.backend_url = self.get_parameter('backend_url').value
        self.alert_url   = self.get_parameter('alert_url').value
        poll_interval    = self.get_parameter('poll_interval').value

        # 캘리브레이션 · ROI · Homography 로드
        from pipeline.calibration import load_calibration
        from pipeline.homography import load_homography

        calib_path = os.path.join(VISION_PATH, 'camera_calib.json')
        homo_path  = os.path.join(VISION_PATH, 'homography.json')
        roi_path   = os.path.join(VISION_PATH, 'camera_roi.json')

        calib = load_calibration(calib_path) if os.path.exists(calib_path) else None
        H     = load_homography(homo_path)   if os.path.exists(homo_path)  else None
        self._roi = json.load(open(roi_path)) if os.path.exists(roi_path) else None

        self.vision = VisionPipeline(
            model_path=model_path,
            calibration=calib,
            homography=H,
            conf_threshold=0.3,
        )
        self.get_logger().info(f'캘리브레이션: {"로드됨" if calib else "없음"}')
        self.get_logger().info(f'Homography: {"로드됨" if H is not None else "없음"}')
        self.get_logger().info(f'ROI: {self._roi if self._roi else "없음"}')
        self.result_pub = self.create_publisher(String, '/detection_result', 10)

        self.modbus = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT, timeout=3)
        self.modbus.connect()

        self._busy = False
        self._retry_count = 0
        self._max_retries = 3
        self._retry_delay = 2.0
        self._pending_found_info = ''

        # /item_ready 토픽으로 found_info 수신 + 직접 트리거 가능
        self.create_subscription(String, '/item_ready', self._on_item_ready, 10)
        self.create_timer(poll_interval, self._poll_modbus)

        self.get_logger().info('LostItemDetector 노드 시작')
        self.get_logger().info(f'모델: {model_path}')
        self.get_logger().info(f'백엔드: {self.backend_url}')
        self.get_logger().info(f'Modbus: {MODBUS_HOST}:{MODBUS_PORT}  폴링 주기: {poll_interval}s')
        self.get_logger().info('트리거: ros2 topic pub --once /item_ready std_msgs/msg/String "{data: \'장소 시간\'}"')

    # ── /item_ready 토픽 콜백 ────────────────────────────────────────────────

    def _on_item_ready(self, msg: String):
        self._pending_found_info = msg.data
        self.get_logger().info(f'/item_ready 수신: "{msg.data}" → reg[1]=1')
        self._set_reg(REG_REALSENSE, 1)

    # ── Modbus 폴링 ───────────────────────────────────────────────────────────

    def _poll_modbus(self):
        if self._busy:
            return
        try:
            result = self.modbus.read_holding_registers(REG_REALSENSE, 1)
            if result.isError() or not hasattr(result, 'registers'):
                self.get_logger().warn(f'Modbus 읽기 오류: {result} — 재연결 시도')
                self.modbus.close()
                self.modbus.connect()
                return
            if result.registers[0] != 1:
                return
        except Exception as e:
            self.get_logger().warn(f'Modbus 읽기 실패: {e} — 재연결 시도')
            self.modbus.close()
            self.modbus.connect()
            return

        self._busy = True
        self.get_logger().info('reg[1]=1 감지 → RealSense 캡처 시작')

        image = self._capture_realsense()
        if image is None:
            self._set_reg(REG_REALSENSE, 0)
            self._busy = False
            return

        result = self.vision.run(image)
        if 'error' in result:
            self._retry_count += 1
            self.get_logger().warn(
                f'VisionPipeline 오류: {result["error"]} '
                f'({self._retry_count}/{self._max_retries}회 재시도)'
            )
            if self._retry_count < self._max_retries:
                import time
                time.sleep(self._retry_delay)
                self._busy = False  # 다음 폴링 주기에 재시도
                self._set_reg(REG_REALSENSE, 1)  # reg[1] 다시 1로
            else:
                self.get_logger().error(f'최대 재시도 횟수 초과 — 이번 물건 건너뜀')
                self._retry_count = 0
                self._set_reg(REG_REALSENSE, 0)
                self._post_alert(
                    f'VisionPipeline 최대 재시도 초과: {result["error"]} — 물건을 인식하지 못해 건너뜀'
                )
                self._busy = False
            return

        self._retry_count = 0
        self.get_logger().info(
            f'분류: {result["category"]} (confidence={result["confidence"]:.2f})'
        )
        self._post_to_backend(result, image)

        self._set_reg(REG_REALSENSE, 0)
        self.get_logger().info('감지 완료 — reg[1]=0, 백엔드가 Dobot 트리거')
        self._busy = False

    # ── 내부 메서드 ────────────────────────────────────────────────────────────

    def _set_reg(self, address: int, value: int):
        try:
            self.modbus.write_register(address, value)
        except Exception as e:
            self.get_logger().warn(f'Modbus 쓰기 실패 reg[{address}]={value}: {e}')

    def _post_alert(self, message: str, level: str = 'error'):
        try:
            requests.post(
                self.alert_url,
                json={'message': message, 'level': level, 'source': 'detector_node'},
                timeout=5,
            )
        except Exception as e:
            self.get_logger().warn(f'알림 전송 실패: {e}')

    def _capture_realsense(self):
        try:
            import pyrealsense2 as rs

            pipe = rs.pipeline()
            cfg = rs.config()
            cfg.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
            pipe.start(cfg)

            self.get_logger().info('RealSense 카메라 안정화 중...')
            for _ in range(30):
                pipe.wait_for_frames()

            frames = pipe.wait_for_frames()
            color_frame = frames.get_color_frame()
            image = np.asanyarray(color_frame.get_data())
            pipe.stop()

            # ROI 크롭
            if self._roi:
                r = self._roi
                image = image[r['y1']:r['y2'], r['x1']:r['x2']]

            return image

        except Exception as e:
            self.get_logger().error(f'RealSense 캡처 실패: {e}')
            return None

    def _post_to_backend(self, result: dict, image: np.ndarray):
        _, buf = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 70])
        image_b64 = base64.b64encode(buf.tobytes()).decode('utf-8')

        # Homography 미캘리브레이션 시 임시 고정 좌표 사용
        FIXED_DOBOT_XYZ = (200.0, 0.0, 50.0)  # mm, 실제 캘리브레이션 후 교체
        dobot_xyz = result.get('dobot_xyz') or FIXED_DOBOT_XYZ
        self.get_logger().info(f'Dobot 좌표: {dobot_xyz}')

        payload = {
            'category':    result['category'],
            'confidence':  result['confidence'],
            'description': result.get('description', ''),
            'image_b64':   image_b64,
            'found_info':  self._pending_found_info,
            'dobot':       {'x': dobot_xyz[0], 'y': dobot_xyz[1], 'z': dobot_xyz[2]},
        }
        self._pending_found_info = ''  # 전송 후 초기화
        try:
            resp = requests.post(self.backend_url, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            item_id = data.get('item', {}).get('id', '?')
            self.get_logger().info(f'백엔드 저장 완료 (item_id={item_id})')
            self.result_pub.publish(String(data=json.dumps(data.get('item', {}))))
        except Exception as e:
            self.get_logger().error(f'백엔드 POST 실패: {e}')

    def destroy_node(self):
        self.modbus.close()
        super().destroy_node()


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
