<template>
  <div id="app">
    <RouterView />
  </div>
</template>

<script setup>
import { RouterView } from 'vue-router'
</script>

<style>
/* 프로젝트 전체 기본 스타일링 */
#app {
  font-family: Arial, sans-serif;
  padding: 20px;
}
</style>