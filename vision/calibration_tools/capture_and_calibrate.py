"""
체커보드 캡처 + 캘리브레이션.
  [SPACE] 캡처  [d] 삭제  [c] 캘리브레이션  [q] 종료
"""

import sys, os, threading
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

from pipeline.calibration import calibrate_camera, save_calibration

BOARD_SIZE_CANDIDATES = [(7,7),(9,6),(6,9),(7,5),(5,7),(8,5),(5,8),(6,5),(5,6)]
SQUARE_SIZE_MM = 10.0
DETECT_SCALE   = 1.0   # 축소 없음 (체커보드가 작을 경우 축소하면 안 됨)
SAVE_DIR  = os.path.join(os.path.dirname(__file__), 'captured_images')
CALIB_OUT = os.path.join(os.path.dirname(__file__), '..', 'camera_calib.json')
os.makedirs(SAVE_DIR, exist_ok=True)


class Detector:
    """백그라운드 스레드에서 체커보드 검출."""
    def __init__(self):
        self.lock = threading.Lock()
        self._gray = None
        self._result = (False, None, None)   # (detected, corners_full_scale, board_size)
        self.board_size = None               # 한 번 찾으면 고정
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def update(self, gray):
        with self.lock:
            self._gray = gray.copy()

    def get(self):
        with self.lock:
            return self._result

    def _run(self):
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        flags = (cv2.CALIB_CB_ADAPTIVE_THRESH |
                 cv2.CALIB_CB_NORMALIZE_IMAGE |
                 cv2.CALIB_CB_FAST_CHECK)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

        while True:
            with self.lock:
                gray = self._gray

            if gray is None:
                continue

            # 축소해서 검출
            small = cv2.resize(gray, None, fx=DETECT_SCALE, fy=DETECT_SCALE)
            candidates = [self.board_size] if self.board_size else BOARD_SIZE_CANDIDATES

            found, corners_small, found_size = False, None, None
            for bs in candidates:
                ret, c = cv2.findChessboardCorners(small, bs, flags)
                if not ret:
                    ret, c = cv2.findChessboardCorners(clahe.apply(small), bs, flags)
                if ret:
                    found, corners_small, found_size = True, c, bs
                    break

            if found:
                # 원본 해상도로 코너 복원 후 서브픽셀 정밀화
                corners_full = corners_small / DETECT_SCALE
                corners_full = cv2.cornerSubPix(
                    gray, corners_full, (11, 11), (-1, -1), criteria)
                if not self.board_size:
                    self.board_size = found_size
                    print(f"  보드 크기 고정: {found_size[0]}x{found_size[1]} 내부 코너")
                with self.lock:
                    self._result = (True, corners_full, found_size)
            else:
                with self.lock:
                    self._result = (False, None, self.board_size or BOARD_SIZE_CANDIDATES[0])


class CalibCapture(Node):
    def __init__(self):
        super().__init__('calib_capture')
        self.bridge = CvBridge()
        self.latest_frame = None
        self.captured_paths = []
        self.sub = self.create_subscription(
            Image, '/camera/camera/color/image_raw', self._cb, 10)

    def _cb(self, msg):
        self.latest_frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')


def draw_status(frame, n_captured, detected, board_size):
    h, w = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, h-80), (w, h), (0,0,0), -1)
    cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

    color = (0,255,0) if detected else (0,100,255)
    size_str = f"{board_size[0]}x{board_size[1]}" if board_size else "?"
    status = f"DETECTED ({size_str})" if detected else f"NOT DETECTED | trying {size_str}"
    cv2.putText(frame, "[SPACE] Capture  [d] Delete  [c] Calibrate  [q] Quit",
                (10, h-55), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200,200,200), 1)
    cv2.putText(frame, f"Captured: {n_captured}    {status}",
                (10, h-25), cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)


def main():
    rclpy.init()
    node = CalibCapture()
    detector = Detector()

    cv2.namedWindow('Calibration Capture', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Calibration Capture', 960, 540)

    capture_idx = 0

    try:
        while True:
            rclpy.spin_once(node, timeout_sec=0.01)

            if node.latest_frame is None:
                continue

            frame = node.latest_frame.copy()
            gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            detector.update(gray)

            detected, corners, board_size = detector.get()
            if detected and corners is not None:
                cv2.drawChessboardCorners(frame, board_size, corners, True)

            draw_status(frame, len(node.captured_paths), detected, board_size)
            cv2.imshow('Calibration Capture', frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break

            elif key == ord(' '):
                if not detected:
                    print("  감지 안 됨. 위치 조정하세요.")
                else:
                    path = os.path.join(SAVE_DIR, f'calib_{capture_idx:03d}.png')
                    cv2.imwrite(path, node.latest_frame)
                    node.captured_paths.append(path)
                    capture_idx += 1
                    print(f"  저장: {os.path.basename(path)} ({len(node.captured_paths)}장)")

            elif key == ord('d'):
                if node.captured_paths:
                    removed = node.captured_paths.pop()
                    os.remove(removed)
                    print(f"  삭제: {os.path.basename(removed)} ({len(node.captured_paths)}장)")

            elif key == ord('c'):
                if len(node.captured_paths) < 5:
                    print(f"  최소 5장 필요 (현재 {len(node.captured_paths)}장)")
                elif not detector.board_size:
                    print("  먼저 체커보드를 감지해주세요.")
                else:
                    print(f"\n캘리브레이션 ({len(node.captured_paths)}장)...")
                    try:
                        result = calibrate_camera(
                            node.captured_paths, detector.board_size, SQUARE_SIZE_MM)
                        save_calibration(result, CALIB_OUT)
                        print(f"완료! 재투영 오차: {result['reprojection_error']} px")
                        if result['reprojection_error'] > 1.0:
                            print("  경고: 오차 큼. 더 다양한 각도로 재촬영 권장.")
                    except Exception as e:
                        print(f"  실패: {e}")

    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
