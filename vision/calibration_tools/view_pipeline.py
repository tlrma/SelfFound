"""
카메라 → 파이프라인 단계별 시각화.
  [s] 현재 파이프라인 실행 & 결과 출력
  [q] 종료
"""
import sys, os, glob
sys.path.insert(0, '/home/ssafy/finalPJT/SelfFound/vision')
_venv = glob.glob('/home/ssafy/finalPJT/SelfFound/vision/.venv/lib/python3*/site-packages')
if _venv:
    sys.path.insert(0, _venv[0])

import cv2
import numpy as np
import pyrealsense2 as rs

from pipeline.inference import LostItemDetector
from pipeline.calibration import load_calibration, undistort

MODEL_PATH = '/home/ssafy/finalPJT/SelfFound/vision/best.pt'
CALIB_PATH = '/home/ssafy/finalPJT/SelfFound/vision/camera_calib.json'
ROI_PATH   = '/home/ssafy/finalPJT/SelfFound/vision/camera_roi.json'

# 캘리브레이션 로드
calib = load_calibration(CALIB_PATH) if os.path.exists(CALIB_PATH) else None
print(f"캘리브레이션: {'로드됨' if calib else '없음'}")

roi = None
if os.path.exists(ROI_PATH):
    import json
    roi = json.load(open(ROI_PATH))
    print(f"ROI: x={roi['x1']}~{roi['x2']}, y={roi['y1']}~{roi['y2']}")
else:
    print("ROI: 없음")

detector = LostItemDetector(MODEL_PATH)
print(f"YOLO 모델 로드 완료\n")
print("[s] 파이프라인 실행  [q] 종료")

pipe = rs.pipeline()
cfg  = rs.config()
cfg.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
pipe.start(cfg)

# 안정화
for _ in range(10):
    pipe.wait_for_frames()

cv2.namedWindow('원본', cv2.WINDOW_NORMAL)
cv2.namedWindow('ROI 크롭 + YOLO', cv2.WINDOW_NORMAL)

try:
    while True:
        frames = pipe.wait_for_frames()
        frame  = np.asanyarray(frames.get_color_frame().get_data())

        # 1. 왜곡 보정
        if calib:
            frame_ud = undistort(frame, calib)
        else:
            frame_ud = frame

        # 2. ROI 크롭
        if roi:
            cropped = frame_ud[roi['y1']:roi['y2'], roi['x1']:roi['x2']]
        else:
            cropped = frame_ud

        # 표시
        cv2.imshow('원본', frame)

        disp_crop = cropped.copy()
        cv2.putText(disp_crop, "ROI crop  [s]=YOLO run  [q]=quit",
                    (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
        cv2.imshow('ROI 크롭 + YOLO', disp_crop)

        key = cv2.waitKey(30) & 0xFF

        if key == ord('q'):
            break

        elif key == ord('s'):
            print("\n--- YOLO 실행 ---")
            det = detector.top1(cropped, conf=0.3)
            disp = cropped.copy()
            if det:
                print(f"  감지: {det['class_name']}  confidence={det['confidence']:.3f}  bbox={det['bbox']}")
                x1,y1,x2,y2 = [int(v) for v in det['bbox']]
                cv2.rectangle(disp, (x1,y1), (x2,y2), (0,0,255), 3)
                cv2.putText(disp, f"{det['class_name']} {det['confidence']:.2f}",
                            (x1, y1-8), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
            else:
                print(f"  감지 없음 (conf 0.3 기준)")
                cv2.putText(disp, "NO DETECTION", (10,60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
            cv2.imshow('ROI 크롭 + YOLO', disp)

finally:
    pipe.stop()
    cv2.destroyAllWindows()
