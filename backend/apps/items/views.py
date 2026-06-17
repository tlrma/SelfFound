from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Item
from .serializers import ItemSerializer
from apps.matching.service import match_new_item

from apps.warehouse.utils import get_empty_warehouse_slot
from apps.robot_tasks.dobot_publisher import publish_dobot_pick_and_place_task


@api_view(['POST'])
def create_item(request):
    """
    POST /api/items/
    비전 파이프라인 결과를 DB에 저장하고 매칭 알고리즘을 실행한다.
    """
    data = request.data.copy()
    
    # dobot 데이터 분리
    target1_dobot = data.pop('dobot', None)
    
    # 빈 창고 위치 탐색 및 데이터 주입
    target2_warehouse = get_empty_warehouse_slot()
    if target2_warehouse:
        data['warehouse_location'] = target2_warehouse.get('location_id')

    # 시리얼라이저를 통한 검증 및 저장
    serializer = ItemSerializer(data=data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    item = serializer.save()

    # 매칭 알고리즘 실행
    matches = match_new_item(item)
    top_match = next((m for m in matches if m['matched']), None)

    # ROS 2 로봇 제어 명령 하달
    if target1_dobot and target2_warehouse:
        publish_dobot_pick_and_place_task(target1_dobot, target2_warehouse)

    return Response({
        'item': serializer.data,
        'top_match': top_match,
        'all_matches': matches,
    }, status=status.HTTP_201_CREATED)