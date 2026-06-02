"""
K-means 기반 주요 색상 추출.

마스크 영역(물건)의 픽셀만 사용하므로 배경 색이 결과에 섞이지 않음.
"""

import numpy as np


def extract_dominant_colors(
    image: np.ndarray,
    mask: np.ndarray,
    n_colors: int = 3,
) -> list[dict]:
    """
    마스킹된 이미지에서 지배적인 색상 n개를 추출한다.

    Args:
        image  : BGR 이미지
        mask   : 물건 영역 이진 마스크 (255=물건)
        n_colors: 추출할 색상 수

    Returns:
        [{"rgb": (R,G,B), "hex": "#RRGGBB", "ratio": 0.xx}, ...]
        비율 내림차순 정렬
    """
    from sklearn.cluster import KMeans

    pixels = image[mask > 0]  # BGR 픽셀 배열
    if len(pixels) < n_colors:
        return []

    km = KMeans(n_clusters=n_colors, n_init=10, random_state=42)
    km.fit(pixels)

    centers = km.cluster_centers_.astype(int)  # BGR
    counts = np.bincount(km.labels_)
    total = counts.sum()

    results = []
    for i in np.argsort(-counts):
        b, g, r = int(centers[i][0]), int(centers[i][1]), int(centers[i][2])
        results.append({
            "rgb":   (r, g, b),
            "hex":   f"#{r:02X}{g:02X}{b:02X}",
            "ratio": round(float(counts[i]) / total, 3),
        })

    return results


def color_name(rgb: tuple[int, int, int]) -> str:
    """
    RGB 값을 간단한 한국어 색상명으로 변환.
    매칭 알고리즘의 색상 설명 생성에 사용.
    """
    r, g, b = rgb
    h_val = _rgb_to_hue(r, g, b)
    v_val = max(r, g, b)
    s_val = (max(r, g, b) - min(r, g, b)) / (max(r, g, b) + 1e-6)

    if v_val < 50:
        return "검정"
    if v_val > 200 and s_val < 0.15:
        return "흰색"
    if s_val < 0.15:
        return "회색"

    if h_val < 15 or h_val >= 345:
        return "빨강"
    if h_val < 45:
        return "주황"
    if h_val < 75:
        return "노랑"
    if h_val < 150:
        return "초록"
    if h_val < 210:
        return "청록"
    if h_val < 270:
        return "파랑"
    if h_val < 315:
        return "보라"
    return "분홍"


def _rgb_to_hue(r: int, g: int, b: int) -> float:
    r_, g_, b_ = r / 255.0, g / 255.0, b / 255.0
    cmax, cmin = max(r_, g_, b_), min(r_, g_, b_)
    delta = cmax - cmin
    if delta == 0:
        return 0.0
    if cmax == r_:
        h = 60 * (((g_ - b_) / delta) % 6)
    elif cmax == g_:
        h = 60 * (((b_ - r_) / delta) + 2)
    else:
        h = 60 * (((r_ - g_) / delta) + 4)
    return h % 360
