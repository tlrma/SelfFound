from django.db import models

class Item(models.Model):
    CATEGORY_CHOICES = [
        ('Card', '카드'),
        ('Glasses', '안경'),
        ('Keys', '열쇠'),
        ('Phone', '휴대폰'),
        ('Sunglasses', '선글라스'),
        ('Wallet', '지갑'),
        ('Watch', '시계'),
        ('Etc', '기타'),
    ]
    
    STATUS_CHOICES = [
        ('stored', '보관중'),
        ('matched', '매칭완료'),
        ('returned', '반환완료'),
        ('expired', '기간만료'),
        ('discarded', '폐기완료'),
    ]

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    confidence = models.FloatField(default=0.0)  # YOLO 인식 신뢰도
    description = models.TextField(blank=True, null=True)  # 상세 묘사
    
    image_b64 = models.TextField(blank=True, null=True)
    found_info = models.TextField(blank=True, null=True)  # STT 원문 (위치+시간 통합)
    
    # 분실물이 보관된 창고 위치
    warehouse_location = models.CharField(max_length=50, blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='stored')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'items'