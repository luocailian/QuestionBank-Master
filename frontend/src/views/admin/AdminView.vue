<template>
  <div class="admin-page">
    <div class="admin-layout">
      <!-- 侧边栏 -->
      <div class="admin-sidebar">
        <div class="sidebar-header">
          <h2>管理后台</h2>
        </div>
        
        <el-menu
          :default-active="activeMenu"
          class="admin-menu"
          @select="handleMenuSelect"
        >
          <el-menu-item index="dashboard">
            <el-icon><Odometer /></el-icon>
            <span>数据概览</span>
          </el-menu-item>
          
          <el-menu-item index="users">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
          
          <el-menu-item index="banks">
            <el-icon><Document /></el-icon>
            <span>题库管理</span>
          </el-menu-item>
          
          <el-menu-item index="questions">
            <el-icon><Edit /></el-icon>
            <span>题目管理</span>
          </el-menu-item>
          
          <el-menu-item index="files">
            <el-icon><Upload /></el-icon>
            <span>文件管理</span>
          </el-menu-item>
          
          <el-menu-item index="settings">
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </el-menu-item>
        </el-menu>
      </div>
      
      <!-- 主内容区 -->
      <div class="admin-main">
        <div class="admin-header">
          <div class="header-left">
            <h1>{{ getPageTitle() }}</h1>
          </div>
          
          <div class="header-right">
            <el-button
              :icon="isAutoRefresh ? 'Refresh' : 'RefreshLeft'"
              :type="isAutoRefresh ? 'primary' : 'default'"
              @click="toggleAutoRefresh"
              size="small"
            >
              {{ isAutoRefresh ? '自动刷新' : '手动刷新' }}
            </el-button>
            <el-button @click="refreshAllData" size="small">
              立即刷新
            </el-button>
            <el-button @click="$router.push('/')">
              返回前台
            </el-button>
            <el-dropdown @command="handleUserAction">
              <span class="user-dropdown">
                <el-avatar :src="authStore.user?.avatar_url" :size="32">
                  {{ authStore.user?.username?.charAt(0).toUpperCase() }}
                </el-avatar>
                <span class="username">{{ authStore.user?.username }}</span>
                <el-icon><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">个人资料</el-dropdown-item>
                  <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
        
        <div class="admin-content">
          <!-- 数据概览 -->
          <div v-if="activeMenu === 'dashboard'" class="dashboard-content">
            <div class="stats-grid">
              <div class="stat-card">
                <div class="stat-icon">
                  <el-icon size="32" color="#409eff"><User /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-number">{{ stats.totalUsers }}</div>
                  <div class="stat-label">总用户数</div>
                </div>
              </div>
              
              <div class="stat-card">
                <div class="stat-icon">
                  <el-icon size="32" color="#67c23a"><Document /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-number">{{ stats.totalBanks }}</div>
                  <div class="stat-label">题库总数</div>
                </div>
              </div>
              
              <div class="stat-card">
                <div class="stat-icon">
                  <el-icon size="32" color="#e6a23c"><Edit /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-number">{{ stats.totalQuestions }}</div>
                  <div class="stat-label">题目总数</div>
                </div>
              </div>
              
              <div class="stat-card">
                <div class="stat-icon">
                  <el-icon size="32" color="#f56c6c"><TrendCharts /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-number">{{ stats.totalAnswers }}</div>
                  <div class="stat-label">答题总数</div>
                </div>
              </div>
            </div>
            
            <!-- 最近活动 -->
            <div class="recent-activity">
              <div class="activity-header">
                <h3>最近活动</h3>
                <div class="refresh-status">
                  <div class="update-time" v-if="lastUpdateTime">
                    <span class="time-label">最后更新:</span>
                    <span class="time-value">{{ lastUpdateTime }}</span>
                  </div>
                  <el-tag
                    :type="isAutoRefresh ? 'success' : 'info'"
                    size="small"
                    effect="light"
                  >
                    <el-icon class="refresh-icon" :class="{ 'rotating': isAutoRefresh }">
                      <Refresh />
                    </el-icon>
                    {{ isAutoRefresh ? '实时同步' : '手动刷新' }}
                  </el-tag>
                </div>
              </div>
              <div class="activity-list">
                <div 
                  v-for="activity in recentActivities" 
                  :key="activity.id"
                  class="activity-item"
                >
                  <div class="activity-icon">
                    <el-icon><Bell /></el-icon>
                  </div>
                  <div class="activity-content">
                    <p>{{ activity.description }}</p>
                    <span class="activity-time">{{ formatDate(activity.created_at) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 其他页面内容 -->
          <div v-else class="page-content">
            <component :is="getCurrentComponent()" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Odometer, User, Document, Edit, Upload, Setting,
  ArrowDown, Bell, TrendCharts, Refresh
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import UserManageView from './UserManageView.vue'
import BankManageView from './BankManageView.vue'
import { getAdminStats, getRecentActivities, type RecentActivity } from '@/api/admin'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = ref('dashboard')
const stats = ref({
  totalUsers: 0,
  totalBanks: 0,
  totalQuestions: 0,
  totalAnswers: 0
})

const recentActivities = ref<RecentActivity[]>([])
const refreshInterval = ref<number | null>(null)
const isAutoRefresh = ref(true)
const lastUpdateTime = ref<string>('')

const getPageTitle = () => {
  const titles = {
    dashboard: '数据概览',
    users: '用户管理',
    banks: '题库管理',
    questions: '题目管理',
    files: '文件管理',
    settings: '系统设置'
  }
  return titles[activeMenu.value as keyof typeof titles] || '管理后台'
}

const getCurrentComponent = () => {
  const components = {
    users: UserManageView,
    banks: BankManageView,
    questions: 'div', // 暂时占位
    files: 'div',
    settings: 'div'
  }
  return components[activeMenu.value as keyof typeof components] || 'div'
}

const handleMenuSelect = (index: string) => {
  activeMenu.value = index
  router.push(`/admin/${index}`)
}

const handleUserAction = (command: string) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'logout':
      authStore.logout()
      router.push('/')
      break
  }
}

const formatDate = (dateString: string) => {
  const now = dayjs()
  const date = dayjs(dateString)
  const diffMinutes = now.diff(date, 'minute')
  const diffHours = now.diff(date, 'hour')
  const diffDays = now.diff(date, 'day')

  if (diffMinutes < 1) {
    return '刚刚'
  } else if (diffMinutes < 60) {
    return `${diffMinutes}分钟前`
  } else if (diffHours < 24) {
    return `${diffHours}小时前`
  } else if (diffDays < 7) {
    return `${diffDays}天前`
  } else {
    return date.format('YYYY-MM-DD HH:mm')
  }
}

const fetchStats = async () => {
  try {
    const data = await getAdminStats()
    stats.value = data
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

const fetchRecentActivities = async () => {
  try {
    const activities = await getRecentActivities()
    recentActivities.value = activities
  } catch (error) {
    console.error('获取最近活动失败:', error)
  }
}

// 刷新所有数据
const refreshAllData = async () => {
  await Promise.all([
    fetchStats(),
    fetchRecentActivities()
  ])
  // 更新最后刷新时间
  lastUpdateTime.value = dayjs().format('YYYY-MM-DD HH:mm:ss')
}

// 启动自动刷新
const startAutoRefresh = () => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
  }

  if (isAutoRefresh.value) {
    refreshInterval.value = setInterval(() => {
      refreshAllData()
    }, 30000) // 每30秒刷新一次
  }
}

// 停止自动刷新
const stopAutoRefresh = () => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
    refreshInterval.value = null
  }
}

// 切换自动刷新状态
const toggleAutoRefresh = () => {
  isAutoRefresh.value = !isAutoRefresh.value
  if (isAutoRefresh.value) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}

onMounted(() => {
  // 根据路由设置当前菜单
  const path = route.path.split('/').pop()
  if (path && path !== 'admin') {
    activeMenu.value = path
  }

  // 初始加载数据
  refreshAllData()

  // 启动自动刷新
  startAutoRefresh()
})

onUnmounted(() => {
  // 清理定时器
  stopAutoRefresh()
})
</script>

<style scoped>
.admin-page {
  min-height: 100vh;
  background-color: var(--background-base);
}

.admin-layout {
  display: flex;
  min-height: 100vh;
}

.admin-sidebar {
  width: 250px;
  background: white;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
  position: fixed;
  height: 100vh;
  overflow-y: auto;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid var(--border-light);
}

.sidebar-header h2 {
  margin: 0;
  color: var(--text-primary);
  font-size: 18px;
}

.admin-menu {
  border: none;
}

.admin-menu .el-menu-item {
  height: 50px;
  line-height: 50px;
}

.admin-main {
  flex: 1;
  margin-left: 250px;
  display: flex;
  flex-direction: column;
}

.admin-header {
  background: white;
  padding: 0 24px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left h1 {
  margin: 0;
  font-size: 20px;
  color: var(--text-primary);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: background-color 0.3s;
}

.user-dropdown:hover {
  background-color: var(--background-base);
}

.username {
  font-size: 14px;
  color: var(--text-primary);
}

.admin-content {
  flex: 1;
  padding: 24px;
}

.dashboard-content {
  max-width: 1200px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: var(--shadow-base);
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-info {
  flex: 1;
}

.stat-number {
  font-size: 28px;
  font-weight: bold;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.recent-activity {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: var(--shadow-base);
}

.activity-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.activity-header h3 {
  margin: 0;
  color: var(--text-primary);
}

.refresh-status {
  display: flex;
  align-items: center;
  gap: 12px;
}

.update-time {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.time-label {
  color: var(--text-secondary);
}

.time-value {
  color: var(--text-primary);
  font-weight: 500;
}

.refresh-icon {
  transition: transform 0.3s ease;
}

.refresh-icon.rotating {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.activity-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  transition: background-color 0.3s;
}

.activity-item:hover {
  background-color: var(--background-base);
}

.activity-icon {
  color: var(--primary-color);
  margin-top: 2px;
}

.activity-content {
  flex: 1;
}

.activity-content p {
  margin: 0 0 4px 0;
  color: var(--text-primary);
  line-height: 1.5;
}

.activity-time {
  font-size: 12px;
  color: var(--text-secondary);
}

.page-content {
  max-width: 1200px;
}

@media (max-width: 768px) {
  .admin-sidebar {
    transform: translateX(-100%);
    transition: transform 0.3s;
  }
  
  .admin-main {
    margin-left: 0;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .admin-header {
    padding: 0 16px;
  }
  
  .admin-content {
    padding: 16px;
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .header-right {
    flex-direction: column;
    gap: 8px;
  }
}
</style>
