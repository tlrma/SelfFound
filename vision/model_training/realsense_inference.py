import time
import pyrealsense2 as rs
import numpy as np
import cv2
from pathlib import Path
from ultralytics import YOLO

MODEL_PATH = Path(__file__).parent / "best.pt"
CONF       = 0.4
FONT       = cv2.FONT_HERSHEY_SIMPLEX

COLORS_BGR = [
    ( 30, 119, 180), (255, 127,  14), ( 44, 160,  44),
    (214,  39,  40), (148, 103, 189), (140,  86,  75),
    (227, 119, 194), (127, 127, 127), (188, 189,  34),
    ( 23, 190, 207), (255, 187, 120), (152, 223, 138),
]

model = YOLO(str(MODEL_PATH))
names = model.names
print(f"클래스: {list(names.values())}")
print("실행 중...  q:종료  +/-:conf 조절  s:저장")

pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
pipeline.start(config)

conf     = CONF
t_prev   = time.time()
fps      = 0.0
save_idx = 0

try:
    while True:
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        if not color_frame:
            continue

        frame = np.asanyarray(color_frame.get_data())

        now   = time.time()
        fps   = fps * 0.9 + (1.0 / max(now - t_prev, 1e-6)) * 0.1
        t_prev = now

        results = model(frame, conf=conf, verbose=False)[0]

        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cid   = int(box.cls[0])
            score = float(box.conf[0])
            label = f"{names[cid]} {score:.2f}"
            clr   = COLORS_BGR[cid % len(COLORS_BGR)]

            cv2.rectangle(frame, (x1, y1), (x2, y2), clr, 2)
            (tw, th), _ = cv2.getTextSize(label, FONT, 0.6, 2)
            cv2.rectangle(frame, (x1, y1 - th - 8), (x1 + tw + 4, y1), clr, -1)
            cv2.putText(frame, label, (x1 + 2, y1 - 4), FONT, 0.6, (255, 255, 255), 2)

        info = f"FPS:{fps:.1f}  CONF:{conf:.2f}  DET:{len(results.boxes)}"
        cv2.putText(frame, info, (8, 22), FONT, 0.6, (0, 0, 0), 3)
        cv2.putText(frame, info, (8, 22), FONT, 0.6, (255, 255, 255), 1)

        cv2.imshow("RealSense YOLO  (q:quit  +/-:conf  s:save)", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key in (ord("+"), ord("=")):
            conf = min(round(conf + 0.05, 2), 0.95)
            print(f"conf → {conf}")
        elif key == ord("-"):
            conf = max(round(conf - 0.05, 2), 0.05)
            print(f"conf → {conf}")
        elif key == ord("s"):
            p = Path(__file__).parent / f"capture_{save_idx:03d}.jpg"
            cv2.imwrite(str(p), frame)
            print(f"저장: {p}")
            save_idx += 1
finally:
    pipeline.stop()
    cv2.destroyAllWindows()
