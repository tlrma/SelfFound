from django.db import models

class Report(models.Model):
    STATUS_CHOICES = [
        ('searching', '찾는중'),
        ('matched', '매칭완료'),
        ('completed', '수령완료'),
    ]

    # items.Item과 동일한 카테고리 선택 옵션을 적용합니다.
    CATEGORY_CHOICES = [
        ('Card', '카드'),
        ('Glasses', '안경'),
        ('Keys', '열쇠'),
        ('Phone', '휴대폰'),
        ('Sunglasses', '선글라스'),
        ('Wallet', '지갑'),
        ('Watch', '시계'),
    ]

    user_name = models.CharField(max_length=50)
    user_email = models.EmailField()
    # max_length를 20으로 유지하고 choices를 연결합니다.
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    lost_location = models.CharField(max_length=100, blank=True, null=True)
    lost_description = models.TextField()  # LLM이 분석할 핵심 자연어 데이터
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='searching')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reports'  #