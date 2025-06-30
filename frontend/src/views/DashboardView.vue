<template>
  <div class="dashboard-page">
    <!-- 顶部导航 -->
    <div class="dashboard-header">
      <div class="container">
        <div class="header-content">
          <div class="brand">
            <router-link to="/" class="brand-link">
              <h1>QuestionBank Master</h1>
            </router-link>
          </div>
          
          <div class="header-actions">
            <el-button @click="$router.push('/banks')">浏览题库</el-button>
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
                  <el-dropdown-item command="favorites">我的收藏</el-dropdown-item>
                  <el-dropdown-item command="admin" v-if="authStore.isAdmin">管理后台</el-dropdown-item>
                  <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
    </div>

    <div class="dashboard-content">
      <div class="container">
        <!-- 欢迎区域 -->
        <div class="welcome-section">
          <h2>欢迎回来，{{ authStore.user?.username }}！</h2>
          <p>继续你的学习之旅</p>
        </div>

        <!-- 统计卡片 -->
        <div class="stats-grid" v-if="statistics">
          <div class="stats-card">
            <div class="stats-icon">
              <el-icon size="32"><Document /></el-icon>
            </div>
            <div class="stats-content">
              <div class="stats-number">{{ statistics.total_banks }}</div>
              <div class="stats-label">参与题库</div>
            </div>
          </div>
          
          <div class="stats-card">
            <div class="stats-icon">
              <el-icon size="32"><Edit /></el-icon>
            </div>
            <div class="stats-content">
              <div class="stats-number">{{ statistics.total_answers }}</div>
              <div class="stats-label">答题总数</div>
            </div>
          </div>
          
          <div class="stats-card">
            <div class="stats-icon">
              <el-icon size="32"><Check /></el-icon>
            </div>
            <div class="stats-content">
              <div class="stats-number">{{ statistics.correct_answers }}</div>
              <div class="stats-label">正确答题</div>
            </div>
          </div>
          
          <div class="stats-card">
            <div class="stats-icon">
              <el-icon size="32"><Trophy /></el-icon>
            </div>
            <div class="stats-content">
              <div class="stats-number">{{ statistics.accuracy_rate }}%</div>
              <div class="stats-label">正确率</div>
            </div>
          </div>
        </div>

        <!-- 主要内容区域 -->
        <div class="main-content">
          <!-- 学习进度 -->
          <div class="content-section">
            <div class="section-header">
              <h3>学习进度</h3>
              <el-button @click="$router.push('/banks')">查看更多</el-button>
            </div>
            
            <div class="progress-list" v-if="statistics?.progress?.length">
              <div 
                v-for="progress in statistics.progress.slice(0, 5)" 
                :key="progress.id"
                class="progress-item"
                @click="$router.push(`/banks/${progress.bank_id}`)"
              >
                <div class="progress-info">
                  <h4>{{ progress.bank_name }}</h4>
                  <div class="progress-meta">
                    <span>{{ progress.answered_questions }}/{{ progress.total_questions }} 题</span>
                    <span>正确率: {{ progress.accuracy_rate }}%</span>
                  </div>
                </div>
                <div class="progress-bar">
                  <el-progress 
                    :percentage="progress.progress_rate" 
                    :show-text="false"
                    :stroke-width="8"
                  />
                </div>
              </div>
            </div>
            
            <div v-else class="empty-state">
              <el-icon size="64"><Document /></el-icon>
              <p>还没有学习记录</p>
              <el-button type="primary" @click="$router.push('/banks')">
                开始学习
              </el-button>
            </div>
          </div>

          <!-- 快速操作 -->
          <div class="content-section">
            <div class="section-header">
              <h3>快速操作</h3>
            </div>
            
            <div class="quick-actions">
              <div class="action-card" @click="$router.push('/banks')">
                <div class="action-icon">
                  <el-icon size="32"><Search /></el-icon>
                </div>
                <h4>浏览题库</h4>
                <p>发现更多有趣的题库</p>
              </div>
              
              <div class="action-card" @click="$router.push('/favorites')">
                <div class="action-icon">
                  <el-icon size="32"><Star /></el-icon>
                </div>
                <h4>我的收藏</h4>
                <p>查看收藏的题目</p>
              </div>
              
              <div class="action-card" @click="showUploadDialog = true">
                <div class="action-icon">
                  <el-icon size="32"><Upload /></el-icon>
                </div>
                <h4>导入题库</h4>
                <p>上传文件创建题库</p>
              </div>
              
              <div class="action-card" @click="$router.push('/profile')">
                <div class="action-icon">
                  <el-icon size="32"><User /></el-icon>
                </div>
                <h4>个人设置</h4>
                <p>管理个人信息</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 文件上传对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="导入题库"
      width="500px"
    >
      <FileUpload @success="handleUploadSuccess" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  ArrowDown, Document, Edit, Check, Trophy, 
  Search, Star, Upload, User 
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { usersApi } from '@/api/users'
import FileUpload from '@/components/FileUpload.vue'
import type { UserStatistics } from '@/types/auth'

const router = useRouter()
const authStore = useAuthStore()

const statistics = ref<UserStatistics | null>(null)
const showUploadDialog = ref(false)
const loading = ref(false)

const handleUserAction = (command: string) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'favorites':
      router.push('/favorites')
      break
    case 'admin':
      router.push('/admin')
      break
    case 'logout':
      authStore.logout()
      router.push('/')
      break
  }
}

const handleUploadSuccess = () => {
  showUploadDialog.value = false
  ElMessage.success('文件上传成功')
}

const fetchStatistics = async () => {
  loading.value = true
  try {
    const response = await usersApi.getUserStatistics()
    statistics.value = response.data
  } catch (error) {
    console.error('获取统计数据失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchStatistics()
})
</script>

<style scoped>
.dashboard-page {
  min-height: 100vh;
  background-color: var(--background-base);
}

.dashboard-header {
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 0;
}

.brand-link {
  text-decoration: none;
  color: inherit;
}

.brand h1 {
  margin: 0;
  font-size: 24px;
  color: var(--primary-color);
}

.header-actions {
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

.dashboard-content {
  padding: 32px 0;
}

.welcome-section {
  text-align: center;
  margin-bottom: 32px;
}

.welcome-section h2 {
  font-size: 32px;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.welcome-section p {
  color: var(--text-secondary);
  font-size: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 24px;
  margin-bottom: 48px;
}

.stats-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: var(--shadow-base);
  transition: transform 0.3s;
}

.stats-card:hover {
  transform: translateY(-2px);
}

.stats-icon {
  color: var(--primary-color);
}

.stats-number {
  font-size: 24px;
  font-weight: bold;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.stats-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.main-content {
  display: grid;
  gap: 32px;
}

.content-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: var(--shadow-base);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.section-header h3 {
  margin: 0;
  font-size: 20px;
  color: var(--text-primary);
}

.progress-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.progress-item {
  padding: 16px;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.progress-item:hover {
  border-color: var(--primary-color);
  box-shadow: var(--shadow-base);
}

.progress-info {
  margin-bottom: 12px;
}

.progress-info h4 {
  margin: 0 0 8px 0;
  color: var(--text-primary);
}

.progress-meta {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: var(--text-secondary);
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.action-card {
  text-align: center;
  padding: 24px;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.action-card:hover {
  border-color: var(--primary-color);
  transform: translateY(-2px);
  box-shadow: var(--shadow-base);
}

.action-icon {
  color: var(--primary-color);
  margin-bottom: 12px;
}

.action-card h4 {
  margin: 0 0 8px 0;
  color: var(--text-primary);
}

.action-card p {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-secondary);
}

.empty-state .el-icon {
  color: var(--text-placeholder);
  margin-bottom: 16px;
}

.empty-state p {
  margin-bottom: 16px;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .quick-actions {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .progress-meta {
    flex-direction: column;
    gap: 4px;
  }
}

@media (max-width: 480px) {
  .stats-grid,
  .quick-actions {
    grid-template-columns: 1fr;
  }
  
  .header-content {
    flex-direction: column;
    gap: 16px;
  }
}
</style>
