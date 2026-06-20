"""
matcher.py(test/) ↔ Django 모델 연결 서비스.
Item/Report DB 인스턴스를 받아 매칭 점수를 계산하고 MatchResult를 저장한다.
"""

import sys
import datetime
import random
import string
from pathlib import Path

# test/matcher.py 임포트
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'test-matching'))
from matcher import (
    ItemData, ReportData,
    find_matches_for_item, find_matches_for_report,
    MATCH_THRESHOLD, REVIEW_THRESHOLD,
)

from apps.items.models import Item
from apps.reports.models import Report
from apps.matching.models import MatchResult
from apps.matching.email import send_match_email


def _to_item_data(item: Item) -> ItemData:
    return ItemData(
        id=item.id,
        category=item.category,
        description=item.description or "",
        found_at=item.created_at.replace(tzinfo=None),
        found_location=item.found_location or "",
        image_path="",
    )


def _to_report_data(report: Report) -> ReportData:
    lost_at = report.lost_at or report.created_at
    return ReportData(
        id=report.id,
        category=report.category,
        description=report.lost_description,
        lost_at=lost_at.replace(tzinfo=None),
        lost_location=report.lost_location or "",
    )


def match_new_item(item: Item) -> list[dict]:
    """
    새 분실물 입고 시 호출. 매칭되는 신고를 찾아 MatchResult에 저장.
    반환: 매칭된 결과 목록 (score 내림차순)
    """
    cutoff = item.created_at - datetime.timedelta(days=30)
    reports = Report.objects.filter(
        category=item.category,
        status='searching',
        created_at__gte=cutoff,
    )
    if not reports.exists():
        return []

    item_data = _to_item_data(item)
    report_pool = [_to_report_data(r) for r in reports]

    results = find_matches_for_item(item_data, report_pool)

    saved = []
    for r in results:
        if r.score >= REVIEW_THRESHOLD:
            MatchResult.objects.update_or_create(
                item_id=r.item_id,
                report_id=r.report_id,
                defaults={'similarity_score': r.score / 100.0},
            )
            report = Report.objects.get(id=r.report_id)
            if r.matched:
                if not report.auth_code:
                    report.auth_code = ''.join(random.choices(string.digits, k=6))
                report.status = 'matched'
                report.save(update_fields=['auth_code', 'status'])
                send_match_email(report.user_email, report.user_name, item, r.reasoning, report.auth_code)
            else:
                report.status = 'review'
                report.save(update_fields=['status'])
        saved.append({
            'report_id': r.report_id,
            'score': r.score,
            'matched': r.matched,
            'needs_review': REVIEW_THRESHOLD <= r.score < MATCH_THRESHOLD,
            'reasoning': r.reasoning,
        })

    return saved


def match_new_report(report: Report) -> list[dict]:
    """
    새 신고 접수 시 호출. 매칭되는 분실물을 찾아 MatchResult에 저장.
    반환: 매칭된 결과 목록 (score 내림차순)
    """
    cutoff = report.created_at - datetime.timedelta(days=30)
    items = Item.objects.filter(
        category=report.category,
        status='stored',
        created_at__gte=cutoff,
    )
    if not items.exists():
        return []

    report_data = _to_report_data(report)
    item_pool = [_to_item_data(i) for i in items]

    results = find_matches_for_report(report_data, item_pool)

    saved = []
    for r in results:
        if r.score >= REVIEW_THRESHOLD:
            MatchResult.objects.update_or_create(
                item_id=r.item_id,
                report_id=r.report_id,
                defaults={'similarity_score': r.score / 100.0},
            )
            if r.matched:
                matched_item = Item.objects.get(id=r.item_id)
                if not report.auth_code:
                    report.auth_code = ''.join(random.choices(string.digits, k=6))
                report.status = 'matched'
                report.save(update_fields=['auth_code', 'status'])
                send_match_email(report.user_email, report.user_name, matched_item, r.reasoning, report.auth_code)
            else:
                report.status = 'review'
                report.save(update_fields=['status'])
        saved.append({
            'item_id': r.item_id,
            'score': r.score,
            'matched': r.matched,
            'needs_review': REVIEW_THRESHOLD <= r.score < MATCH_THRESHOLD,
            'reasoning': r.reasoning,
        })

    return saved
