from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Item
from .serializers import ItemSerializer
from apps.matching.service import match_new_item

from apps.warehouse.models import WarehouseSlot
from apps.warehouse.utils import get_empty_warehouse_slot
from apps.robot_tasks.dobot_publisher import publish_dobot_pick_and_place_task


@api_view(['GET', 'POST'])
def create_item(request):
    """
    GET /api/items/
    query: found_from=YYYY-MM-DD, found_to=YYYY-MM-DD

    POST /api/items/
    body: { category, confidence, description, image_b64 }
    found_info는 키오스크 STT 큐에서 자동 주입된다.
    """
    if request.method == 'GET':
        queryset = Item.objects.all().order_by('-created_at')
        found_from = parse_date(request.query_params.get('found_from') or '')
        found_to = parse_date(request.query_params.get('found_to') or '')

        if found_from:
            queryset = queryset.filter(created_at__date__gte=found_from)
        if found_to:
            queryset = queryset.filter(created_at__date__lte=found_to)

        serializer = ItemSerializer(queryset, many=True)
        return Response({'status': 'ok', 'data': serializer.data}, status=status.HTTP_200_OK)

    data = request.data.copy()

    # dobot 데이터 분리
    target1_dobot = data.pop('dobot', None)

    # found_info는 detector_node가 payload에 직접 포함해서 전송

    # 빈 창고 위치 탐색 및 데이터 주입
    target2_warehouse = get_empty_warehouse_slot()
    if target2_warehouse:
        data['warehouse_location'] = target2_warehouse.get('location_id')

    serializer = ItemSerializer(data=data)
    if not serializer.is_valid():
        if target2_warehouse:
            WarehouseSlot.objects.filter(
                slot_id=target2_warehouse.get('location_id'),
                item__isnull=True,
            ).update(is_occupied=False)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    item = serializer.save()

    if target2_warehouse:
        WarehouseSlot.objects.filter(
            slot_id=target2_warehouse.get('location_id')
        ).update(item=item, is_occupied=True)

    matches = match_new_item(item)
    top_match = next((m for m in matches if m['matched']), None)

    if target1_dobot and target2_warehouse:
        publish_dobot_pick_and_place_task(target1_dobot, target2_warehouse)

    return Response({
        'item': serializer.data,
        'top_match': top_match,
        'all_matches': matches,
    }, status=status.HTTP_201_CREATED)
