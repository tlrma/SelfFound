import base64

from django.core.files.base import ContentFile
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.matching.models import MatchResult
from apps.reports.models import Report
from apps.warehouse.models import WarehouseSlot
from apps.warehouse.utils import SLOT_COORDINATES

TURTLEBOT_LOAD_COORDS = {'x': 171.862, 'y': -26.082, 'z': -83.127}
DOBOT_HOME_COORDS = {'x': 200.0, 'y': 0.0, 'z': 100.0}

def _get_pickup_match(report):
    return (
        MatchResult.objects
        .select_related('item')
        .filter(report=report)
        .order_by('-is_confirmed', '-similarity_score', '-created_at')
        .first()
    )


@api_view(['POST'])
def verify_code(request):
    code = request.data.get('code')
    if not code:
        return Response({'error': '인증 코드를 입력해 주세요.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        report = Report.objects.get(auth_code=code)
    except Report.DoesNotExist:
        return Response({'error': '일치하는 분실물이 존재하지 않습니다.'}, status=status.HTTP_404_NOT_FOUND)

    match = _get_pickup_match(report)
    if match is None:
        return Response({'error': '인증된 신고와 연결된 매칭 물품이 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

    warehouse_location = match.item.warehouse_location
    pick_coords = SLOT_COORDINATES.get(warehouse_location, TURTLEBOT_LOAD_COORDS)

    report.status = 'processing'
    report.save(update_fields=['status'])

    return Response({
        'message': '인증이 완료되었습니다.',
        'report_id': report.id,
        'warehouse_location': warehouse_location,
        'dobot_pick_coords': [pick_coords['x'], pick_coords['y'], pick_coords['z']],
        'dobot_place_coords': [
            TURTLEBOT_LOAD_COORDS['x'],
            TURTLEBOT_LOAD_COORDS['y'],
            TURTLEBOT_LOAD_COORDS['z'],
        ],
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
def confirm_pickup(request):
    report_id = request.data.get('report_id')
    new_status = request.data.get('status')
    image_b64 = request.data.get('image_b64')

    try:
        with transaction.atomic():
            report = Report.objects.get(id=report_id)

            if image_b64 and ';base64,' in image_b64:
                image_format, imgstr = image_b64.split(';base64,', 1)
                ext = image_format.split('/')[-1]
                report.receiver_image = ContentFile(
                    base64.b64decode(imgstr),
                    name=f'pickup_{report_id}.{ext}',
                )

            if new_status == 'processing':
                report.status = 'processing'
            elif new_status in ['completed', 'returned']:
                match = _get_pickup_match(report)
                if match is None:
                    return Response(
                        {'error': '해당 신고와 연결된 매칭 물품을 찾을 수 없습니다.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                item = match.item
                if new_status == 'completed':
                    report.status = 'completed'
                    match.is_confirmed = True
                    match.save(update_fields=['is_confirmed'])

                    item.status = 'returned'
                    item.warehouse_location = None
                    item.save(update_fields=['status', 'warehouse_location'])

                    WarehouseSlot.objects.filter(item=item).update(
                        item=None,
                        is_occupied=False,
                    )
                else:
                    report.status = 'searching'
                    item.status = 'stored'
                    item.save(update_fields=['status'])
            elif new_status:
                return Response({'error': '지원하지 않는 상태 값입니다.'}, status=status.HTTP_400_BAD_REQUEST)

            report.save()

        return Response({'message': '데이터가 성공적으로 업데이트되었습니다.'}, status=status.HTTP_200_OK)
    except Report.DoesNotExist:
        return Response({'error': '해당 신고 내역을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as exc:
        return Response(
            {'error': f'서버 처리 중 오류가 발생했습니다: {exc}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
