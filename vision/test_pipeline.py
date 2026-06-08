"""
vision/pipeline 모듈 테스트
실행: python test_pipeline.py
RealSense, Dobot, 실기 하드웨어 없이 로컬 이미지로 동작 검증.
"""

import sys
import cv2
import numpy as np
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

BOLD  = "\033[1m"
GREEN = "\033[92m"
RED   = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def ok(msg):  print(f"  {GREEN}✓{RESET} {msg}")
def fail(msg): print(f"  {RED}✗ {msg}{RESET}")
def warn(msg): print(f"  {YELLOW}⚠ {msg}{RESET}")
def header(msg): print(f"\n{BOLD}[ {msg} ]{RESET}")

# 테스트에 쓸 샘플 이미지 (카테고리별 1장씩)
SAMPLES = {
    "wallet":  "dataset/test/images/43336463-old-leather-wallet-on-wood-table_jpg.rf.0c7649189ef162618e588b94cf0e4792.jpg",
    "phone":   "dataset/test/images/apple-desk-iphone-mobile-phone_jpg.rf.28badb2d0dbb492bba0210cc9ba3b3d5.jpg",
    "glasses": "dataset/test/images/images31_jpg.rf.e9e5676bda10c77f93ac1e8ffe0bcc04.jpg",
}


# ─── 테스트 1: Segmentation ────────────────────────────────────────────────────

def test_segmentation():
    header("1. Segmentation (흰 배경 분리)")
    from pipeline.segmentation import segment_on_white, visualize_segmentation

    for name, rel_path in SAMPLES.items():
        img_path = ROOT / rel_path
        if not img_path.exists():
            warn(f"{name}: 이미지 없음 ({rel_path})")
            continue

        img = cv2.imread(str(img_path))
        if img is None:
            fail(f"{name}: 이미지 로드 실패")
            continue

        masked, mask, bbox = segment_on_white(img)

        if bbox is None:
            warn(f"{name}: 흰 배경 없음 → bbox None (배경이 흰색이 아닌 이미지)")
        else:
            x, y, w, h = bbox
            obj_ratio = (mask > 0).sum() / mask.size
            ok(f"{name}: bbox=({x},{y},{w},{h})  물건 비율={obj_ratio:.1%}")


# ─── 테스트 2: Inference (YOLO) ───────────────────────────────────────────────

def test_inference():
    header("2. Inference (YOLO 분류)")
    from pipeline.inference import LostItemDetector

    model_path = ROOT / "best.pt"
    if not model_path.exists():
        fail(f"best.pt 없음: {model_path}")
        return

    try:
        detector = LostItemDetector(str(model_path))
        ok("모델 로드 성공")
    except Exception as e:
        fail(f"모델 로드 실패: {e}")
        return

    for name, rel_path in SAMPLES.items():
        img_path = ROOT / rel_path
        if not img_path.exists():
            warn(f"{name}: 이미지 없음")
            continue

        img = cv2.imread(str(img_path))
        result = detector.top1(img, conf=0.3)

        if result is None:
            warn(f"{name}: 검출 없음 (conf 0.3 이하)")
        else:
            ok(f"{name}: {result['class_name']} (confidence={result['confidence']:.2f})")

        # 전체 검출 결과도 출력
        all_results = detector.detect(img, conf=0.1)
        if all_results:
            for r in all_results[:3]:
                print(f"      └ {r['class_name']} conf={r['confidence']:.2f}")


# ─── 테스트 3: Color Extractor ────────────────────────────────────────────────

def test_color_extractor():
    header("3. Color Extractor (K-means 색상 추출)")
    from pipeline.color_extractor import extract_dominant_colors, color_name

    for name, rel_path in SAMPLES.items():
        img_path = ROOT / rel_path
        if not img_path.exists():
            warn(f"{name}: 이미지 없음")
            continue

        img = cv2.imread(str(img_path))
        # 마스크 없이 전체 이미지로 테스트 (배경 포함)
        full_mask = np.ones(img.shape[:2], dtype=np.uint8) * 255

        colors = extract_dominant_colors(img, full_mask, n_colors=3)
        color_names = [f"{color_name(c['rgb'])}({c['ratio']:.0%})" for c in colors]
        ok(f"{name}: {', '.join(color_names)}")


# ─── 테스트 4: 통합 파이프라인 ────────────────────────────────────────────────

def test_pipeline():
    header("4. VisionPipeline 통합 (calibration·homography 없이)")
    from pipeline.pipeline import VisionPipeline

    model_path = ROOT / "best.pt"
    if not model_path.exists():
        fail("best.pt 없음")
        return

    # calibration, homography 없이 실행 — dobot_xyz는 None이 돼야 정상
    pipeline = VisionPipeline(
        model_path=str(model_path),
        homography=None,
        calibration=None,
        pickup_z=0.0,
        conf_threshold=0.3,
    )
    ok("파이프라인 초기화 성공")

    for name, rel_path in SAMPLES.items():
        img_path = ROOT / rel_path
        if not img_path.exists():
            warn(f"{name}: 이미지 없음")
            continue

        img = cv2.imread(str(img_path))
        result = pipeline.run(img)

        if "error" in result:
            warn(f"{name}: {result['error']}")
        else:
            cat    = result["category"]
            conf   = result["confidence"]
            colors = [c["name"] for c in result["colors"]]
            dobot  = result["dobot_xyz"]
            ok(f"{name}: {cat} ({conf:.2f})  색상={colors}  dobot_xyz={dobot}")
            if dobot is None:
                print(f"      └ dobot_xyz=None 은 정상 (homography 미설정)")


# ─── 테스트 5: Calibration 코드 경로 확인 ────────────────────────────────────

def test_calibration_api():
    header("5. Calibration API (코드 로딩만 확인)")
    from pipeline.calibration import calibrate_camera, undistort, save_calibration, load_calibration
    ok("calibrate_camera, undistort, save_calibration, load_calibration 임포트 성공")
    warn("실제 캘리브레이션은 체커보드 + 카메라 필요 → 실기 때 수행")


# ─── 테스트 6: Homography API 확인 ───────────────────────────────────────────

def test_homography_api():
    header("6. Homography API (더미 데이터로 계산)")
    from pipeline.homography import compute_homography, pixel_to_dobot, reprojection_error

    # 더미 대응점 (실제 캘리브레이션 전까지 placeholder)
    pixel_pts = [(100, 100), (300, 100), (300, 300), (100, 300),
                 (200, 200), (400, 200)]
    dobot_pts = [(50, 50),   (150, 50),  (150, 150), (50, 150),
                 (100, 100), (200, 100)]

    try:
        H = compute_homography(pixel_pts, dobot_pts)
        ok(f"Homography 행렬 계산 성공 (shape={H.shape})")

        test_px = (200, 200)
        dx, dy, dz = pixel_to_dobot(test_px, H, z=50.0)
        ok(f"pixel_to_dobot({test_px}) → ({dx:.1f}, {dy:.1f}, {dz:.1f}) mm")

        err = reprojection_error(pixel_pts, dobot_pts, H)
        ok(f"재투영 오차: {err:.2f} mm (더미 데이터)")
    except Exception as e:
        fail(f"Homography 계산 실패: {e}")


# ─── 실행 ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"{BOLD}=== Vision Pipeline 테스트 ==={RESET}")
    print(f"작업 디렉토리: {ROOT}")

    test_segmentation()
    test_inference()
    test_color_extractor()
    test_pipeline()
    test_calibration_api()
    test_homography_api()

    print(f"\n{BOLD}=== 완료 ==={RESET}")
    print("⚠  calibration.json, homography.json 은 실기 환경에서 수집 필요")
