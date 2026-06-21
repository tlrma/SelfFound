from robodk import robolink    # RoboDK API
from robodk import robomath    # Robot toolbox
from robodk import * # RoboDK API
from robodk.robolink import * # RoboDK API

RDK = robolink.Robolink()

# ----------------------------------------------------------------
# 1. 최상위 프레임 생성
# ----------------------------------------------------------------
def ADDFrame():
    MAIN_Base = RDK.AddFrame("MAIN Base")
    return MAIN_Base


# ----------------------------------------------------------------
# 2. 로봇 및 오브젝트 로드 함수
# ----------------------------------------------------------------
def addfile_robot(main_base):
    dobot_item = RDK.AddFile(r'C:\work\SelfFound\roboDK\Dobot-Magician.robot', main_base)

    dobot_base_frame = RDK.Item("Dobot Magician Base", 3)
    if not dobot_base_frame.Valid():
        # 만약 로봇 기본 이름으로 프레임이 생성되었다면 찾아서 이름을 변경
        auto_frame = RDK.Item("Dobot-Magician Base", 3)
        if auto_frame.Valid():
            auto_frame.setName("Dobot Magician Base")


def addfile_tool():
    # 💡 변경된 로봇 이름을 정확히 추적할 수 있도록 예외 처리를 추가
    robot_item = RDK.Item("Dobot Magician", 2)
    if not robot_item.Valid():
        robot_item = RDK.Item("Dobot-Magician", 2)
        
    if robot_item.Valid():
        RDK.AddFile(r'C:\work\SelfFound\roboDK\Tool1.tool', robot_item)


def addfile_conveyor(main_base):
    con1_item = RDK.AddFile(r'C:\work\SelfFound\roboDK\CON1.robot', main_base)
    
    # 자동으로 생성된 컨베이어 베이스 프레임 이름 정렬
    con1_base_frame = RDK.Item("CON1 Base", 3)
    if not con1_base_frame.Valid():
        auto_frame = RDK.Item("CON1 Base", 3)
        if auto_frame.Valid():
            auto_frame.setName("CON1 Base")


def addfile_object(main_base):
    RDK.AddFile(r'C:\work\SelfFound\roboDK\Room.stl', main_base)
    RDK.AddFile(r'C:\work\SelfFound\roboDK\Panels.sld', main_base)
    RDK.AddFile(r'C:\work\SelfFound\roboDK\Table.stl', main_base)
    RDK.AddFile(r'C:\work\SelfFound\roboDK\Warehouse.stl', main_base)
    RDK.AddFile(r'C:\work\SelfFound\roboDK\Item.stl', main_base)
    RDK.AddFile(r'C:\work\SelfFound\roboDK\Camera.sld', main_base)


# ----------------------------------------------------------------
# 3. 메인 실행 제어
# ----------------------------------------------------------------
main_b = ADDFrame()

addfile_robot(main_b)
addfile_tool()
addfile_conveyor(main_b)
addfile_object(main_b)
