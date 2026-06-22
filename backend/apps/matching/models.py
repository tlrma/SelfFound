from django.db import models
from apps.items.models import Item
from apps.reports.models import Report

class MatchResult(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    report = models.ForeignKey(Report, on_delete=models.CASCADE)
    # LLM이 계산한 0.0 ~ 1.0 사이의 유사도 점수
    similarity_score = models.FloatField()
    reasoning = models.TextField(blank=True, default='')
    is_confirmed = models.BooleanField(default=False) # 주인이 본인 확인을 완료했는지 여부
    created_at = models.DateTimeField(auto_now_add=True)
