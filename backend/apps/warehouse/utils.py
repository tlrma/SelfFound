from .models import WarehouseSlot

# 💡 Dobot이 실제로 이동할 각 슬롯의 물리적 x, y, z 좌표 매핑 (예시)
# 이 수치들은 실제 환경의 창고 칸 위치에 맞게 수정하셔야 합니다.
SLOT_COORDINATES = {
    'A-1': {'x': 200.0, 'y': 150.0, 'z': -50.0},
    'A-2': {'x': 200.0, 'y':  50.0, 'z': -50.0},
    'B-1': {'x': 250.0, 'y': 150.0, 'z': -50.0},
    'B-2': {'x': 250.0, 'y':  50.0, 'z': -50.0},
}

def get_empty_warehouse_slot():
    """
    사용 가능한(비어있는) 창고 칸을 찾아 반환합니다.
    """
    # is_occupied가 False인 첫 번째 슬롯을 찾습니다.
    empty_slot = WarehouseSlot.objects.filter(is_occupied=False).order_by('slot_id').first()

    if empty_slot:
        # 💡 중요: 찾자마자 '점유 중'으로 상태를 변경합니다.
        # 이렇게 해야 로봇이 이동하는 동안 다른 분실물이 같은 칸에 중복 배정되는 것을 막을 수 있습니다.
        empty_slot.is_occupied = True
        empty_slot.save()

        # 슬롯 ID에 해당하는 로봇 물리 좌표 가져오기 (없을 경우 안전을 위해 0.0 반환)
        coords = SLOT_COORDINATES.get(empty_slot.slot_id, {'x': 0.0, 'y': 0.0, 'z': 0.0})

        return {
            'location_id': empty_slot.slot_id,
            'x': coords['x'],
            'y': coords['y'],
            'z': coords['z']
        }
    
    # 빈 슬롯이 없을 경우 None 반환
    return None

def initialize_warehouse_slots():
    """
    초기 5x5 창고 데이터를 생성하고, 2x2 영역만 비워두는 헬퍼 함수입니다.
    터미널에서 Django shell을 열고 한 번만 실행해 주시면 됩니다.
    """
    rows = ['A', 'B', 'C', 'D', 'E']
    cols = ['1', '2', '3', '4', '5']
    
    # 사용할 2x2 활성 영역 지정
    active_slots = ['A-1', 'A-2', 'B-1', 'B-2']

    for r in rows:
        for c in cols:
            slot_id = f"{r}-{c}"
            
            # 활성 영역이면 False(비어있음), 아니면 True(차있음/사용불가)
            is_active = slot_id in active_slots
            
            slot, created = WarehouseSlot.objects.get_or_create(
                slot_id=slot_id,
                defaults={'is_occupied': not is_active}
            )
            
            # 이미 DB에 생성된 슬롯이 있다면 상태를 강제로 업데이트합니다.
            if not created:
                slot.is_occupied = not is_active
                slot.save()
                
    print("5x5 창고 초기화가 완료되었습니다. (2x2 영역만 활성화됨)")