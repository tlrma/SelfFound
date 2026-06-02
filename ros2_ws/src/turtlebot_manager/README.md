# turtlebot_manager

분실물 시스템의 TurtleBot 자율주행 관리 패키지

## 패키지 구조

```
turtlebot_manager/
├── launch/
│   └── navigation.launch.py       # Gazebo + Nav2 + RViz2 통합 실행
├── maps/
│   ├── pjt_map.pgm                # SLAM으로 생성한 맵
│   └── pjt_map.yaml               # 맵 메타데이터
├── worlds/
│   └── lost_and_found.world       # 분실물 센터 Gazebo 맵
├── config/
│   └── named_poses.yaml           # 주요 위치 좌표
└── turtlebot_manager/
    └── navigate_to_named_pose.py  # named pose 이동 노드
```

## 환경 설정

```bash
export TURTLEBOT3_MODEL=waffle_pi
source ~/turtlebot3_ws/install/setup.bash
source ~/finalPJT/SelfFound/ros2_ws/install/setup.bash
```

## 실행 방법

### 1. Gazebo 시뮬레이션 실행

```bash
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py \
  world:=~/finalPJT/SelfFound/ros2_ws/install/turtlebot_manager/share/turtlebot_manager/worlds/lost_and_found.world
```

### 2. Nav2 실행

```bash
ros2 launch turtlebot3_navigation2 navigation2.launch.py \
  use_sim_time:=True \
  map:=~/finalPJT/SelfFound/ros2_ws/install/turtlebot_manager/share/turtlebot_manager/maps/pjt_map.yaml
```

### 3. RViz2에서 초기 위치 설정

- `2D Pose Estimate` 버튼 클릭
- 맵에서 TurtleBot 현재 위치에 클릭 후 드래그

### 4. Named Pose 이동

```bash
# Dobot 근처로 이동
ros2 run turtlebot_manager navigate_to_named_pose dobot_near

# 반환 창구로 이동
ros2 run turtlebot_manager navigate_to_named_pose return_counter

# 대기 위치로 이동
ros2 run turtlebot_manager navigate_to_named_pose waiting
```

## Named Poses

| 이름 | x | y | yaw | 설명 |
|------|---|---|-----|------|
| dobot_near | -0.876 | 0.82 | 1.5708 | Dobot 근처 (북쪽 방향) |
| return_counter | -3.09 | -1.21 | 3.1416 | 반환 창구 (서쪽 방향) |
| waiting | -0.254 | -1.79 | 1.5708 | 대기 위치 (북쪽 방향) |
