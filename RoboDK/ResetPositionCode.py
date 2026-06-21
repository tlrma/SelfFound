from robodk import robolink    # RoboDK API
from robodk import robomath    # Robot toolbox
from robodk import * # RoboDK API
from robodk.robolink import * # RoboDK API

RDK = robolink.Robolink()

# ----------------------------------------------------------------
# 1. 트리 창에 존재하는 실제 아이템 객체 정의
# ----------------------------------------------------------------
MAIN_Base = RDK.Item("MAIN Base", 3)
Dobot_Base = RDK.Item("Dobot Magician Base", 3)
if not Dobot_Base.Valid():
    Dobot_Base = RDK.Item("Dobot-Magician Base", 3)
CON1_Base = RDK.Item("CON1 Base", 3)

Dobot = RDK.Item("Dobot-Magician", 2)
if not Dobot.Valid():
    Dobot = RDK.Item("Dobot Magician", 2)
CON1 = RDK.Item("CON1", 2)

Room = RDK.Item("Room", 5)
Panels = RDK.Item("Panels", 5)
Warehouse = RDK.Item("Warehouse", 5)
if not Warehouse.Valid():
    Warehouse = RDK.Item("warehouse", 5)

Table = RDK.Item("Table", 5)
Item = RDK.Item("Item", 5)
Tool1 = RDK.Item("Tool1", 4)
Camera = RDK.Item("Camera", 5)


# ----------------------------------------------------------------
# 2. 이미지 트리 창 기준 최종 계층 구조 정의
# ----------------------------------------------------------------
# 1) 베이스 프레임들을 MAIN Base 하위로 종속
if Dobot_Base.Valid() and MAIN_Base.Valid(): Dobot_Base.setParent(MAIN_Base)
if CON1_Base.Valid() and MAIN_Base.Valid(): CON1_Base.setParent(MAIN_Base)

# 2) 도봇 로봇 본체와 툴 구조 조립
if Dobot.Valid() and Dobot_Base.Valid(): Dobot.setParent(Dobot_Base)
if Tool1.Valid() and Dobot.Valid(): Tool1.setParent(Dobot)

# 3) 컨베이어 벨트 본체를 CON1 Base 하위로 종속
if CON1.Valid() and CON1_Base.Valid(): CON1.setParent(CON1_Base)

# 4) Item이 CON1(컨베이어 장치)을 부모로 따라가도록 묶기
if Item.Valid() and CON1.Valid():
    Item.setParent(CON1)

# 5) 나머지 환경 및 적재 오브젝트들은 MAIN Base 하위로 일렬 정렬
if Room.Valid() and MAIN_Base.Valid(): Room.setParent(MAIN_Base)
if Panels.Valid() and MAIN_Base.Valid(): Panels.setParent(MAIN_Base)
if Table.Valid() and MAIN_Base.Valid(): Table.setParent(MAIN_Base)
if Warehouse.Valid() and MAIN_Base.Valid(): Warehouse.setParent(MAIN_Base)
if Camera.Valid() and MAIN_Base.Valid(): Camera.setParent(MAIN_Base)


# ----------------------------------------------------------------
# 3. 설계도 기반 정밀 좌표 재배치 (단위: mm)
# ----------------------------------------------------------------
Panels.setPose(Mat([[     1.000000,     0.000000,     0.000000, -2000.000000 ],
      [     0.000000,     1.000000,     0.000000,     0.000000 ],
      [     0.000000,     0.000000,     1.000000,     0.000000 ],
      [     0.000000,     0.000000,     0.000000,     1.000000 ]]))

CON1_Base.setPose(Mat([[     1.000000,     0.000000,     0.000000,  -660.000000 ],
      [     0.000000,     1.000000,     0.000000, -1200.000000 ],
      [     0.000000,     0.000000,     1.000000,   130.000000 ],
      [     0.000000,     0.000000,     0.000000,     1.000000 ]]))

Table.setPose(Mat([[     1.000000,     0.000000,     0.000000,  -810.000000 ],
      [     0.000000,     1.000000,     0.000000, -980.000000 ],
      [     0.000000,     0.000000,     1.000000,     0.000000 ],
      [     0.000000,     0.000000,     0.000000,     1.000000 ]]))

Dobot_Base.setPose(Mat([[     0.000000,    -1.000000,     0.000000, -1020.000000 ],
      [     1.000000,     0.000000,     0.000000, -980.000000 ],
      [     0.000000,     0.000000,     1.000000,     50.000000 ],
      [     0.000000,     0.000000,     0.000000,     1.000000 ]]))

Warehouse.setPose(Mat([[     0.000000,    -1.000000,     0.000000, -1320.000000 ],
      [     1.000000,     0.000000,     0.000000, -890.000000 ],
      [     0.000000,     0.000000,     1.000000,    20.000000 ],
      [     0.000000,     0.000000,     0.000000,     1.000000 ]]))

Item.setPose(Mat([[     1.000000,    0.000000,     0.000000,  1930.000000 ],
      [     0.000000,     0.000000,     1.000000, 230.000000 ],
      [     0.000000,     -1.000000,     0.000000,   0.000000 ],
      [     0.000000,     0.000000,     0.000000,     1.000000 ]]))

Camera.setPose(Mat([[ 1.000000,  0.000000,   0.000000, -740.000000 ],
      [ 0.000000, -0.766044,   0.642788, -1090.000000 ],
      [ 0.000000, -0.642788,  -0.766044,  240.000000 ],
      [ 0.000000,  0.000000,   0.000000,    1.000000 ]]))

# ----------------------------------------------------------------
# 4. 내부 장치 및 관절각 초기화
# ----------------------------------------------------------------
if CON1.Valid():
    CON1.setPose(Mat([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]))

if Dobot.Valid():
    Dobot.setPose(Mat([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]))
    Dobot.setJoints([0, 0, 0, 0, 0])
