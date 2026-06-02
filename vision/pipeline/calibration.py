"""
카메라 캘리브레이션 (체커보드 기반).

체커보드 출력 → 다양한 각도에서 20장 이상 촬영 → calibrate_camera()
이후 undistort()로 실시간 왜곡 보정.
"""

import json
from pathlib import Path

import cv2
import numpy as np


def calibrate_camera(
    image_paths: list[str],
    board_size: tuple[int, int] = (9, 6),
    square_size_mm: float = 25.0,
) -> dict:
    """
    체커보드 이미지들로 내부 파라미터를 계산한다.

    Args:
        image_paths   : 체커보드가 찍힌 이미지 경로 리스트 (20장 이상 권장)
        board_size    : 내부 코너 수 (cols, rows). 10×7 보드면 (9, 6)
        square_size_mm: 체커보드 한 칸 실제 크기 (mm)

    Returns:
        {camera_matrix, dist_coeffs, reprojection_error, image_size}
    """
    objp = np.zeros((board_size[0] * board_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:board_size[0], 0:board_size[1]].T.reshape(-1, 2)
    objp *= square_size_mm

    obj_points, img_points = [], []
    image_size = None
    success_count = 0

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    for path in image_paths:
        img = cv2.imread(path)
        if img is None:
            print(f"  읽기 실패: {path}")
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        image_size = gray.shape[::-1]  # (w, h)

        ret, corners = cv2.findChessboardCorners(gray, board_size)
        if not ret:
            print(f"  코너 미검출: {Path(path).name}")
            continue

        corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        obj_points.append(objp)
        img_points.append(corners)
        success_count += 1
        print(f"  코너 검출 성공: {Path(path).name}")

    if success_count < 5:
        raise RuntimeError(f"유효 이미지 부족: {success_count}장 (최소 5장 필요)")

    print(f"\n캘리브레이션 시작 ({success_count}장 사용)...")
    ret, mtx, dist, _, _ = cv2.calibrateCamera(
        obj_points, img_points, image_size, None, None
    )

    result = {
        "camera_matrix": mtx.tolist(),
        "dist_coeffs":   dist.tolist(),
        "reprojection_error": round(float(ret), 4),
        "image_size":    list(image_size),
    }
    print(f"재투영 오차: {ret:.4f} px  (0.5 이하면 양호)")
    return result


def undistort(image: np.ndarray, calib: dict) -> np.ndarray:
    """
    캘리브레이션 결과로 이미지 왜곡을 보정한다.

    Args:
        calib: calibrate_camera() 또는 load_calibration()의 반환값
    """
    mtx  = np.array(calib["camera_matrix"], dtype=np.float64)
    dist = np.array(calib["dist_coeffs"],   dtype=np.float64)
    h, w = image.shape[:2]
    new_mtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w, h), alpha=1)
    undistorted = cv2.undistort(image, mtx, dist, None, new_mtx)
    x, y, rw, rh = roi
    return undistorted[y:y+rh, x:x+rw] if all([rw, rh]) else undistorted


def save_calibration(calib: dict, path: str = "camera_calib.json") -> None:
    with open(path, "w") as f:
        json.dump(calib, f, indent=2)
    print(f"캘리브레이션 저장: {path}")


def load_calibration(path: str = "camera_calib.json") -> dict:
    with open(path) as f:
        return json.load(f)
