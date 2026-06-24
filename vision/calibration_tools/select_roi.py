"""
카메라 화면에서 마우스로 드래그해서 작업 영역(ROI)을 선택하고 저장.
  드래그 : 영역 선택
  ENTER  : 저장
  r      : 다시 선택
  q      : 종료
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import cv2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

ROI_OUT = os.path.join(os.path.dirname(__file__), '..', 'camera_roi.json')

class Grab(Node):
    def __init__(self):
        super().__init__('roi_selector')
        self.bridge = CvBridge()
        self.latest = None
        self.sub = self.create_subscription(
            Image, '/camera/camera/color/image_raw', self._cb, 10)
    def _cb(self, msg):
        self.latest = self.bridge.imgmsg_to_cv2(msg, 'bgr8')


drawing = False
ix, iy, ex, ey = 0, 0, 0, 0
roi = None

def mouse_cb(event, x, y, flags, param):
    global drawing, ix, iy, ex, ey, roi
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y
    elif event == cv2.EVENT_MOUSEMOVE and drawing:
        ex, ey = x, y
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        ex, ey = x, y
        x1, x2 = min(ix, ex), max(ix, ex)
        y1, y2 = min(iy, ey), max(iy, ey)
        roi = (x1, y1, x2, y2)


def main():
    global roi
    rclpy.init()
    node = Grab()
    print("프레임 수신 대기 중...")
    while node.latest is None:
        rclpy.spin_once(node, timeout_sec=0.1)

    cv2.namedWindow('ROI Selector', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('ROI Selector', 960, 540)
    cv2.setMouseCallback('ROI Selector', mouse_cb)
    print("흰 종이 영역을 드래그로 선택하세요.  ENTER=저장  r=다시  q=종료")

    try:
        while True:
            rclpy.spin_once(node, timeout_sec=0.01)
            frame = node.latest.copy()

            if drawing:
                x1, x2 = min(ix, ex), max(ix, ex)
                y1, y2 = min(iy, ey), max(iy, ey)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            if roi:
                rx1, ry1, rx2, ry2 = roi
                cv2.rectangle(frame, (rx1, ry1), (rx2, ry2), (0, 255, 0), 2)
                cv2.putText(frame, f"({rx1},{ry1})-({rx2},{ry2})  ENTER=save  r=redo",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                crop = node.latest[ry1:ry2, rx1:rx2]
                if crop.size > 0:
                    h, w = frame.shape[:2]
                    ph = h // 3
                    pw = int(ph * crop.shape[1] / max(crop.shape[0], 1))
                    if pw > 0:
                        preview = cv2.resize(crop, (pw, ph))
                        frame[h-ph:h, 0:pw] = preview
                        cv2.putText(frame, "preview", (5, h-ph-5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            else:
                cv2.putText(frame, "Drag to select white paper area",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)

            cv2.imshow('ROI Selector', frame)
            key = cv2.waitKey(1) & 0xFF

            if key == 13 and roi:  # ENTER
                rx1, ry1, rx2, ry2 = roi
                data = {"x1": rx1, "y1": ry1, "x2": rx2, "y2": ry2,
                        "width": rx2-rx1, "height": ry2-ry1}
                with open(ROI_OUT, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"ROI 저장 완료: {ROI_OUT}")
                print(f"  x={rx1}~{rx2}, y={ry1}~{ry2}  ({rx2-rx1}x{ry2-ry1}px)")
                break
            elif key == ord('r'):
                roi = None
            elif key == ord('q'):
                break
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
