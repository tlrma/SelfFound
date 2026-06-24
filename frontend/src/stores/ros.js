import { defineStore } from 'pinia'
import { ref, shallowRef } from 'vue'
import * as ROSLIB from 'roslib'

const ROS_URL = 'ws://192.168.110.241:9091'

export const useRosStore = defineStore('ros', () => {
  const ros = shallowRef(null)
  const isConnected = ref(false)

  function connect() {
    if (isConnected.value) return

    ros.value = new ROSLIB.Ros({ url: ROS_URL })

    ros.value.on('connection', () => {
      isConnected.value = true
      console.log('[ROS] rosbridge 연결됨')
    })

    ros.value.on('error', (err) => {
      isConnected.value = false
      console.error('[ROS] 연결 오류:', err)
    })

    ros.value.on('close', () => {
      isConnected.value = false
      console.log('[ROS] rosbridge 연결 종료')
    })
  }

  function publish(topicName, messageType, data) {
    if (!isConnected.value) {
      console.warn('[ROS] 연결되지 않아 발행 실패:', topicName)
      return
    }
    const topic = new ROSLIB.Topic({ ros: ros.value, name: topicName, messageType })
    topic.publish(data)
    console.log('[ROS] 발행:', topicName, data)
  }

  function subscribe(topicName, messageType, callback) {
    if (!isConnected.value) {
      console.warn('[ROS] 연결되지 않아 구독 실패:', topicName)
      return null
    }
    const topic = new ROSLIB.Topic({ ros: ros.value, name: topicName, messageType })
    topic.subscribe((msg) => {
      console.log('[ROS] 수신:', topicName, msg)
      callback(msg)
    })
    return topic
  }

  return { ros, isConnected, connect, publish, subscribe }
})
