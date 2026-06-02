"""
YOLOv11 학습 스크립트 — Lost-and-Found 데이터셋
데이터 검증 결과 반영:
  - 이미지 512×512 (Roboflow 전처리 고정)
  - Roboflow에서 이미 rotation/brightness/blur 3× 증강 완료
  - 클래스 불균형 846× (Phone vs Charging-cable)
  - Umbrella: valid/test 샘플 0개
"""

from pathlib import Path
from ultralytics import YOLO
import yaml, torch

# ── 경로 / 설정 ────────────────────────────────────────────
ROOT       = Path(__file__).parent
DATA_YAML  = ROOT / "dataset" / "data.yaml"
RUNS_DIR   = ROOT / "runs"
MODEL_NAME = "yolo11s.pt"   # ~4GB→n  ~6GB→s  ~10GB→m
BATCH      = 16             # VRAM 부족 시 8

with open(DATA_YAML) as f:
    _meta = yaml.safe_load(f)
CLASS_NAMES  = _meta["names"]
TRAIN_COUNTS = [717, 6, 15, 3882, 144, 15, 5075, 1368, 117, 681, 591, 9]

# ── 학습 설정 ─────────────────────────────────────────────
CFG = dict(
    data        = str(DATA_YAML),
    imgsz       = 512,
    epochs      = 100,
    batch       = BATCH,
    workers     = 4,
    device      = 0 if torch.cuda.is_available() else "cpu",
    project     = str(RUNS_DIR),
    name        = "exp",
    exist_ok    = False,

    # ─ 옵티마이저
    optimizer        = "AdamW",
    lr0              = 0.001,
    lrf              = 0.01,
    momentum         = 0.937,
    weight_decay     = 0.0005,
    warmup_epochs    = 3,
    warmup_momentum  = 0.8,

    # ─ 손실 가중치
    box = 7.5,
    cls = 0.5,
    dfl = 1.5,

    # ─ 증강 (Roboflow: rotation±15°, brightness±17%, blur 이미 적용)
    degrees   = 0.0,   # Roboflow에서 이미 적용
    hsv_h     = 0.015,
    hsv_s     = 0.5,
    hsv_v     = 0.3,   # Roboflow brightness와 중복 방지
    translate = 0.1,
    scale     = 0.5,
    shear     = 0.0,
    perspective = 0.0,
    flipud    = 0.0,
    fliplr    = 0.5,
    bgr       = 0.0,
    mosaic    = 1.0,
    mixup     = 0.1,
    copy_paste= 0.1,
    erasing   = 0.4,

    # ─ 학습 제어
    patience    = 20,
    save_period = 10,
    val         = True,
    plots       = True,
    verbose     = True,
)


def print_imbalance_warning():
    print("\n" + "=" * 60)
    print("클래스 불균형 현황 (train bbox 기준)")
    print("-" * 60)
    for name, cnt in zip(CLASS_NAMES, TRAIN_COUNTS):
        bar = "█" * int(cnt / max(TRAIN_COUNTS) * 30)
        print(f"  {name:<18} {cnt:>5}  {bar}")
    mx, mn = max(TRAIN_COUNTS), min(TRAIN_COUNTS)
    print(f"\n  불균형 비율: {mx/mn:.0f}x  (max={mx}, min={mn})")
    print("  [주의] Umbrella: valid/test 샘플 없음 → mAP 측정 불가")
    print("  [주의] Charging-cable/iPad/Earphones/Pen 극히 적음")
    print("=" * 60 + "\n")


# ── 메인 ──────────────────────────────────────────────────
def main():
    print_imbalance_warning()

    model   = YOLO(MODEL_NAME)
    results = model.train(**CFG)

    save_dir = Path(results.save_dir)
    model.val(data=str(DATA_YAML), split="test", imgsz=512,
              batch=BATCH, save_json=True)
    print(f"\n최적 가중치 경로: {save_dir / 'weights' / 'best.pt'}")


if __name__ == "__main__":
    main()
