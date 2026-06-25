from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Report
from .serializers import ReportSerializer
from apps.matching.service import match_new_report

@api_view(['POST'])
def create_report(request):
    """
    POST /api/reports/
    분실물 신고를 DB에 저장하고 즉시 응답을 반환합니다. (매칭 제외)
    """
    serializer = ReportSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    report = serializer.save()

    # 데이터 저장 후 매칭을 돌리지 않고 바로 프론트엔드로 성공 응답
    return Response({
        'message': '신고가 성공적으로 접수되었습니다.',
        'report_id': report.id
    }, status=status.HTTP_201_CREATED)


# ✅ 새로운 매칭 전용 API 추가
@api_view(['POST'])
def run_matching(request, pk):
    """
    POST /api/reports/<pk>/match/
    접수 완료 화면(또는 다음 단계)에서 호출하여 매칭 알고리즘을 실행합니다.
    """
    try:
        report = Report.objects.get(pk=pk)
    except Report.DoesNotExist:
        return Response({'error': '해당 신고 내역을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        matches = match_new_report(report)
        top_match = next((m for m in matches if m.get('matched')), None)
        # ✅ 질문자님께서 찾으시던 누락된 로직 추가 부분
        if top_match:
            report.status = 'matched'    # 매칭된 항목이 있으면 '매칭완료'로 변경
        else:
            report.status = 'searching'  # 없으면 '찾는중' 유지
            
        report.save() # 변경된 상태 값을 DB에 최종 반영합니다.
        
        return Response({
            'top_match': top_match,
            'all_matches': matches,
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        print(f"🚨 [매칭 알고리즘 에러]: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PATCH'])
def manage_reports(request, pk=None):
    # 1. 특정 ID(pk) 값이 주소창에 들어온 경우
    if pk is not None:
        try:
            report = Report.objects.get(pk=pk)
        except Report.DoesNotExist:
            return Response({'error': '해당 신고 내역을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        # 💡 [GET] 단건 상세 조회 처리 (ReportStatus.vue 연동)
        if request.method == 'GET':
            serializer = ReportSerializer(report)
            return Response({'status': 'ok', 'data': serializer.data}, status=status.HTTP_200_OK)
        
        # [PATCH] 관리자 대시보드 상태 수정 처리
        elif request.method == 'PATCH':
            serializer = ReportSerializer(report, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # 2. 주소창에 pk 없이 들어온 경우 (전체 목록 및 검색 조회)
    else:
        if request.method == 'GET':
            name = request.query_params.get('name', None)
            email = request.query_params.get('email', None)
            
            if name and email:
                queryset = Report.objects.filter(user_name=name, user_email=email).order_by('-created_at')
            else:
                queryset = Report.objects.all().order_by('-created_at')
                
            serializer = ReportSerializer(queryset, many=True)
            return Response({'status': 'ok', 'data': serializer.data}, status=status.HTTP_200_OK)