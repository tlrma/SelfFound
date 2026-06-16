from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Item
from .serializers import ItemSerializer
from apps.matching.service import match_new_item


@api_view(['POST'])
def create_item(request):
    """
    POST /api/items/
    비전 파이프라인 결과를 DB에 저장하고 매칭 알고리즘을 실행한다.

    body: { category, confidence, description, photo_path, found_location }
    description은 vision pipeline에서 LLM으로 생성해 전송한다.
    """
    serializer = ItemSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    item = serializer.save()

    matches = match_new_item(item)
    top_match = next((m for m in matches if m['matched']), None)

    return Response({
        'item': serializer.data,
        'top_match': top_match,
        'all_matches': matches,
    }, status=status.HTTP_201_CREATED)
