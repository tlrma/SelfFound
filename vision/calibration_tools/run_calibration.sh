#!/bin/bash
# 시스템 Python3(GTK3 cv2) + ROS2 환경을 함께 사용

source /opt/ros/humble/setup.bash

# ROS Python 패키지 경로 수집
ROS_PYTHON_PATH=$(python3 -c "import sys; print(':'.join(sys.path))" 2>/dev/null)

# 시스템 cv2(GTK3) 경로를 앞에 추가
PYTHONPATH="/usr/lib/python3/dist-packages:${ROS_PYTHON_PATH}:/home/ssafy/finalPJT/SelfFound/vision" \
  /usr/bin/python3 "$(dirname "$0")/capture_and_calibrate.py"
