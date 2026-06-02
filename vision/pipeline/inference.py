"""
YOLO 추론 래퍼.

학습된 모델(.pt)이 준비되면 model_path만 지정하면 바로 사용 가능.
모델 없이도 pipeline 나머지 부분은 동작하도록 설계.
"""

from pathlib import Path
import numpy as np


class LostItemDetector:
    def __init__(self, model_path: str):
        """
        Args:
            model_path: 학습된 YOLO .pt 파일 경로
        """
        from ultralytics import YOLO

        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(f"모델 파일 없음: {path}")
        self.model = YOLO(str(path))

    def detect(self, image: np.ndarray, conf: float = 0.5) -> list[dict]:
        """
        이미지에서 분실물을 감지한다.

        Returns:
            [{"class_id", "class_name", "confidence", "bbox": [x1,y1,x2,y2]}, ...]
            confidence 내림차순 정렬
        """
        results = self.model(image, conf=conf, verbose=False)[0]
        detections = []
        for box in results.boxes:
            detections.append({
                "class_id":   int(box.cls),
                "class_name": results.names[int(box.cls)],
                "confidence": float(box.conf),
                "bbox":       box.xyxy[0].tolist(),  # [x1, y1, x2, y2]
            })
        detections.sort(key=lambda d: d["confidence"], reverse=True)
        return detections

    def top1(self, image: np.ndarray, conf: float = 0.5) -> dict | None:
        """가장 신뢰도 높은 감지 결과 하나만 반환. 없으면 None."""
        results = self.detect(image, conf)
        return results[0] if results else None
