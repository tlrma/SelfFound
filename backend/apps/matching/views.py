import random
import string

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.matching.email import send_match_email
from apps.matching.models import MatchResult
from apps.reports.models import Report


def _item_payload(item):
    return {
        'id': item.id,
        'category': item.category,
        'description': item.description,
        'image_b64': item.image_b64,
        'found_at': item.found_at,
        'found_info': item.found_info,
        'warehouse_location': item.warehouse_location,
        'status': item.status,
        'created_at': item.created_at,
    }


def _report_payload(report):
    return {
        'id': report.id,
        'user_name': report.user_name,
        'user_email': report.user_email,
        'category': report.category,
        'lost_location': report.lost_location,
        'lost_description': report.lost_description,
        'lost_at': report.lost_at,
        'status': report.status,
        'created_at': report.created_at,
    }


def _match_payload(match):
    return {
        'id': match.id,
        'similarity_score': match.similarity_score,
        'score_percent': round(match.similarity_score * 100),
        'reasoning': match.reasoning,
        'is_confirmed': match.is_confirmed,
        'created_at': match.created_at,
        'item': _item_payload(match.item),
        'report': _report_payload(match.report),
    }


@api_view(['GET'])
def review_candidates(request, report_id):
    try:
        report = Report.objects.get(pk=report_id)
    except Report.DoesNotExist:
        return Response({'error': '해당 신고 내역을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

    matches = (
        MatchResult.objects
        .select_related('item', 'report')
        .filter(report=report)
        .order_by('-similarity_score', '-created_at')
    )

    return Response({
        'status': 'ok',
        'report': _report_payload(report),
        'data': [_match_payload(match) for match in matches],
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
def decide_review_candidate(request, match_id):
    action = request.data.get('action')
    if action not in ['approve', 'reject']:
        return Response({'error': 'action은 approve 또는 reject여야 합니다.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        match = MatchResult.objects.select_related('item', 'report').get(pk=match_id)
    except MatchResult.DoesNotExist:
        return Response({'error': '해당 매칭 후보를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

    report = match.report
    item = match.item

    if action == 'approve':
        match.is_confirmed = True
        match.save(update_fields=['is_confirmed'])

        if not report.auth_code:
            report.auth_code = ''.join(random.choices(string.digits, k=6))
        report.status = 'matched'
        report.save(update_fields=['auth_code', 'status'])

        item.status = 'matched'
        item.save(update_fields=['status'])

        MatchResult.objects.filter(report=report).exclude(pk=match.pk).delete()

        if report.user_email:
            try:
                send_match_email(report.user_email, report.user_name, item, match.reasoning, report.auth_code)
            except Exception as exc:
                print(f'관리자 승인 후 매칭 이메일 발송 실패: {exc}')

        return Response({
            'status': 'ok',
            'message': '매칭 후보를 승인했습니다.',
            'data': _match_payload(match),
        }, status=status.HTTP_200_OK)

    match.delete()

    has_other_candidates = MatchResult.objects.filter(report=report).exists()
    if not has_other_candidates and report.status == 'review':
        report.status = 'searching'
        report.save(update_fields=['status'])

    return Response({
        'status': 'ok',
        'message': '매칭 후보를 반려했습니다.',
        'remaining_candidates': MatchResult.objects.filter(report=report).count(),
        'report': _report_payload(report),
    }, status=status.HTTP_200_OK)
