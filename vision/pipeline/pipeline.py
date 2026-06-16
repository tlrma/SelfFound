"""
비전 파이프라인 통합.

흐름: 이미지 입력 → 왜곡 보정 → 흰 배경 분리 → YOLO 추론 → 색상 추출 → LLM 묘사 → Dobot 좌표 변환
"""

import numpy as np

from .calibration import undistort
from .color_extractor import color_name, extract_dominant_colors
from .homography import pixel_to_dobot
from .inference import LostItemDetector
from .llm import generate_description
from .segmentation import segment_on_white


class VisionPipeline:
    def __init__(
        self,
        model_path: str,
        homography: np.ndarray | None = None,
        calibration: dict | None = None,
        pickup_z: float = 0.0,
        conf_threshold: float = 0.5,
        use_llm: bool = True,
    ):
        """
        Args:
            model_path    : 학습된 YOLO .pt 경로
            homography    : 픽셀→Dobot 변환 행렬 (load_homography()로 로드)
            calibration   : 카메라 캘리브레이션 결과 (load_calibration()로 로드)
            pickup_z      : Dobot 피킹 Z 높이 (mm). 환경에 따라 조정 필요.
            conf_threshold: YOLO 신뢰도 임계값
            use_llm       : True면 LLM으로 자연어 묘사 생성 (GMS_KEY 환경변수 필요)
        """
        self.detector   = LostItemDetector(model_path)
        self.H          = homography
        self.calib      = calibration
        self.pickup_z   = pickup_z
        self.conf       = conf_threshold
        self.use_llm    = use_llm

    def run(self, image: np.ndarray) -> dict:
        """
        이미지 한 장을 처리해 분류 결과와 Dobot 좌표를 반환한다.

        Returns:
            성공 시:
                {
                  "category"   : "Phone",
                  "confidence" : 0.92,
                  "description": "검정색 스마트폰으로...",  # use_llm=True 시
                  "colors"     : [{"rgb": (R,G,B), "hex": "#..", "ratio": 0.6, "name": "검정"}, ...],
                  "bbox_px"    : (x, y, w, h),
                  "center_px"  : (cx, cy),
                  "dobot_xyz"  : (X, Y, Z) or None,
                }
            실패 시:
                {"error": "object_not_found" | "no_detection"}
        """
        # 1. 카메라 왜곡 보정 (캘리브레이션 데이터 있을 때만)
        if self.calib:
            image = undistort(image, self.calib)

        # 2. 흰 배경 분리
        masked, mask, bbox = segment_on_white(image)
        if bbox is None:
            return {"error": "object_not_found"}

        # 3. YOLO 추론 (원본 이미지로, bbox crop 없이 전체 추론)
        detection = self.detector.top1(image, conf=self.conf)
        if detection is None:
            return {"error": "no_detection"}

        category = detection["class_name"]

        # 4. 색상 추출
        raw_colors = extract_dominant_colors(image, mask)
        colors = [{**c, "name": color_name(c["rgb"])} for c in raw_colors]

        # 5. LLM 자연어 묘사 생성
        description = generate_description(image, category) if self.use_llm else ""

        # 6. Dobot 좌표 변환
        x, y, w, h = bbox
        center_px = (x + w // 2, y + h // 2)
        dobot_xyz = (
            pixel_to_dobot(center_px, self.H, self.pickup_z)
            if self.H is not None
            else None
        )

        return {
            "category":    category,
            "confidence":  round(detection["confidence"], 4),
            "description": description,
            "colors":      colors,
            "bbox_px":     bbox,
            "center_px":   center_px,
            "dobot_xyz":   dobot_xyz,
        }
