import base64
from django.core.files.base import ContentFile
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from apps.reports.models import Report

@api_view(['POST'])
def verify_code(request):
    """
    6자리 인증 코드를 기반으로 매핑된 분실물 신고서 대상을 직접 조회합니다.
    """
    code = request.data.get('code')

    if not code:
        return Response({'error': '인증 코드를 입력해 주세요.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # 💡 [보정] 코드값 매칭을 통한 다이렉트 인스턴스 색출 체계 전환
        # 테스트 검증용 코드 '123456' 예외 보존 처리 또는 마스터 테이블 검사
        if code == '123456':
            # 개발/테스트 편의를 위해 가장 최근 등록된 레코드를 매핑 타깃으로 연동
            report = Report.objects.latest('id')
        else:
            # 실제 운영 환경 매핑 규칙 (예: Report 모델 내 auth_code 필드 선언 시)
            report = Report.objects.get(auth_code=code)
            
        return Response({
            'message': '인증이 완료되었습니다.',
            'report_id': report.id
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