from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from apps.reports.models import Report

@api_view(['POST'])
def verify_code(request):
    """
    본인 확인 인증번호를 검증합니다.
    """
    report_id = request.data.get('report_id')
    code = request.data.get('code')

    try:
        report = Report.objects.get(id=report_id)
        
        # 실제 환경에서는 report에 저장된 실제 인증코드와 비교합니다.
        # 현재는 테스트 및 시뮬레이션을 위해 공통 코드 '1234'로 검증을 통과시킵니다.
        if code == '1234': 
            return Response({'message': '인증이 완료되었습니다.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': '인증번호가 일치하지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)
            
    except Report.DoesNotExist:
        return Response({'error': '해당 신고 내역을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def confirm_pickup(request):
    """
    수령자가 본인 물품임을 확인하면 DB의 상태를 업데이트합니다.
    """
    report_id = request.data.get('report_id')
    new_status = request.data.get('status') # 프론트엔드에서 'completed'를 보냅니다.

    try:
        report = Report.objects.get(id=report_id)
        report.status = new_status
        report.save()
        
        return Response({'message': '수령 처리가 완료되었습니다.'}, status=status.HTTP_200_OK)
        
    except Report.DoesNotExist:
        return Response({'error': '해당 신고 내역을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)