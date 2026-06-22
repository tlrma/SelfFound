from rest_framework import serializers
from .models import Report


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['id', 'user_name', 'user_email', 'category',
                  'lost_location', 'lost_description', 'lost_at',
                  'status', 'created_at']
        read_only_fields = ['id', 'created_at']
