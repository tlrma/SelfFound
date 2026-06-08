"""
matcher.py 테스트
실행: python test_matcher.py
"""

import datetime
from matcher import (
    match_score, find_matches_for_item, find_matches_for_report,
    generate_item_description,
    ItemData, ReportData
)

# ─── 더미 데이터 ───────────────────────────────────────────────────────────────

item = ItemData(
    id=1,
    category="wallet",
    description="검은 가죽 반지갑, 카드 슬롯 여러 개, 모서리 약간 닳음",
    found_at=datetime.datetime(2025, 6, 4, 14, 0),
    found_location="3층 안내데스크",
)

# 매칭돼야 하는 신고
report_match = ReportData(
    id=1,
    category="wallet",
    description="검은 지갑 잃어버렸어요. 카드 많이 들어있는 지갑이에요.",
    lost_at=datetime.datetime(2025, 6, 4, 12, 0),
    lost_location="3층",
)

# 매칭 안 돼야 하는 신고 (카테고리 다름)
report_no_match = ReportData(
    id=2,
    category="phone",
    description="아이폰 잃어버렸어요.",
    lost_at=datetime.datetime(2025, 6, 4, 12, 0),
    lost_location="3층",
)

# 시간이 맞지 않는 신고 (분실이 습득보다 나중)
report_wrong_time = ReportData(
    id=3,
    category="wallet",
    description="검은 지갑 잃어버렸어요.",
    lost_at=datetime.datetime(2025, 6, 4, 16, 0),  # 습득보다 2시간 뒤
    lost_location="3층",
)

# ─── 테스트 ────────────────────────────────────────────────────────────────────

def test_match_score():
    print("\n[ 테스트 1 ] 정상 매칭 케이스")
    result = match_score(item, report_match)
    print(f"  점수:    {result.score}")
    print(f"  매칭:    {result.matched}")
    print(f"  세부:    시간={result.score_breakdown.time} / 장소={result.score_breakdown.location} / 묘사={result.score_breakdown.description}")
    print(f"  근거:    {result.reasoning}")

def test_category_filter():
    print("\n[ 테스트 2 ] 카테고리 불일치 (LLM 호출 없이 0점)")
    result = match_score(item, report_no_match)
    print(f"  점수:    {result.score}")
    print(f"  매칭:    {result.matched}")
    print(f"  근거:    {result.reasoning}")

def test_wrong_time():
    print("\n[ 테스트 3 ] 시간 불일치 (분실이 습득보다 나중)")
    result = match_score(item, report_wrong_time)
    print(f"  점수:    {result.score}")
    print(f"  매칭:    {result.matched}")
    print(f"  세부:    시간={result.score_breakdown.time}")

def test_find_matches():
    print("\n[ 테스트 4 ] find_matches_for_item (후보 풀 검색)")
    pool = [report_match, report_no_match, report_wrong_time]
    results = find_matches_for_item(item, pool)
    for r in results:
        print(f"  report_id={r.report_id}  점수={r.score}  매칭={r.matched}")

def test_image_description(image_path: str):
    print(f"\n[ 테스트 5 ] 이미지 → 설명 생성 ({image_path})")
    description = generate_item_description(image_path)
    print(f"  설명: {description}")

# ─── 실행 ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_category_filter()   # LLM 호출 없음, 빠름
    test_wrong_time()        # LLM 호출 없음, 빠름
    test_match_score()       # gpt-5-nano 호출
    test_find_matches()      # gpt-5-nano 호출

    # 이미지 테스트는 파일 경로 직접 넣어서 실행
    # test_image_description("test_image.jpg")