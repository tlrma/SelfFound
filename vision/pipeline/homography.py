"""
픽셀 좌표 → Dobot XY 좌표 변환 (Homography 행렬).

사용법:
1. 캘리브레이션 포인트 수집: 카메라로 보이는 특정 픽셀 위치에
   Dobot을 실제로 이동시켜 (px, py) ↔ (dobot_x, dobot_y) 쌍을 최소 6개 기록
2. compute_homography()로 변환 행렬 계산 후 저장
3. pixel_to_dobot()으로 실시간 변환
"""

import json
from pathlib import Path

import cv2
import numpy as np


def compute_homography(
    pixel_points: list[tuple[float, float]],
    dobot_points: list[tuple[float, float]],
) -> np.ndarray:
    """
    픽셀-Dobot 대응점으로 Homography 행렬(3×3)을 계산한다.

    Args:
        pixel_points : [(px, py), ...] 최소 4쌍 (6쌍 이상 권장)
        dobot_points : [(dx, dy), ...] 대응되는 Dobot XY (mm)
    """
    if len(pixel_points) < 4:
        raise ValueError("대응점은 최소 4쌍 필요 (6쌍 이상 권장)")
    if len(pixel_points) != len(dobot_points):
        raise ValueError("pixel_points와 dobot_points 개수가 다름")

    src = np.array(pixel_points, dtype=np.float32)
    dst = np.array(dobot_points, dtype=np.float32)
    H, mask = cv2.findHomography(src, dst, cv2.RANSAC)

    inliers = int(mask.sum())
    print(f"Homography 계산 완료 | 인라이어: {inliers}/{len(pixel_points)}")
    return H


def pixel_to_dobot(
    pixel_point: tuple[float, float],
    H: np.ndarray,
    z: float = 0.0,
) -> tuple[float, float, float]:
    """
    픽셀 좌표 하나를 Dobot XYZ(mm)로 변환한다.

    Args:
        pixel_point : (px, py)
        H           : compute_homography()로 얻은 3×3 행렬
        z           : Dobot Z 높이 (카메라로 추정 불가, 고정값 사용)
    """
    pt = np.array([[[pixel_point[0], pixel_point[1]]]], dtype=np.float32)
    result = cv2.perspectiveTransform(pt, H)
    dx, dy = float(result[0][0][0]), float(result[0][0][1])
    return (dx, dy, z)


def reprojection_error(
    pixel_points: list[tuple[float, float]],
    dobot_points: list[tuple[float, float]],
    H: np.ndarray,
) -> float:
    """변환 오차(mm)를 계산해 캘리브레이션 품질을 확인한다."""
    errors = []
    for px, actual in zip(pixel_points, dobot_points):
        predicted = pixel_to_dobot(px, H)
        err = np.linalg.norm(np.array(predicted[:2]) - np.array(actual))
        errors.append(err)
    mean_err = float(np.mean(errors))
    print(f"평균 재투영 오차: {mean_err:.2f} mm")
    return mean_err


def save_homography(H: np.ndarray, path: str = "homography.json") -> None:
    with open(path, "w") as f:
        json.dump({"H": H.tolist()}, f, indent=2)
    print(f"Homography 저장: {path}")


def load_homography(path: str = "homography.json") -> np.ndarray:
    with open(path) as f:
        data = json.load(f)
    return np.array(data["H"], dtype=np.float64)
