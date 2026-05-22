from django.db import models
from apps.items.models import Item

class RobotTask(models.Model):
    TASK_TYPE_CHOICES = [
        ('intake', '적재'),
        ('pickup', '수령반환'),
        ('return', '창고복귀'),
        ('discard', '폐기'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '대기중'),
        ('running', '수행중'),
        ('success', '완료'),
        ('failed', '실패'),
    ]

    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_code = models.CharField(max_length=50, blank=True, null=True)  # 예: "PICKUP_FAILED"
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'robot_tasks'