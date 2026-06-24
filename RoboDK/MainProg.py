from robodk import robolink    # RoboDK API
from robodk import robomath    # Robot toolbox
RDK = robolink.Robolink()
from robodk import * # RoboDK API
from robolink import * # Robot toolbox
import time

# 로봇 선언
Dobot = RDK.Item("Dobot Magician", 2)
CON1 = RDK.Item("CON1", 2)

# 오브젝트 선언
Room = RDK.Item("Room", 5)
Panels = RDK.Item("Panels", 5)
Warehouse = RDK.Item("Warehouse", 5)
Table = RDK.Item("Table", 5)
Item_Object = RDK.Item("Item", 5)

# Tool 선언
Tool1 = RDK.Item("Tool1", 4)

# 프레임 선언
MAIN_Base = RDK.Item("MAIN Base", 3)
Dobot_Base = RDK.Item("Dobot Magician Base", 3)
CON1_Base = RDK.Item("CON1 Base", 3)


# ----------------------------------------------------------------
# 1. 컨베이어 이송 구동 함수
# ----------------------------------------------------------------
def job1_conveyor():
    print("컨베이어 이송 시작.")
    for x_pos in range(-540, -2000, -20):
        if CON1.Valid():
            CON1.setPose(transl(x_pos, 0.0, 0.0))
            RDK.Render()
            time.sleep(0.02)
    print("컨베이어 이송 완료.")


# ----------------------------------------------------------------
# 2. 두봇 매지션 흡착 및 이송 함수
# ----------------------------------------------------------------
def job2_dobot_pick_and_place():
    print("두봇 피크 앤 플레이스 시작.")
    
    if Dobot.Valid():
        # 두봇의 기준 좌표계를 베이스로 설정
        Dobot.setPoseFrame(Dobot_Base)

        via_joints = [-90.00, 40.58, -6.15, 0.00]        
        pick_joints = [-90.00, 42.08, 12.54, 0.00]
        
        # 1) 원하는 Pick 위치로 이동
        Dobot.MoveJ(via_joints)
        time.sleep(0.5)
        Dobot.MoveL(pick_joints)
        time.sleep(0.5)
        
        # 진공 흡착(Vacuum ON) 작동
        Tool1.AttachClosest("Item", 200)
        time.sleep(0.5)
        
        # 2) 안전 높이로 수직 상승
        Dobot.MoveL(via_joints)
        time.sleep(0.5)

        via_joints = [90.00, 1.26, 20.12, 0.00] 
        place_joints = [90.00, 32.14, 61.93, 0.00]
        
        # 3) Place 위치로 이동
        Dobot.MoveJ(via_joints)
        time.sleep(0.5)
        Dobot.MoveL(place_joints)
        time.sleep(0.5)
        
        # 진공 해제(Vacuum OFF)
        Tool1.DetachAll(MAIN_Base)
        time.sleep(0.5)
        
        # 4) 작업 종료 후 로봇 팔 안전 상승
        Dobot.MoveL(via_joints)
        time.sleep(0.5)

        
    print("두봇 피크 앤 플레이스 완료.")


# ----------------------------------------------------------------
# 3. 두봇 복귀 및 초기 방향 정렬 함수
# ----------------------------------------------------------------
def job3_return_home():
    if Dobot.Valid():
        print("두봇 복귀 시작.")
        Dobot.MoveJ([0.0, 0.0, 0.0, 0.0])
        print("두봇 복귀 완료.")


# ----------------------------------------------------------------
# 메인 프로세스 시퀀스 실행
# ----------------------------------------------------------------
job1_conveyor()             
job2_dobot_pick_and_place() 
job3_return_home()
