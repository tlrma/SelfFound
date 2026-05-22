"""
흰 배경 위 분실물 분리 (HSV 임계값 기반).

흰색 기준: Saturation < s_thresh AND Value > v_thresh
실제 조명 환경에 따라 두 임계값을 조정해야 함.
"""

import cv2
import numpy as np


def segment_on_white(
    image: np.ndarray,
    s_thresh: int = 40,
    v_thresh: int = 180,
    kernel_size: int = 5,
) -> tuple[np.ndarray, np.ndarray, tuple | None]:
    """
    흰 배경에서 물건 영역을 분리한다.

    Returns:
        masked_image : 배경이 검정으로 제거된 원본 이미지
        binary_mask  : 물건 영역 이진 마스크 (255=물건, 0=배경)
        bbox         : (x, y, w, h) 또는 물건 없으면 None
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # 흰색 픽셀 마스크 (배경)
    white_mask = (hsv[:, :, 1] < s_thresh) & (hsv[:, :, 2] > v_thresh)

    # 물건 = 흰색이 아닌 영역
    obj_mask = (~white_mask).astype(np.uint8) * 255

    # 노이즈 제거 및 구멍 메우기
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    obj_mask = cv2.morphologyEx(obj_mask, cv2.MORPH_OPEN, kernel)
    obj_mask = cv2.morphologyEx(obj_mask, cv2.MORPH_CLOSE, kernel)

    # 가장 큰 컨투어 = 분실물
    contours, _ = cv2.findContours(obj_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return image, obj_mask, None

    largest = max(contours, key=cv2.contourArea)

    # 너무 작으면 노이즈로 판단
    if cv2.contourArea(largest) < 500:
        return image, obj_mask, None

    # 최대 컨투어만 남긴 마스크
    clean_mask = np.zeros_like(obj_mask)
    cv2.drawContours(clean_mask, [largest], -1, 255, thickness=cv2.FILLED)

    masked = cv2.bitwise_and(image, image, mask=clean_mask)
    bbox = cv2.boundingRect(largest)  # (x, y, w, h)

    return masked, clean_mask, bbox


def visualize_segmentation(image: np.ndarray) -> np.ndarray:
    """분리 결과를 바운딩박스와 함께 시각화한 이미지 반환."""
    masked, mask, bbox = segment_on_white(image)
    vis = image.copy()
    if bbox is not None:
        x, y, w, h = bbox
        cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cx, cy = x + w // 2, y + h // 2
        cv2.circle(vis, (cx, cy), 5, (0, 0, 255), -1)
    return vis
