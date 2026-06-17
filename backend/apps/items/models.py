from django.db import models

class Item(models.Model):
    # 사용자가 정의한 7개 카테고리로 변경
    CATEGORY_CHOICES = [
        ('Card', '카드'),
        ('Glasses', '안경'),
        ('Keys', '열쇠'),
        ('Phone', '휴대폰'),
        ('Sunglasses', '선글라스'),
        ('Wallet', '지갑'),
        ('Watch', '시계'),
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
    
    # CV 연동을 위해 수정된 부분
    image_b64 = models.TextField(blank=True, null=True)  # 기존 photo_path 대신 base64 데이터 직접 저장
    found_at = models.DateTimeField(blank=True, null=True) # STT 결과
    found_location = models.CharField(max_length=100, blank=True, null=True) # STT 결과
    
    # 분실물이 보관된 창고 위치
    warehouse_location = models.CharField(max_length=50, blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='stored')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'items'