"""
모델별 성능 비교 테스트.

실행:
  python test_models.py           # 텍스트 매칭 테스트 (top 5)
  python test_models.py --image /path/to/image.jpg  # 이미지 묘사 테스트 (top 5)
"""

import sys
import json
import re
import os
import base64
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

GMS_KEY       = os.environ.get("GMS_KEY")
OPENAI_URL    = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions"
GEMINI_BASE   = "https://gms.ssafy.io/gmsapi/generativelanguage.googleapis.com/v1beta/models"
ANTHROPIC_URL = "https://gms.ssafy.io/gmsapi/api.anthropic.com/v1/messages"

# ── 이미지 테스트 경로 (수정 가능) ────────────────────────────────────────────
# python test_models.py --image 로 실행 시 이 경로 사용
DEFAULT_IMAGE_PATH = "/home/ssafy/finalPJT/SelfFound/test-card2.jpg"

# ── 텍스트 매칭용 Top 5 (정확도 + 저크레딧) ───────────────────────────────────
# 선정 이유: 한국어 의미 비교, 다른 표현→같은 의미 인식, 반복 호출이므로 크레딧 중요
MATCHING_MODELS = [
    ("gpt-4.1-nano",          1),   # 최저가, 성능 확인
    ("gpt-4o-mini",           2),   # 기존 검증된 기준선
    ("gpt-5-nano",            4),   # 현재 서비스 사용 모델
    ("gpt-4.1-mini",          4),   # GPT-4.1 계열 비교
    ("gemini-2.5-flash-lite", 1),   # Google 최저가, 한국어 성능 확인
]

# ── 이미지 묘사용 Top 5 (정밀도 우선, 크레딧 이차) ────────────────────────────
# 선정 이유: 사소한 특징(로고·색상·재질) 정확히 묘사, 아이템 등록 시 1회만 호출
IMAGE_MODELS = [
    ("gpt-4o-mini",              2),   # 검증됨, 가성비
    ("gpt-4o",                  20),   # OpenAI 최고 비전
    ("gemini-3.5-flash",        18),   # Google 비전
    ("gemini-2.5-flash",        30),   # Google 최신 비전
    ("claude-haiku-4-5-20251001", 10), # Anthropic 비전, 저렴
]

# ── 텍스트 매칭 테스트 케이스 ──────────────────────────────────────────────────
# (item_desc, report_desc, expected: "match" | "no_match")
MATCH_CASES = [
    (
        # 같은 카드, 로고 위치 표현이 다름
        "흰색 배경의 플라스틱 카드로, 왼쪽 하단에 빨간색과 노란색 원이 있는 로고가 있습니다. "
        "카드 상단에는 'MASTER CARD'라는 글씨가 보이며, 카드사 불분명합니다.",
        "흰색에 오른쪽 아래에 마스터카드 로고 있는 우리은행 체크카드",
        "match",
    ),
    (
        # 다른 폰: 색상·상태가 명확히 다름
        "검정색 스마트폰으로 화면이 깨져 있으며 뒷면에 카메라가 세 개 달려 있습니다.",
        "흰색 삼성 갤럭시 폰, 뒷면에 스티커 있음",
        "no_match",
    ),
    (
        # 지갑: 색상 일치, 로고 없음·상세 불확실
        "갈색 가죽 지갑으로 안쪽에 카드 슬롯이 여러 개 있습니다. 로고는 보이지 않습니다.",
        "갈색 지갑 잃어버렸어요, 현금이랑 카드 들어있었는데",
        "match",
    ),
    (
        # STT 발음 차이: "삼층" vs "3층" — 의미적으로 같음
        "3층 엘리베이터 앞에서 발견된 검정 우산입니다.",
        "삼층에서 우산 잃어버렸어요",
        "match",
    ),
    (
        # 안경: 형태는 비슷하지만 색상이 완전히 다름
        "금색 테 반뿔 안경입니다. 렌즈는 투명합니다.",
        "검정 뿔테 안경 잃어버렸어요",
        "no_match",
    ),
]


def _is_gemini(model: str) -> bool:
    return model.startswith("gemini")

def _is_claude(model: str) -> bool:
    return model.startswith("claude")


def _parse_json(raw: str) -> dict:
    return json.loads(re.sub(r"```json|```", "", raw).strip())


# ── OpenAI 호환 API ────────────────────────────────────────────────────────────

def _openai_text(model: str, prompt: str) -> str:
    resp = requests.post(
        OPENAI_URL,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {GMS_KEY}"},
        json={"model": model, "messages": [{"role": "user", "content": prompt}]},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _openai_image(model: str, b64: str, prompt: str) -> str:
    resp = requests.post(
        OPENAI_URL,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {GMS_KEY}"},
        json={
            "model": model,
            "max_tokens": 300,
            "messages": [{"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                {"type": "text", "text": prompt},
            ]}],
        },
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


# ── Gemini API (GMS 프록시) ────────────────────────────────────────────────────

def _gemini_text(model: str, prompt: str) -> str:
    url = f"{GEMINI_BASE}/{model}:generateContent?key={GMS_KEY}"
    resp = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


def _gemini_image(model: str, b64: str, prompt: str) -> str:
    url = f"{GEMINI_BASE}/{model}:generateContent?key={GMS_KEY}"
    resp = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        json={"contents": [{"parts": [
            {"inline_data": {"mime_type": "image/jpeg", "data": b64}},
            {"text": prompt},
        ]}]},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


# ── Anthropic API (GMS 프록시) ─────────────────────────────────────────────────

def _anthropic_headers() -> dict:
    return {
        "Content-Type": "application/json",
        "x-api-key": GMS_KEY,
        "anthropic-version": "2023-06-01",
    }


def _claude_text(model: str, prompt: str) -> str:
    resp = requests.post(
        ANTHROPIC_URL,
        headers=_anthropic_headers(),
        json={
            "model": model,
            "max_tokens": 300,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


def _claude_image(model: str, b64: str, prompt: str) -> str:
    resp = requests.post(
        ANTHROPIC_URL,
        headers=_anthropic_headers(),
        json={
            "model": model,
            "max_tokens": 300,
            "messages": [{"role": "user", "content": [
                {"type": "image", "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": b64,
                }},
                {"type": "text", "text": prompt},
            ]}],
        },
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


# ── 공통 호출 함수 ─────────────────────────────────────────────────────────────

def call_matching(model: str, item_desc: str, report_desc: str) -> dict:
    prompt = f"""아래 두 물건이 같은 물건인지 판단해주세요.

[습득된 물건]
설명: {item_desc}

[분실 신고 묘사]
신고자 묘사: {report_desc}

반드시 아래 JSON 형식으로만 응답하세요. 다른 말은 절대 하지 마세요.
{{"score": 0에서 100 사이 정수, "reasoning": "한국어로 판단 근거 1~2문장"}}"""

    if _is_gemini(model):
        raw = _gemini_text(model, prompt)
    elif _is_claude(model):
        raw = _claude_text(model, prompt)
    else:
        raw = _openai_text(model, prompt)
    return _parse_json(raw)


def _load_image_b64(image_path: str, max_side: int = 512) -> str:
    """이미지를 읽어 512px 이하로 리사이즈 후 JPEG base64 반환."""
    from PIL import Image
    import io
    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    if max(w, h) > max_side:
        scale = max_side / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=70)
    return base64.b64encode(buf.getvalue()).decode()


def call_image_desc(model: str, image_path: str) -> str:
    b64 = _load_image_b64(image_path)

    prompt = (
        "이 분실물을 한국어로 상세히 설명해주세요. "
        "색상, 재질, 브랜드 로고, 특이한 특징을 빠짐없이 묘사해주세요. "
        "3~5문장으로만 답하세요."
    )
    if _is_gemini(model):
        return _gemini_image(model, b64, prompt)
    elif _is_claude(model):
        return _claude_image(model, b64, prompt)
    return _openai_image(model, b64, prompt)


RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")


def _save(tag: str, data: dict, chart_fn):
    """JSON + PNG 차트를 results/ 폴더에 저장."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = os.path.join(RESULTS_DIR, f"{tag}_{ts}")

    with open(f"{base}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n수치 저장: {base}.json")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        chart_fn(plt, data, base)
        print(f"차트 저장: {base}.png")
    except ImportError:
        print("matplotlib 미설치 — 차트 생략 (pip install matplotlib)")


def test_matching():
    print("\n[텍스트 매칭 정확도 테스트]")

    records = []
    for model, credit in MATCHING_MODELS:
        correct = 0
        cases = []
        for i, (item_desc, report_desc, expected) in enumerate(MATCH_CASES):
            try:
                t0 = time.time()
                r = call_matching(model, item_desc, report_desc)
                elapsed = time.time() - t0
                score = r["score"]
                matched = "match" if score >= 70 else "no_match"
                is_correct = matched == expected
                if is_correct:
                    correct += 1
                cases.append({"case": i + 1, "score": score, "expected": expected,
                               "matched": matched, "correct": is_correct,
                               "elapsed": round(elapsed, 2),
                               "reasoning": r.get("reasoning", "")})
            except Exception as e:
                cases.append({"case": i + 1, "score": None, "elapsed": None, "error": str(e)})
        accuracy = correct / len(MATCH_CASES)
        records.append({"model": model, "credit": credit, "accuracy": accuracy,
                         "correct": correct, "total": len(MATCH_CASES), "cases": cases})

    # ── 요약 테이블 ────────────────────────────────────────────────────────────
    print(f"\n{'모델':<26} {'C':>2}", end="")
    for i in range(len(MATCH_CASES)):
        print(f"  케이스{i+1}", end="")
    print("  정답률  평균응답")
    print("-" * 90)
    for rec in records:
        row = ""
        for c in rec["cases"]:
            if c.get("score") is None:
                row += "    ERR"
            else:
                ok = "✅" if c["correct"] else "❌"
                row += f"  {ok}{c['score']:>3}"
        times = [c["elapsed"] for c in rec["cases"] if c.get("elapsed") is not None]
        avg_t = f"{sum(times)/len(times):.1f}s" if times else " -"
        print(f"{rec['model']:<26} {rec['credit']:>2}C{row}  {rec['correct']}/{rec['total']}  {avg_t:>6}")

    # ── 모델별 케이스 reasoning ────────────────────────────────────────────────
    print()
    for rec in records:
        print(f"▶ {rec['model']} ({rec['credit']}C) — {rec['correct']}/{rec['total']}")
        for c in rec["cases"]:
            if c.get("score") is None:
                print(f"  케이스{c['case']}: ERR — {c.get('error', '')[:65]}")
            else:
                ok = "✅" if c["correct"] else "❌"
                t = f"{c['elapsed']:.1f}s"
                print(f"  케이스{c['case']} {ok} {c['score']:>3}점 ({t:>5}): {c['reasoning'][:60]}")
        print()

    def draw(plt, data, base):
        models   = [r["model"] for r in data["records"]]
        accuracy = [r["accuracy"] * 100 for r in data["records"]]
        credits  = [r["credit"] for r in data["records"]]
        colors   = ["#4CAF50" if a >= 80 else "#FF9800" if a >= 60 else "#F44336"
                    for a in accuracy]

        _, ax1 = plt.subplots(figsize=(10, 5))
        bars = ax1.bar(models, accuracy, color=colors, alpha=0.85, label="정확도 (%)")
        ax1.set_ylabel("정확도 (%)")
        ax1.set_ylim(0, 110)
        ax1.set_title("텍스트 매칭 모델별 정확도 vs 크레딧")
        for bar, acc in zip(bars, accuracy):
            ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                     f"{acc:.0f}%", ha="center", va="bottom", fontsize=9)

        ax2 = ax1.twinx()
        ax2.plot(models, credits, "D--", color="#1565C0", linewidth=1.5,
                 markersize=7, label="크레딧")
        ax2.set_ylabel("크레딧 (C)")

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

        plt.xticks(rotation=15, ha="right")
        plt.tight_layout()
        plt.savefig(f"{base}.png", dpi=150)
        plt.close()

    summary = [
        {
            "model": r["model"],
            "credit": r["credit"],
            "correct": r["correct"],
            "total": r["total"],
            "accuracy_pct": round(r["accuracy"] * 100, 1),
            "avg_elapsed_s": round(
                sum(c["elapsed"] for c in r["cases"] if c.get("elapsed") is not None)
                / max(sum(1 for c in r["cases"] if c.get("elapsed") is not None), 1),
                2,
            ),
        }
        for r in records
    ]
    _save("matching", {"summary": summary, "records": records}, draw)


def test_image(image_path: str):
    print(f"\n[이미지 묘사 품질 테스트] {image_path}\n")
    records = []
    for model, credit in IMAGE_MODELS:
        try:
            t0 = time.time()
            desc = call_image_desc(model, image_path)
            elapsed = time.time() - t0
            print(f"▶ {model} ({credit}C) — {elapsed:.1f}s")
            for line in desc.split(". "):
                if line.strip():
                    print(f"  {line.strip()}")
            records.append({"model": model, "credit": credit,
                             "description": desc, "elapsed": round(elapsed, 2), "error": None})
        except Exception as e:
            print(f"▶ {model} ({credit}C) — ERR")
            print(f"  ERR: {e}")
            records.append({"model": model, "credit": credit,
                             "description": None, "elapsed": None, "error": str(e)})
        print()

    def draw(plt, data, base):
        ok_records = [r for r in data["records"] if r["description"]]
        if not ok_records:
            return
        models  = [r["model"] for r in ok_records]
        lengths = [len(r["description"]) for r in ok_records]
        credits = [r["credit"] for r in ok_records]
        elapsed = [r["elapsed"] for r in ok_records]

        _, ax1 = plt.subplots(figsize=(10, 5))
        bars = ax1.bar(models, lengths, color="#42A5F5", alpha=0.85, label="묘사 길이 (chars)")
        ax1.set_ylabel("묘사 텍스트 길이 (chars)")
        ax1.set_title("이미지 묘사 모델별 응답 길이 / 응답시간 / 크레딧")
        for bar, l in zip(bars, lengths):
            ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
                     str(l), ha="center", va="bottom", fontsize=9)

        ax2 = ax1.twinx()
        ax2.plot(models, credits, "D--", color="#E53935", linewidth=1.5,
                 markersize=7, label="크레딧")
        ax2.plot(models, elapsed, "s:", color="#FF6F00", linewidth=1.5,
                 markersize=7, label="응답시간 (s)")
        ax2.set_ylabel("크레딧 (C) / 응답시간 (s)")

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

        plt.xticks(rotation=15, ha="right")
        plt.tight_layout()
        plt.savefig(f"{base}.png", dpi=150)
        plt.close()

    summary = [
        {
            "model": r["model"],
            "credit": r["credit"],
            "elapsed_s": r.get("elapsed"),
            "desc_length": len(r["description"]) if r["description"] else None,
            "error": r.get("error"),
        }
        for r in records
    ]
    _save("image", {"summary": summary, "image_path": image_path, "records": records}, draw)


if __name__ == "__main__":
    if "--image" in sys.argv:
        idx = sys.argv.index("--image")
        path = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else DEFAULT_IMAGE_PATH
        test_image(path)
    else:
        test_matching()
