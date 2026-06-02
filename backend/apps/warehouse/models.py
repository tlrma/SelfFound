from django.db import models
from apps.items.models import Item

# 5×5 물리 창고
class WarehouseSlot(models.Model):
    slot_id = models.CharField(max_length=10, unique=True)  # 예: "A-1", "B-5"
    is_occupied = models.BooleanField(default=False)
    item = models.OneToOneField(Item, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'warehouse_slots'