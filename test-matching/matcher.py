"""
분실물 매칭 알고리즘 프로토타입
- 텍스트 유사도: gpt-5-nano (1 크레딧, 텍스트)
"""

import json
import re
import datetime
import os
import requests
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

# ─── 상수 ─────────────────────────────────────────────────────────────────────

GMS_KEY    = os.environ.get("GMS_KEY")
OPENAI_URL = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions"

MATCH_THRESHOLD      = 70
MAX_TIME_WINDOW_DAYS = 30

WEIGHTS = {
    "time":        0.20,
    "location":    0.30,
    "description": 0.50,
}

# ─── 데이터 구조 ───────────────────────────────────────────────────────────────

@dataclass
class ItemData:
    """창고에 입고된 습득물"""
    id:             int
    category:       str
    description:    str        # generate_item_description()으로 생성한 자연어 설명
    found_at:       datetime.datetime
    found_location: str
    image_path:     str = ""

@dataclass
class ReportData:
    """분실자가 접수한 신고"""
    id:             int
    category:       str
    description:    str        # 신고자가 직접 입력한 묘사
    lost_at:        datetime.datetime
    lost_location:  str

@dataclass
class ScoreBreakdown:
    time:        float   # 0~1
    location:    float   # 0~1
    description: float   # 0~1

@dataclass
class MatchResult:
    item_id:         int
    report_id:       int
    score:           int          # 0~100 종합 점수
    matched:         bool         # 임계값 통과 여부
    score_breakdown: ScoreBreakdown
    reasoning:       str          # LLM 판단 근거


# ─── OpenAI API 헬퍼 ───────────────────────────────────────────────────────────

def _call_openai(model: str, messages: list) -> str:
    """OpenAI 형식 API 공통 호출 함수"""
    response = requests.post(
        OPENAI_URL,
        headers={
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {GMS_KEY}",
        },
        json={"model": model, "messages": messages},
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def _parse_json(text: str) -> dict:
    """LLM 응답에서 JSON 파싱 (```json 블록 자동 제거)"""
    clean = re.sub(r"```json|```", "", text).strip()
    return json.loads(clean)


# ─── 개별 점수 함수 ────────────────────────────────────────────────────────────

def score_time(item: ItemData, report: ReportData) -> float:
    """분실 추정 시각이 습득 시각보다 앞이어야 함. 차이가 작을수록 높은 점수."""
    if report.lost_at > item.found_at:
        return 0.0

    diff_hours = (item.found_at - report.lost_at).total_seconds() / 3600

    if diff_hours <= 48:     # 2일 이내
        return 1.0
    elif diff_hours <= 168:  # 1주일 이내
        return 0.7
    elif diff_hours <= 720:  # 30일 이내
        return 0.4
    return 0.0


def score_location(item: ItemData, report: ReportData) -> float:
    """장소 유사도 (프로토타입: 키워드 기반). 추후 임베딩으로 교체 가능."""
    loc_item   = item.found_location.lower()
    loc_report = report.lost_location.lower()

    if loc_item == loc_report:
        return 1.0
    if set(loc_item.split()) & set(loc_report.split()):
        return 0.6
    return 0.1


def score_description_llm(item: ItemData, report: ReportData) -> tuple[float, str]:
    """
    gpt-5-nano로 묘사 유사도 계산 (1 크레딧).
    반환: (0~1 float, 한국어 reasoning)
    """
    prompt = f"""아래 두 물건이 같은 물건인지 판단해주세요.

    [습득된 물건]
    카테고리: {item.category}
    설명: {item.description}

    [분실 신고 묘사]
    카테고리: {report.category}
    신고자 묘사: {report.description}

    반드시 아래 JSON 형식으로만 응답하세요. 다른 말은 절대 하지 마세요.
    {{"score": 0에서 100 사이 정수, "reasoning": "한국어로 판단 근거 1~2문장"}}"""

    messages = [{"role": "user", "content": prompt}]
    raw      = _call_openai("gpt-5-nano", messages)
    result   = _parse_json(raw)
    return result["score"] / 100.0, result["reasoning"]


# ─── 핵심 함수 ─────────────────────────────────────────────────────────────────

def match_score(item: ItemData, report: ReportData) -> MatchResult:
    """
    단일 (item, report) 쌍의 매칭 점수를 계산해 MatchResult 반환.
    카테고리가 다르면 LLM 호출 없이 즉시 0점 반환.
    """
    if item.category != report.category:
        return MatchResult(
            item_id=item.id,
            report_id=report.id,
            score=0,
            matched=False,
            score_breakdown=ScoreBreakdown(time=0.0, location=0.0, description=0.0),
            reasoning="카테고리 불일치",
        )

    t = score_time(item, report)
    l = score_location(item, report)
    d, reasoning = score_description_llm(item, report)

    total     = WEIGHTS["time"] * t + WEIGHTS["location"] * l + WEIGHTS["description"] * d
    score_int = round(total * 100)

    return MatchResult(
        item_id=item.id,
        report_id=report.id,
        score=score_int,
        matched=score_int >= MATCH_THRESHOLD,
        score_breakdown=ScoreBreakdown(
            time=round(t, 2),
            location=round(l, 2),
            description=round(d, 2),
        ),
        reasoning=reasoning,
    )


# ─── 양방향 매칭 ───────────────────────────────────────────────────────────────

def find_matches_for_item(
    item: ItemData,
    report_pool: list[ReportData],
) -> list[MatchResult]:
    """
    새 분실물 입고 시 신고 풀에서 후보를 찾아 점수 순으로 반환.

    Django 연동 예시 (views.py):
        cutoff = item_obj.found_at - timedelta(days=MAX_TIME_WINDOW_DAYS)
        qs = Report.objects.filter(
            category=item_obj.category, status="open",
            lost_at__gte=cutoff, lost_at__lte=item_obj.found_at
        )
        results = find_matches_for_item(item_data, [ReportData(...) for r in qs])
        top = next((r for r in results if r.matched), None)
        # top 있으면 → 서진: 메일 발송 트리거 (나중에 연결)
    """
    results = [match_score(item, report) for report in report_pool]
    results.sort(key=lambda r: r.score, reverse=True)
    return results


def find_matches_for_report(
    report: ReportData,
    item_pool: list[ItemData],
) -> list[MatchResult]:
    """
    새 신고 접수 시 분실물 풀에서 후보를 찾아 점수 순으로 반환.

    Django 연동 예시 (views.py):
        qs = Item.objects.filter(
            category=report_obj.category, status="stored",
            found_at__gte=cutoff
        )
        results = find_matches_for_report(report_data, [ItemData(...) for i in qs])
        top = next((r for r in results if r.matched), None)
    """
    results = [match_score(item, report) for item in item_pool]
    results.sort(key=lambda r: r.score, reverse=True)
    return results