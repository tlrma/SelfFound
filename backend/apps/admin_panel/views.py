from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Alert


@api_view(['GET', 'POST'])
def alerts(request):
    if request.method == 'GET':
        unread = Alert.objects.filter(is_read=False)
        data = [
            {
                'id':         a.id,
                'message':    a.message,
                'level':      a.level,
                'source':     a.source,
                'created_at': a.created_at.isoformat(),
            }
            for a in unread
        ]
        return Response({'status': 'ok', 'data': data})

    # POST: create new alert
    message = request.data.get('message', '').strip()
    if not message:
        return Response({'error': 'message is required'}, status=status.HTTP_400_BAD_REQUEST)

    alert = Alert.objects.create(
        message=message,
        level=request.data.get('level', Alert.LEVEL_ERROR),
        source=request.data.get('source', ''),
    )
    return Response({'status': 'ok', 'id': alert.id}, status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
def dismiss_alert(request, pk):
    try:
        alert = Alert.objects.get(pk=pk)
    except Alert.DoesNotExist:
        return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)

    alert.is_read = True
    alert.save(update_fields=['is_read'])
    return Response({'status': 'ok'})
