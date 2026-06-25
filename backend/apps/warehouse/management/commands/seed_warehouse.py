from django.core.management.base import BaseCommand
from apps.warehouse.models import WarehouseSlot

class Command(BaseCommand):
    help = '5x5 창고 슬롯 초기 데이터 생성 (A-1 ~ E-5)'

    def handle(self, *args, **kwargs):
        rows = ['A', 'B', 'C', 'D', 'E']
        cols = ['1', '2', '3', '4', '5']
        
        created_count = 0
        
        for row in rows:
            for col in cols:
                slot_id = f"{row}-{col}"
                
                # 이미 존재하는 슬롯이면 중복 생성 방지
                slot, created = WarehouseSlot.objects.get_or_create(
                    slot_id=slot_id,
                    defaults={'is_occupied': False, 'item': None}
                )
                
                if created:
                    created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'성공: 총 {created_count}개의 창고 슬롯이 생성되었습니다.')
        )
