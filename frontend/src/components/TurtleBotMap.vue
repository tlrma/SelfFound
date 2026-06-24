<template>
  <div class="schematic-map">

    <!-- ── 좌측: 하드웨어 영역 ── -->
    <div class="alcove">
      <div class="zone zone-dobot" :class="{ active: dobotActive }">
        <span class="zone-name">Dobot</span>
      </div>

      <div class="alcove-mid">
        <div class="zone zone-camera" :class="{ active: cameraActive, 'has-error': hasCameraError }">
          <span class="zone-name">카메라</span>
          <div v-if="hasCameraError" class="err-badge">⚠ 인식 오류</div>
        </div>
        <div class="zone zone-desk">
          <span class="zone-name">책상</span>
        </div>
      </div>

      <div class="zone zone-conveyor" :class="{ active: conveyorActive }">
        <span class="zone-name">컨베이어<br>벨트</span>
      </div>
    </div>

    <!-- ── 우측: 터틀봇 이동 구역 ── -->
    <div class="main-room">

      <!-- 터틀봇 실시간 위치 마커 (연결 시) -->
      <div v-if="turtlePose" class="tb-marker" :style="turtlebotStyle">
        <div class="tb-ring" :class="{ moving: turtlebotActive }"></div>
        <div class="tb-body" :style="{ transform: `rotate(${turtleYawDeg}deg)` }">
          <div class="tb-arrow"></div>
        </div>
      </div>

      <!-- 기본 대기 위치 마커 (미연결 또는 위치 미수신 시) -->
      <div v-else class="tb-marker tb-marker--idle" :style="idleMarkerStyle">
        <div class="tb-body tb-body--idle"></div>
      </div>

      <!-- 연결/수신 상태 메시지 -->
      <div v-if="!rosConnected" class="room-msg">ROS 연결 대기중...</div>
      <div v-else-if="!turtlePose" class="room-msg">위치 수신 대기중...</div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import * as ROSLIB from 'roslib'
import { useRosStore } from '@/stores/ros'

const props = defineProps({
  turtlebotActive:{ type: Boolean, default: false },
  conveyorActive: { type: Boolean, default: false },
  cameraActive:   { type: Boolean, default: false },
  hasCameraError: { type: Boolean, default: false },
})

/* ── 터틀봇이 다니는 메인 룸 ROS 좌표 범위 ── */
/* named_poses 기준: dobot_near(0.25,1.11) ~ waiting(1.41,1.21) ~ return_counter(1.32,0.003) */
const ROOM = { xMin: 0.0, xMax: 1.6, yMin: -0.1, yMax: 1.35 }

function rosToRoom(rx, ry) {
  const left = Math.max(2, Math.min(96, (rx - ROOM.xMin) / (ROOM.xMax - ROOM.xMin) * 100))
  const top  = Math.max(2, Math.min(96, (ROOM.yMax - ry) / (ROOM.yMax - ROOM.yMin) * 100))
  return { left: `${left}%`, top: `${top}%` }
}

/* ── 상태 ── */
const rosStore    = useRosStore()
const rosConnected = computed(() => rosStore.isConnected)
const turtlePose  = ref(null)     // { x, y, yaw }
const dobotActive = ref(false)    // /dobot_task_targets → true, /dobot_status done:* → false

const turtlebotStyle = computed(() => {
  if (!turtlePose.value) return {}
  const p = rosToRoom(turtlePose.value.x, turtlePose.value.y)
  return { left: p.left, top: p.top }
})

const idleMarkerStyle = computed(() => rosToRoom(1.41, 1.21))

const turtleYawDeg = computed(() => {
  if (!turtlePose.value?.yaw) return 0
  return -turtlePose.value.yaw * 180 / Math.PI
})

/* ── ROS 토픽 ── */
let amclTopic        = null
let dobotTargetTopic = null
let dobotStatusTopic = null
let stopWatch        = null

function quatToYaw({ x, y, z, w }) {
  return Math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
}

function subscribeAll() {
  if (!rosStore.ros) return

  amclTopic = new ROSLIB.Topic({
    ros:         rosStore.ros,
    name:        '/amcl_pose',
    messageType: 'geometry_msgs/PoseWithCovarianceStamped',
    throttle_rate: 0,
  })
  amclTopic.subscribe((msg) => {
    const pos = msg.pose.pose.position
    const ori = msg.pose.pose.orientation
    turtlePose.value = { x: pos.x, y: pos.y, yaw: quatToYaw(ori) }
  })

  // 두봇 작업 시작: /dobot_task_targets 수신 시 active
  dobotTargetTopic = new ROSLIB.Topic({
    ros:         rosStore.ros,
    name:        '/dobot_task_targets',
    messageType: 'std_msgs/Float64MultiArray',
  })
  dobotTargetTopic.subscribe(() => { dobotActive.value = true })

  // 두봇 작업 완료: /dobot_status "done:*" 수신 시 inactive
  dobotStatusTopic = new ROSLIB.Topic({
    ros:         rosStore.ros,
    name:        '/dobot_status',
    messageType: 'std_msgs/String',
  })
  dobotStatusTopic.subscribe((msg) => {
    if (msg.data.startsWith('done:')) dobotActive.value = false
  })
}

onMounted(() => {
  rosStore.connect()
  stopWatch = watch(
    () => rosStore.isConnected,
    (ok) => { if (ok) subscribeAll() },
    { immediate: true },
  )
})

onUnmounted(() => {
  amclTopic?.unsubscribe()
  dobotTargetTopic?.unsubscribe()
  dobotStatusTopic?.unsubscribe()
  stopWatch?.()
})
</script>

<style scoped>
/* ── 전체 컨테이너 ── */
.schematic-map {
  display: flex;
  height: 320px;
  border: 2px solid #1e293b;
  border-radius: 10px;
  background: #fff;
  overflow: hidden;
  font-size: 11px;
}

/* ── 좌측 알코브 ── */
.alcove {
  display: flex;
  flex-direction: column;
  width: 21%;
  border-right: 2px solid #1e293b;
  flex-shrink: 0;
}

.alcove-mid {
  display: flex;
  flex: 0 0 20%;
  border-bottom: 1px solid #cbd5e1;
}

/* ── 공통 zone ── */
.zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 6px 4px;
  position: relative;
  transition: background 0.25s, outline 0.25s;
}

.zone-name {
  font-weight: 700;
  color: #374151;
  text-align: center;
  line-height: 1.3;
}

/* active: 빨간 테두리 */
.zone.active {
  background: #fff5f5;
  outline: 2px solid #dc2626;
  outline-offset: -2px;
  border-radius: 2px;
}

/* error: 빨간 배경 강조 */
.zone.has-error {
  background: #fef2f2;
  outline: 2px solid #dc2626;
  outline-offset: -2px;
}

.err-badge {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  background: #dc2626;
  color: #fff;
  font-size: 9px;
  font-weight: 800;
  padding: 2px 5px;
  border-radius: 3px;
  margin-top: 2px;
}

/* 개별 zone 비율 */
.zone-dobot    { flex: 0 0 20%; border-bottom: 1px solid #cbd5e1; }
.zone-camera   { flex: 1; border-right: 1px solid #cbd5e1; }
.zone-desk     { flex: 1; }
.zone-conveyor { flex: 1; }

/* ── 우측 메인 룸 ── */
.main-room {
  flex: 1;
  position: relative;
  overflow: hidden;
  background: #f8fafc;
}

/* 터틀봇 마커 공통 */
.tb-marker {
  position: absolute;
  width: 0;
  height: 0;
  pointer-events: none;
}

.tb-ring {
  position: absolute;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(220, 38, 38, 0.15);
  transform: translate(-50%, -50%);
  transition: background 0.3s;
}

.tb-ring.moving {
  animation: tb-pulse 1.4s ease-out infinite;
}

@keyframes tb-pulse {
  0%   { box-shadow: 0 0 0 0   rgba(220, 38, 38, 0.4); }
  70%  { box-shadow: 0 0 0 10px rgba(220, 38, 38, 0); }
  100% { box-shadow: 0 0 0 0   rgba(220, 38, 38, 0); }
}

.tb-body {
  position: absolute;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #dc2626;
  border: 2px solid #fff;
  box-shadow: 0 1px 4px rgba(0,0,0,0.25);
  transform: translate(-50%, -50%);
  display: flex;
  align-items: flex-start;
  justify-content: center;
}

/* 미연결 시 검정 마커 */
.tb-body--idle {
  background: #374151;
  border-color: #fff;
  box-shadow: 0 1px 4px rgba(0,0,0,0.3);
}

.tb-arrow {
  width: 0;
  height: 0;
  border-left: 3px solid transparent;
  border-right: 3px solid transparent;
  border-bottom: 5px solid #fff;
  margin-top: 1px;
}

/* 상태 메시지 */
.room-msg {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  color: #94a3b8;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}
</style>
