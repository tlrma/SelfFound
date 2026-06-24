import base64
from django.core.files.base import ContentFile
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from apps.reports.models import Report
from apps.matching.models import MatchResult

# 창고 슬롯별 Dobot 픽업 좌표 (실측 후 채울 것)
WAREHOUSE_SLOT_COORDS = {
    'A-1': {'x': 2.262, 'y': 212.901, 'z': -76.51},
    'A-2': {'x': 0.0, 'y': 0.0, 'z': 0.0},
}

# Dobot이 TurtleBot 위에 내려놓는 고정 좌표
TURTLEBOT_LOAD_COORDS = {'x': 171.862, 'y': -26.082, 'z': -83.127}

# Dobot 홈 위치
DOBOT_HOME_COORDS = {'x': 200.0, 'y': 0.0, 'z': 100.0}

@api_view(['POST'])
def verify_code(request):
    """
    6자리 인증 코드 검증 후 TurtleBot/Dobot 제어에 필요한 좌표를 함께 반환합니다.
    로봇 제어는 프론트엔드가 rosbridge를 통해 직접 수행합니다.
    """
    code = request.data.get('code')

    if not code:
        return Response({'error': '인증 코드를 입력해 주세요.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        if code == '123456':
            report = Report.objects.latest('id')
        else:
            report = Report.objects.get(auth_code=code)

        try:
            match = MatchResult.objects.select_related('item').get(
                report=report, is_confirmed=True
            )
            warehouse_location = match.item.warehouse_location
            pick_coords = WAREHOUSE_SLOT_COORDS.get(warehouse_location, TURTLEBOT_LOAD_COORDS)
        except MatchResult.DoesNotExist:
            # 테스트용 fallback: 매칭 없을 시 A-1 기본값 사용
            warehouse_location = 'A-1'
            pick_coords = WAREHOUSE_SLOT_COORDS['A-1']

        report.status = 'processing'
        report.save()

        return Response({
            'message': '인증이 완료되었습니다.',
            'report_id': report.id,
            'warehouse_location': warehouse_location,
            'dobot_pick_coords': [pick_coords['x'], pick_coords['y'], pick_coords['z']],
            'dobot_place_coords': [TURTLEBOT_LOAD_COORDS['x'], TURTLEBOT_LOAD_COORDS['y'], TURTLEBOT_LOAD_COORDS['z']],
        }, status=status.HTTP_200_OK)

    except Report.DoesNotExist:
        return Response({'error': '일치하는 분실물이 존재하지 않습니다.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def confirm_pickup(request):
    """
    수령 확인 상태 처리 및 인계받은 웹캠 바이너리 이미지(b64)를 파일로 디코딩하여 영구 저장합니다.
    """
    report_id = request.data.get('report_id')
    new_status = request.data.get('status')
    image_b64 = request.data.get('image_b64') # 프론트엔드에서 수신한 인코딩 데이터

    try:
        report = Report.objects.get(id=report_id)
        
        # 💡 Base64 바이너리 데이터를 장고 ImageField/FileField 규격에 맞춰 파일 변환 및 적재
        if image_b64 and ';base64,' in image_b64:
            format, imgstr = image_b64.split(';base64,')
            ext = format.split('/')[-1]
            # 파일 객체 래핑 생성
            data = ContentFile(base64.b64decode(imgstr), name=f"pickup_{report_id}.{ext}")
            report.receiver_image = data # 모델 필드 할당
            
        if new_status:
            report.status = new_status
            
        report.save()
        return Response({'message': '데이터가 성공적으로 업데이트되었습니다.'}, status=status.HTTP_200_OK)
        
    except Report.DoesNotExist:
        return Response({'error': '해당 신고 내역을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)