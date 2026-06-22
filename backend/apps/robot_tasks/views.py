from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .conveyor_client import trigger_conveyor_belt
from .found_info_queue import push_found_info


@api_view(['POST'])
def operate_conveyor(request):
    """
    키오스크 확인 버튼 → Modbus reg[0]=1 + STT 텍스트 저장.
    body: { found_info: "오후 2시 3층 강의실에서 주웠어요" }
    """
    found_info = request.data.get('found_info', '').strip()
    if found_info:
        push_found_info(found_info)

    success = trigger_conveyor_belt()

    if success:
        return Response({"message": "컨베이어 벨트가 작동을 시작했습니다."}, status=status.HTTP_200_OK)
    else:
        return Response({"error": "Modbus 서버 연결 실패"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
