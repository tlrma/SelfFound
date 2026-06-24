"""
현재 카메라 프레임을 저장하고 모든 보드 크기를 시도해서 결과를 보여줌.
python3 diagnose.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import cv2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

CANDIDATES = [(7,7),(9,6),(6,9),(8,6),(6,8),(7,5),(5,7),(8,5),(5,8),(6,5),(5,6),(4,7),(7,4)]
OUT = os.path.join(os.path.dirname(__file__), 'diagnose_frame.png')

class Grab(Node):
    def __init__(self):
        super().__init__('grab')
        self.bridge = CvBridge()
        self.frame = None
        self.sub = self.create_subscription(Image, '/camera/camera/color/image_raw', self._cb, 10)
    def _cb(self, msg):
        self.frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')

rclpy.init()
node = Grab()
print("프레임 수신 대기 중...")
while node.frame is None:
    rclpy.spin_once(node, timeout_sec=0.1)

frame = node.frame.copy()
cv2.imwrite(OUT, frame)
print(f"프레임 저장: {OUT}  ({frame.shape[1]}x{frame.shape[0]})")

gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
gray_eq = clahe.apply(gray)

flags = cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_NORMALIZE_IMAGE

print("\n--- 보드 크기 탐색 결과 ---")
found_any = False
for bs in CANDIDATES:
    r1, _ = cv2.findChessboardCorners(gray, bs, flags)
    r2, _ = cv2.findChessboardCorners(gray_eq, bs, flags)
    tag = ""
    if r1: tag = "원본 OK"
    elif r2: tag = "CLAHE OK"
    if r1 or r2:
        print(f"  {bs[0]}x{bs[1]} 내부코너 ({bs[0]+1}x{bs[1]+1} 보드) → {tag}  ★")
        found_any = True
    else:
        print(f"  {bs[0]}x{bs[1]}  → 미감지")

if not found_any:
    print("\n모든 크기에서 감지 실패.")
    print("diagnose_frame.png 를 열어서 체커보드가 잘 보이는지 확인하세요.")

node.destroy_node()
rclpy.shutdown()
