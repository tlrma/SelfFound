from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .conveyor_client import trigger_conveyor_belt

@api_view(['POST'])
def operate_conveyor(request):
    """
    프론트엔드에서 호출하는 컨베이어 벨트 수동 제어 API
    """
    success = trigger_conveyor_belt()
    
    if success:
        return Response({"message": "컨베이어 벨트가 작동을 시작했습니다."}, status=status.HTTP_200_OK)
    else:
        return Response({"error": "라즈베리파이 통신에 실패했습니다."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)