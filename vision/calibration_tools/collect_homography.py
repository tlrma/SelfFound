"""
픽셀 ↔ Dobot 좌표 대응점 수집 → Homography 행렬 계산.

절차:
  1. 두봇 팁을 작업 영역 임의 위치로 이동 (제어판 or 수동)
  2. 카메라 화면에서 팁 위치를 마우스로 클릭
  3. 두봇 XY는 /dobot_pose_raw 에서 자동 수신
  4. 6쌍 이상 모으면 [h] 눌러 Homography 계산

키:
  클릭  : 현재 두봇 위치와 클릭 픽셀을 대응점으로 등록
  [u]   : 마지막 대응점 삭제
  [h]   : Homography 계산 및 저장 (6쌍 이상 필요)
  [q]   : 종료
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Float64MultiArray
from cv_bridge import CvBridge

from pipeline.homography import compute_homography, save_homography, reprojection_error

HOMO_OUT = os.path.join(os.path.dirname(__file__), '..', 'homography.json')
ROI_PATH = os.path.join(os.path.dirname(__file__), '..', 'camera_roi.json')

_roi = json.load(open(ROI_PATH)) if os.path.exists(ROI_PATH) else None
if _roi:
    print(f"ROI 적용: x={_roi['x1']}~{_roi['x2']}, y={_roi['y1']}~{_roi['y2']}")
else:
    print("ROI 없음 — 전체 이미지 사용")


class CalibNode(Node):
    def __init__(self):
        super().__init__('homo_calib')
        self.bridge = CvBridge()
        self.frame = None
        self.dobot_xy = None  # (x, y) mm

        self.create_subscription(Image, '/camera/camera/color/image_raw', self._img_cb, 10)
        self.create_subscription(Float64MultiArray, '/dobot_pose_raw', self._pose_cb, 10)

    def _img_cb(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        if _roi:
            frame = frame[_roi['y1']:_roi['y2'], _roi['x1']:_roi['x2']]
        self.frame = frame

    def _pose_cb(self, msg):
        # dobot_pose_raw: [x, y, z, r] (mm)
        if len(msg.data) >= 2:
            self.dobot_xy = (round(msg.data[0] * 1000, 3), round(msg.data[1] * 1000, 3))


pixel_points = []
dobot_points = []
last_click = None

def mouse_cb(event, x, y, flags, param):
    global last_click
    if event == cv2.EVENT_LBUTTONDOWN:
        last_click = (x, y)


def draw_overlay(frame, node, last_click_consumed):
    h, w = frame.shape[:2]
    n = len(pixel_points)

    # 기존 대응점 표시
    for i, (px, py) in enumerate(pixel_points):
        cv2.circle(frame, (px, py), 6, (0, 200, 255), -1)
        cv2.putText(frame, str(i+1), (px+8, py+5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 1)

    # 두봇 현재 위치
    dobot_str = f"Dobot XY: {node.dobot_xy[0]:.1f}, {node.dobot_xy[1]:.1f} mm" \
        if node.dobot_xy else "Dobot: 미수신 (두봇 연결 확인)"
    dobot_color = (0, 255, 0) if node.dobot_xy else (0, 100, 255)

    # 하단 상태바
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, h-90), (w, h), (0,0,0), -1)
    cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
    cv2.putText(frame, "[Click] Add point  [u] Undo  [h] Calc homography  [q] Quit",
                (10, h-65), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,200), 1)
    cv2.putText(frame, dobot_str,
                (10, h-40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, dobot_color, 2)
    cv2.putText(frame, f"Points: {n}/6+",
                (10, h-12), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                (0,255,0) if n >= 6 else (200,200,200), 2)


def main():
    global last_click

    rclpy.init()
    node = CalibNode()

    print("카메라·두봇 연결 대기 중...")
    while node.frame is None:
        rclpy.spin_once(node, timeout_sec=0.1)
    print("연결됨. 두봇 팁을 작업 영역으로 이동 후 화면에서 클릭하세요.")

    cv2.namedWindow('Homography Calibration', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Homography Calibration', 960, 540)
    cv2.setMouseCallback('Homography Calibration', mouse_cb)

    try:
        while True:
            rclpy.spin_once(node, timeout_sec=0.01)
            if node.frame is None:
                continue

            frame = node.frame.copy()

            # 클릭 처리
            if last_click is not None:
                if node.dobot_xy is None:
                    print("  두봇 좌표 미수신. /dobot_pose_raw 토픽 확인하세요.")
                else:
                    px, py = last_click
                    dx, dy = node.dobot_xy
                    pixel_points.append((px, py))
                    dobot_points.append((dx, dy))
                    print(f"  #{len(pixel_points)}  픽셀({px},{py}) → Dobot({dx:.1f},{dy:.1f}mm)")
                last_click = None

            draw_overlay(frame, node, False)
            cv2.imshow('Homography Calibration', frame)
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break

            elif key == ord('u'):
                if pixel_points:
                    pp = pixel_points.pop()
                    dp = dobot_points.pop()
                    print(f"  삭제: 픽셀{pp} → Dobot{dp}  (남은 {len(pixel_points)}쌍)")

            elif key == ord('h'):
                if len(pixel_points) < 4:
                    print(f"  최소 4쌍 필요 (현재 {len(pixel_points)}쌍, 6쌍 이상 권장)")
                else:
                    print(f"\nHomography 계산 중 ({len(pixel_points)}쌍)...")
                    H = compute_homography(pixel_points, dobot_points)
                    err = reprojection_error(pixel_points, dobot_points, H)
                    save_homography(H, HOMO_OUT)

                    # 대응점도 함께 저장 (나중에 재계산 가능)
                    pts_path = HOMO_OUT.replace('.json', '_points.json')
                    with open(pts_path, 'w') as f:
                        json.dump({"pixel": pixel_points, "dobot": dobot_points}, f, indent=2)

                    print(f"\n완료! 평균 오차: {err:.2f} mm")
                    print(f"저장: {HOMO_OUT}")
                    if err > 5.0:
                        print("  경고: 오차가 큽니다. 더 많은 점을 추가하거나 재수집하세요.")

    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
