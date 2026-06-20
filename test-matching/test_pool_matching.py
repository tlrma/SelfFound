"""
풀 매칭 테스트.

실제 서비스 흐름과 동일:
  신고 1건 vs 여러 item 풀 → 가장 유사한 item 찾기

실행:
  python test_pool_matching.py
"""

import json
import re
import os
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

GMS_KEY     = os.environ.get("GMS_KEY")
OPENAI_URL  = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions"
GEMINI_BASE = "https://gms.ssafy.io/gmsapi/generativelanguage.googleapis.com/v1beta/models"

RESULTS_DIR      = os.path.join(os.path.dirname(__file__), "results")
MATCH_THRESHOLD  = 70   # 이상: 매칭 성공
REVIEW_THRESHOLD = 50   # 이상 70 미만: 관리자 검토 필요

MODELS = [
    ("gpt-4.1-nano",          1),
    ("gpt-4o-mini",           2),
    ("gpt-5-nano",            4),
    ("gpt-4.1-mini",          4),
    ("gemini-2.5-flash-lite", 1),
]

# ── Item 풀 ────────────────────────────────────────────────────────────────────
# (id, 카테고리, 묘사)
ITEM_POOL = [
    (1,  "Card",    "흰색 배경의 플라스틱 카드. 왼쪽 하단에 빨간색과 노란색 원 로고(마스터카드). 카드사 불분명."),
    (2,  "Phone",   "검정색 스마트폰. 화면이 깨져 있고 뒷면에 카메라 세 개."),
    (3,  "Wallet",  "갈색 가죽 지갑. 안쪽에 카드 슬롯 여러 개. 로고 없음."),
    (4,  "Glasses", "금색 테 반뿔 안경. 렌즈 투명."),
    (5,  "Etc",     "검정 우산. 3층 엘리베이터 앞에서 발견."),
    (6,  "Phone",   "흰색 아이폰. 뒷면에 사과 로고. 케이스 없음."),
    (7,  "Wallet",  "검정 인조가죽 반지갑. 브랜드 불분명."),
    (8,  "Card",    "파란색 카드. 앞면에 'IBK기업은행' 글씨. 체크카드."),
    (9,  "Keys",    "은색 열쇠 두 개 묶음. 작은 곰 인형 키링."),
    (10, "Glasses", "검정 뿔테 안경. 렌즈 약간 긁힘."),
]

# ── 테스트 케이스 ──────────────────────────────────────────────────────────────
# (케이스 설명, 신고 카테고리, 신고 묘사, 정답 item id)
# 정답 item id = None → 풀에 일치하는 item이 없어야 정답
TEST_CASES = [
    (
        "마스터카드 카드",
        "Card",
        "흰색에 오른쪽 아래 마스터카드 로고 있는 우리은행 체크카드",
        1,
    ),
    (
        "갈색 지갑",
        "Wallet",
        "갈색 지갑 잃어버렸어요, 현금이랑 카드 들어있었는데",
        3,
    ),
    (
        "STT: 삼층 검정 우산",
        "Etc",
        "삼층에서 검정 우산 잃어버렸어요",
        5,
    ),
    (
        "검정 뿔테 안경",
        "Glasses",
        "검정 뿔테 안경 잃어버렸어요",
        10,
    ),
    (
        "기업은행 카드",
        "Card",
        "파란 기업은행 카드 잃어버렸어요",
        8,
    ),
    # ── 정답 없는 케이스 (풀에 해당 item 없음) ────────────────────────────────
    (
        "[NO MATCH] 빨간 지갑",
        "Wallet",
        "빨간색 명품 지갑 잃어버렸어요, 루이비통 로고 있어요",
        None,
    ),
    (
        "[NO MATCH] 에어팟",
        "Etc",
        "흰색 에어팟 케이스 잃어버렸어요",
        None,
    ),
    (
        "[NO MATCH] 신한카드",
        "Card",
        "초록색 신한카드 잃어버렸어요",
        None,
    ),
]


def _call_api(model: str, prompt: str) -> str:
    if model.startswith("gemini"):
        url = f"{GEMINI_BASE}/{model}:generateContent?key={GMS_KEY}"
        resp = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=20,
        )
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    else:
        resp = requests.post(
            OPENAI_URL,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {GMS_KEY}"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}]},
            timeout=20,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


def call_match_score(model: str, item_desc: str, report_desc: str) -> dict:
    prompt = f"""아래 두 물건이 같은 물건인지 판단해주세요.

[습득된 물건]
설명: {item_desc}

[분실 신고 묘사]
신고자 묘사: {report_desc}

반드시 아래 JSON 형식으로만 응답하세요. 다른 말은 절대 하지 마세요.
{{"score": 0에서 100 사이 정수, "reasoning": "한국어로 판단 근거 1문장"}}"""

    raw = _call_api(model, prompt)
    return json.loads(re.sub(r"```json|```", "", raw).strip())


def find_best_match(model: str, category: str, report_desc: str):
    """같은 카테고리 item만 비교 후 최고 점수 item 반환."""
    candidates = [(id_, desc) for id_, cat, desc in ITEM_POOL if cat == category]
    best_id, best_score, best_reasoning = None, -1, ""
    scores = []
    for item_id, item_desc in candidates:
        r = call_match_score(model, item_desc, report_desc)
        scores.append((item_id, r["score"], r.get("reasoning", "")))
        if r["score"] > best_score:
            best_id, best_score, best_reasoning = item_id, r["score"], r.get("reasoning", "")
    return best_id, best_score, best_reasoning, scores


def run():
    print("\n[풀 매칭 테스트]")
    print("같은 카테고리 내 item 풀에서 신고와 가장 유사한 item을 찾습니다.\n")

    all_records = []

    for model, credit in MODELS:
        print(f"{'─'*70}")
        print(f"▶ {model} ({credit}C)")
        model_correct = 0
        model_records = []

        for case_name, category, report_desc, answer_id in TEST_CASES:
            try:
                t0 = time.time()
                picked_id, top_score, reasoning, all_scores = find_best_match(
                    model, category, report_desc
                )
                elapsed = time.time() - t0

                if top_score >= MATCH_THRESHOLD:
                    zone = "match"
                elif top_score >= REVIEW_THRESHOLD:
                    zone = "review"
                else:
                    zone = "no_match"

                if answer_id is None:
                    is_correct = zone == "no_match"
                else:
                    is_correct = zone in ("match", "review") and picked_id == answer_id
                ok = "✅" if is_correct else "❌"
                if is_correct:
                    model_correct += 1

                zone_label = {"match": "매칭", "review": "검토필요", "no_match": "없음"}[zone]
                answer_str = f"#{answer_id}" if answer_id else "없음"
                picked_str = f"#{picked_id} [{zone_label}] (점수 {top_score})"
                print(f"  {ok} [{case_name}]  {elapsed:.1f}s")
                print(f"     신고: {report_desc}")
                print(f"     정답: {answer_str}  →  선택: {picked_str}")
                print(f"     이유: {reasoning[:70]}")

                # 후보 점수 요약
                score_line = "  ".join(f"#{i}:{s}" for i, s, _ in sorted(all_scores, key=lambda x: -x[1]))
                print(f"     후보 점수: {score_line}")
                print()

                model_records.append({
                    "case": case_name, "category": category,
                    "report": report_desc, "answer_id": answer_id,
                    "picked_id": picked_id, "top_score": top_score,
                    "zone": zone, "correct": is_correct, "elapsed": round(elapsed, 2),
                    "reasoning": reasoning, "all_scores": all_scores,
                })

            except Exception as e:
                print(f"  ❌ [{case_name}] ERR: {e}\n")
                model_records.append({
                    "case": case_name, "answer_id": answer_id,
                    "correct": False, "error": str(e),
                })

        accuracy = model_correct / len(TEST_CASES)
        print(f"  정답률: {model_correct}/{len(TEST_CASES)} ({accuracy*100:.0f}%)\n")
        all_records.append({
            "model": model, "credit": credit,
            "accuracy": accuracy, "correct": model_correct,
            "total": len(TEST_CASES), "cases": model_records,
        })

    # ── 요약 테이블 ────────────────────────────────────────────────────────────
    print(f"\n{'─'*50}")
    print(f"{'모델':<26} {'C':>2}  정답률  평균응답")
    print(f"{'─'*50}")
    for rec in all_records:
        ok_cases = [c for c in rec["cases"] if "elapsed" in c]
        avg_t = f"{sum(c['elapsed'] for c in ok_cases)/len(ok_cases):.1f}s" if ok_cases else "-"
        print(f"{rec['model']:<26} {rec['credit']:>2}C  "
              f"{rec['correct']}/{rec['total']}     {avg_t:>5}")

    # ── JSON 저장 ──────────────────────────────────────────────────────────────
    os.makedirs(RESULTS_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(RESULTS_DIR, f"pool_matching_{ts}.json")

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
        for r in all_records
    ]

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            {"summary": summary, "item_pool": ITEM_POOL, "records": all_records},
            f, ensure_ascii=False, indent=2,
        )
    print(f"\n수치 저장: {out_path}")


if __name__ == "__main__":
    run()
