# SelfFound

멀티로봇 협업 기반 분실물 관리 시스템.
습득자가 키오스크에 물건을 두면 비전 AI가 물건을 인식하고, Dobot이 창고에 적재한 뒤, 신고자와 매칭되면 TurtleBot이 반환 창구까지 운반합니다.

---

## 1. 프로젝트 개요

기존 분실물 처리는 사람이 물건을 분류하고 보관하며, 신고 내용과 하나하나 대조해야 하는 수작업 위주로 이루어집니다. SelfFound는 이 과정을 **비전 인식 + 매니퓰레이터 + 자율주행 로봇**의 협업으로 자동화한 무인 분실물 센터입니다.

### 주요 기능

- **분실 신고 접수**: 웹에서 카테고리, 시간, 장소, 특징을 입력받아 저장
- **습득물 입고**: 키오스크에서 음성으로 습득 정보를 입력받고, 컨베이어를 통해 인식 위치로 이송
- **비전 인식**: RealSense 카메라가 촬영한 이미지를 YOLO로 분류하고, LLM이 자연어 설명을 생성
- **자동 매칭**: 새로 등록된 물건 또는 신고와 유사도가 높은 항목을 자동으로 찾아 신고자에게 인증코드가 포함된 메일 발송
- **무인 수령**: 인증코드 확인 후 TurtleBot이 창고에서 물건을 받아 반환 창구로 운반, 본인 확인 후 수령
- **관리자 대시보드**: 신고·습득물·매칭 후보·창고 슬롯·로봇 상태를 실시간으로 확인하고 관제

### 팀 구성

| 이름 | 담당 |
| --- | --- |
| 서진 | Dobot, DB, 프론트엔드, 백엔드, 서버 통신, 키오스크 |
| 시은 | TurtleBot, CV/AI, 매칭 알고리즘 |

---

## 2. 프로젝트 실행 명령어

전체 시스템은 여러 컴포넌트가 함께 동작해야 하므로, 아래 순서대로 각각의 터미널에서 실행합니다.

### 사전 준비

```bash
# 저장소 클론
git clone https://github.com/tlrma/SelfFound.git
cd SelfFound
```

환경변수는 `backend/.env`, `frontend/.env` 파일에 각각 설정합니다. `.env.example` 파일을 참고해 SMTP 계정, DB 경로, ROS bridge 주소 등을 채워주세요.

### 백엔드 (Django)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows는 .venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser  # 관리자 계정 생성 (선택)
python manage.py runserver 0.0.0.0:8000
```

### 프론트엔드 (Vue)

```bash
cd frontend
npm install
npm run dev
```

기본 접속 주소는 `http://localhost:5173` 입니다. 주요 경로는 다음과 같습니다.

| 경로 | 설명 |
| --- | --- |
| `/` | 분실 신고 폼 |
| `/status/:id` | 신고 상태 및 매칭 결과 |
| `/auth` → `/my-reports` | 내 신고 내역 조회 |
| `/admin` | 관리자 대시보드 |
| `/kiosk/deposit` | 습득물 입고 키오스크 |
| `/kiosk/pickup` | 분실물 수령 키오스크 |

### ROS 2 워크스페이스 빌드

```bash
cd ros2_ws
colcon build
source install/setup.bash
```

### TurtleBot 자율주행

```bash
export TURTLEBOT3_MODEL=waffle_pi

# Gazebo 시뮬레이션
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py \
  world:=$(ros2 pkg prefix turtlebot_manager)/share/turtlebot_manager/worlds/lost_and_found.world

# Nav2
ros2 launch turtlebot3_navigation2 navigation2.launch.py \
  use_sim_time:=True \
  map:=$(ros2 pkg prefix turtlebot_manager)/share/turtlebot_manager/maps/pjt_map.yaml

# Named pose 이동 서버
ros2 run turtlebot_manager navigation_server
```

RViz에서 `2D Pose Estimate`로 초기 위치를 지정한 뒤 사용하세요.

### Dobot 매니퓰레이터

```bash
ros2 run dobot_manager dobot_task_manager
```

### 비전 감지 노드 (RealSense + YOLO + LLM)

```bash
ros2 run lost_item_detector detector_node
```

### rosbridge

프론트엔드와 ROS 간 WebSocket 통신을 위한 브릿지를 띄웁니다.

```bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml port:=9092
```

### Modbus 서버 & 컨베이어 클라이언트

```bash
# Modbus TCP 서버
python modbus/server.py

# 컨베이어 벨트 (라즈베리파이/모터 연결 노드)
python hardware/conveyor_belt/modbus_client.py
```

---

## 3. 프로젝트 아키텍처

### 3-1. 전체 구조

Django 백엔드가 단일 진실 원천(single source of truth) 역할을 하며, 모든 서브시스템은 백엔드를 통해 데이터와 작업 명령을 주고받습니다.

```
[사용자 계층]
  Vue 웹 · 입고/수령 키오스크
        │  REST API · WebSocket
        ▼
[제어·데이터 계층]
  Django + DRF + Channels
        │  ORM
        ▼
      Database (Report / Item / MatchResult / WarehouseSlot / Alert)

[제어·데이터 계층]  ─ rosbridge WebSocket ─▶  [로봇·하드웨어 계층]
                                             Vision (RealSense, YOLO, LLM)
                                             Dobot Manager (ROS 2)
                                             TurtleBot Manager (Nav2, AMCL)
                                             Modbus TCP → 컨베이어 벨트
```

### 3-2. 폴더 구조

```
SelfFound/
├── backend/                 # Django + DRF
│   ├── apps/
│   │   ├── reports/         # 분실 신고
│   │   ├── items/           # 습득물 등록·저장
│   │   ├── matching/        # 매칭 알고리즘·메일 발송
│   │   ├── pickup/          # 수령 인증·완료 처리
│   │   ├── robot_tasks/     # 컨베이어 트리거·STT 큐
│   │   ├── warehouse/       # 창고 슬롯 관리
│   │   └── admin_panel/     # 시스템 알림
│   └── manage.py
├── frontend/                # Vue 3 + Vue Router + Axios
│   └── src/
│       ├── views/           # 화면별 컴포넌트
│       ├── components/      # TurtleBotMap 등 공용 컴포넌트
│       └── stores/          # ROS 연결 등 상태 관리
├── ros2_ws/
│   └── src/
│       ├── dobot_manager/           # Pick & Place 시퀀스
│       ├── turtlebot_manager/       # Named pose 기반 자율주행
│       └── lost_item_detector/      # RealSense + 비전 파이프라인
├── vision/                  # YOLO 학습·비전 파이프라인
│   └── pipeline/
├── hardware/
│   └── conveyor_belt/       # 라즈베리파이 GPIO + Modbus 클라이언트
├── modbus/                  # Modbus TCP 서버
├── test-matching/           # 매칭 알고리즘 테스트 스크립트
└── docs/                    # 기술 문서
```

### 3-3. 통신 인터페이스

| 인터페이스 | 사용처 |
| --- | --- |
| REST (HTTP) | 프론트엔드 ↔ 백엔드, 키오스크 ↔ 백엔드 |
| WebSocket | 실시간 로봇 상태 모니터링 (Django Channels) |
| rosbridge WebSocket | 프론트엔드/백엔드 ↔ ROS 2 노드 (기본 포트 9092) |
| ROS 2 토픽/서비스/액션 | 로봇 내부 통신 |
| Modbus TCP | 백엔드/감지 노드 ↔ 컨베이어 벨트 (포트 5020) |
| SMTP | 매칭 결과 메일 발송 |
| Serial (RS-232) | Dobot 시리얼 옵션 |

### 3-4. 핵심 데이터 흐름

**입고 흐름**

```
키오스크 STT → Django (found_info 큐)
  → Modbus reg[0]=1 → 컨베이어 이동
  → IR 센서 감지 → Modbus reg[1]=1
  → RealSense 촬영 → YOLO 분류 + LLM 묘사
  → Django Item 생성 + 빈 창고 슬롯 할당
  → Dobot 창고 적재 (pick & place)
  → 기존 신고와 매칭 → 매칭 성공 시 SMTP 발송
```

**반환 흐름**

```
웹 신고 접수 → 매칭 검색 (카테고리 + 시간/장소 + 묘사 유사도)
  → 매칭 성공 시 인증코드 + 메일 발송
  → 분실자 방문 → 수령 키오스크 인증코드 입력
  → 수령자 사진 촬영 → Django 저장
  → TurtleBot Dobot 근처 이동 → Dobot 슬롯에서 꺼내 TurtleBot에 적재
  → TurtleBot 반환 창구 이동 → 본인 확인 후 수령
  → status = completed, 창고 슬롯 해제
  → 거부 시: TurtleBot 창고 복귀 → Dobot 재적재
```

**상태 머신**

| 대상 | 상태 값 |
| --- | --- |
| Report | `searching` → `review` → `matched` → `processing` → `completed` |
| Item | `stored` → `matched` → `returned` / `expired` → `discarded` |
| WarehouseSlot | `is_occupied` + `item` 참조로 점유 여부 관리 |

---

## 4. 기술 스택

| 영역 | 사용 기술 |
| --- | --- |
| Frontend | Vue 3, Vue Router, Axios, Chart.js, WebSocket |
| Backend | Django, Django REST Framework, Django Channels |
| Database | SQLite (개발) |
| AI · Vision | YOLOv8 (PyTorch), OpenCV, LLM, Roboflow |
| Robot · ROS | ROS 2 Humble, Nav2, AMCL, slam_toolbox, Dobot Python SDK |
| Simulation | Gazebo, RViz, URDF, RoboDK |
| Voice | Web Speech API (STT), Coqui TTS / gTTS |
| Communication | REST, WebSocket, rosbridge_suite, Modbus TCP, SMTP |
| Hardware | Dobot Magician / MG400, TurtleBot3, RealSense, Raspberry Pi + 스텝모터 |
| Mechanical | Onshape 설계, 3D 프린팅 (STL) |

---

## 5. 확장성

현재 구현은 소규모 시연 환경(창고 5×5 슬롯, 로봇 1대씩)을 기준으로 설계되었지만, 구조상 다음과 같은 확장이 가능합니다.

### 5-1. 로봇 대수 확장

- **다수 TurtleBot 운용**: Named pose와 Nav2 액션은 로봇 네임스페이스 단위로 분리 가능하므로, 여러 대의 TurtleBot을 창고 구역별로 담당하도록 배치할 수 있습니다.
- **다수 Dobot 운용**: 창고를 여러 구역으로 나누고 각 구역별로 Dobot을 배치하면 병목을 줄일 수 있습니다. 백엔드의 `robot_tasks` 큐를 로봇 ID 단위로 분리하도록 확장하면 됩니다.

### 5-2. 창고 규모 확장

- `WarehouseSlot` 모델과 `SLOT_COORDINATES` 매핑을 확장하면 슬롯 수를 늘릴 수 있습니다. 슬롯 좌표는 DB에 저장되어 있어 코드 수정 없이 좌표만 추가하면 됩니다.
- 관리자 대시보드의 5×5 그리드 뷰도 슬롯 수에 맞춰 자동으로 확장되도록 컴포넌트를 일반화하면 대규모 창고에도 대응할 수 있습니다.

### 5-3. 카테고리 및 매칭 고도화

- YOLO 모델은 Roboflow에서 재학습해 카테고리를 확장할 수 있습니다.
- 매칭 알고리즘은 LLM 기반 유사도 비교를 사용하므로, 프롬프트를 수정하거나 다른 임베딩 모델을 붙이는 것만으로 성능을 개선할 수 있습니다. 자동 매칭·검토·미매칭의 임계값은 백엔드 상수로 분리되어 있어 운영 데이터를 반영해 튜닝할 수 있습니다.

### 5-4. 실운영 대비 보완 지점

- **인증 강화**: 현재는 이름·이메일로 신고 내역을 조회하는 구조이므로, 실운영 시에는 OAuth 또는 이메일 인증 토큰 방식으로 보완이 필요합니다.
- **DB 이전**: 개발용 SQLite를 MySQL/PostgreSQL 등으로 전환하고, `found_info` 임시 큐도 Redis 기반으로 이전하면 서버 재시작·다중 프로세스 환경에서도 안정적으로 동작합니다.
- **비전 오검출 대응**: 관리자 알림 채널과 수동 재분류 UI가 이미 마련되어 있어, 오검출 발생 시 관리자가 개입하는 절차를 그대로 활용할 수 있습니다.
- **개인정보 보호**: 신분증 OCR 및 마스킹, TTL 기반 자동 삭제, 감사 로그 유지 등 개인정보 처리 방침을 이미 설계에 반영해두었으며, 실운영 시 법적 요건에 맞춰 구체화할 수 있습니다.

### 5-5. 시뮬레이션과 실기의 일치

시뮬레이션(Gazebo + RoboDK)에서 검증한 좌표와 동작 시퀀스를 실기에 그대로 이식할 수 있도록 설계되어 있습니다. 실기 환경 이관 시에는 카메라 캘리브레이션과 Named pose 좌표만 재조정하면 되며, 상위 로직은 그대로 유지됩니다.

---

## 6. 참고 문서

- `docs/` — 기술 스택 및 구조 설계, 4주 개발 일정
- `test-matching/results/` — LLM 매칭 알고리즘 테스트 결과
- 각 ROS 2 패키지 내부 `README.md` — 노드별 사용법
