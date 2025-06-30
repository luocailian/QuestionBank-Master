<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

onMounted(() => {
  // 应用启动时检查登录状态
  authStore.checkAuth()
})
</script>

<style>
#app {
  min-height: 100vh;
  background-color: var(--el-bg-color-page);
}
</style>
