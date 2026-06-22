from rest_framework import serializers
from .models import Item

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        
        fields = [
            'id', 'category', 'confidence', 'description',
            'image_b64', 'found_info',
            'warehouse_location', 'status', 'created_at'
        ]
        
        read_only_fields = ['id', 'status', 'created_at']