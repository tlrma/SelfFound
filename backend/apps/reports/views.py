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
    분실물 신고를 DB에 저장하고 매칭 알고리즘을 실행한다.

    body: { user_name, user_email, category, lost_location, lost_description, lost_at(optional) }
    """
    serializer = ReportSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    report = serializer.save()

    matches = match_new_report(report)
    top_match = next((m for m in matches if m['matched']), None)

    return Response({
        'report': serializer.data,
        'top_match': top_match,
        'all_matches': matches,
    }, status=status.HTTP_201_CREATED)
