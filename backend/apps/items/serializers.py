from rest_framework import serializers
from .models import Item


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'category', 'confidence', 'description',
                  'photo_path', 'found_location', 'status', 'created_at']
        read_only_fields = ['id', 'status', 'created_at']
