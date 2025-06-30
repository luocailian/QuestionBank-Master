<template>
  <div class="home-page">
    <!-- 导航栏 -->
    <nav class="navbar">
      <div class="container">
        <div class="nav-content">
          <div class="nav-brand">
            <h1>QuestionBank Master</h1>
            <span class="tagline">智能题库系统</span>
          </div>
          
          <div class="nav-actions">
            <template v-if="!authStore.isAuthenticated">
              <el-button @click="$router.push('/login')">登录</el-button>
              <el-button type="primary" @click="$router.push('/register')">注册</el-button>
            </template>
            <template v-else>
              <el-button @click="$router.push('/dashboard')">控制台</el-button>
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
                    <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </template>
          </div>
        </div>
      </div>
    </nav>

    <!-- 英雄区域 -->
    <section class="hero-section">
      <div class="container">
        <div class="hero-content">
          <h2 class="hero-title">现代化的在线题库系统</h2>
          <p class="hero-description">
            支持多种题型、智能统计、文件导入，让学习更高效
          </p>
          <div class="hero-actions">
            <el-button 
              type="primary" 
              size="large" 
              @click="handleStartLearning"
            >
              开始学习
            </el-button>
            <el-button size="large" @click="$router.push('/banks')">
              浏览题库
            </el-button>
          </div>
        </div>
        
        <div class="hero-stats">
          <div class="stat-item">
            <div class="stat-number">{{ stats.totalBanks }}</div>
            <div class="stat-label">题库数量</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ stats.totalQuestions }}</div>
            <div class="stat-label">题目总数</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ stats.totalUsers }}</div>
            <div class="stat-label">用户数量</div>
          </div>
        </div>
      </div>
    </section>

    <!-- 特性介绍 -->
    <section class="features-section">
      <div class="container">
        <h3 class="section-title">核心特性</h3>
        <div class="features-grid">
          <div class="feature-card">
            <div class="feature-icon">
              <el-icon size="48"><Document /></el-icon>
            </div>
            <h4>多种题型</h4>
            <p>支持选择题、判断题、问答题、数学题、编程题等多种题型</p>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon">
              <el-icon size="48"><Upload /></el-icon>
            </div>
            <h4>文件导入</h4>
            <p>支持PDF、Word、Excel等格式文件一键导入，自动解析题目</p>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon">
              <el-icon size="48"><DataAnalysis /></el-icon>
            </div>
            <h4>智能统计</h4>
            <p>详细的答题统计、进度跟踪、错题分析，让学习更有针对性</p>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon">
              <el-icon size="48"><Star /></el-icon>
            </div>
            <h4>个性化学习</h4>
            <p>收藏功能、错题本、积分排行，打造个性化学习体验</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 热门题库 -->
    <section class="popular-banks-section" v-if="popularBanks.length > 0">
      <div class="container">
        <h3 class="section-title">热门题库</h3>
        <div class="banks-grid">
          <div 
            v-for="bank in popularBanks" 
            :key="bank.id"
            class="bank-card"
            @click="$router.push(`/banks/${bank.id}`)"
          >
            <div class="bank-header">
              <h4>{{ bank.name }}</h4>
              <el-tag :type="getDifficultyType(bank.difficulty)">
                {{ getDifficultyText(bank.difficulty) }}
              </el-tag>
            </div>
            <p class="bank-description">{{ bank.description }}</p>
            <div class="bank-meta">
              <span><el-icon><Document /></el-icon> {{ bank.question_count }} 题</span>
              <span><el-icon><User /></el-icon> {{ bank.creator_name }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 页脚 -->
    <footer class="footer">
      <div class="container">
        <div class="footer-content">
          <div class="footer-brand">
            <h4>QuestionBank Master</h4>
            <p>让学习更高效，让知识更有趣</p>
          </div>
          <div class="footer-links">
            <div class="link-group">
              <h5>产品</h5>
              <a href="/banks">题库浏览</a>
              <a href="/dashboard">用户中心</a>
            </div>
            <div class="link-group">
              <h5>支持</h5>
              <a href="#">使用帮助</a>
              <a href="#">联系我们</a>
            </div>
          </div>
        </div>
        <div class="footer-bottom">
          <p>&copy; 2024 QuestionBank Master. All rights reserved.</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ArrowDown, Document, Upload, DataAnalysis, Star, User } from '@element-plus/icons-vue'
import type { QuestionBank } from '@/types/banks'
import { getPublicStats, getPopularBanks } from '@/api/public'

const router = useRouter()
const authStore = useAuthStore()

const stats = ref({
  totalBanks: 0,
  totalQuestions: 0,
  totalUsers: 0
})

const popularBanks = ref<QuestionBank[]>([])
const refreshInterval = ref<number | null>(null)

const handleStartLearning = () => {
  if (authStore.isAuthenticated) {
    router.push('/dashboard')
  } else {
    router.push('/login')
  }
}

// 刷新统计数据
const refreshStats = async () => {
  try {
    const statsData = await getPublicStats()
    stats.value = {
      totalUsers: statsData.totalUsers,
      totalBanks: statsData.totalBanks,
      totalQuestions: statsData.totalQuestions
    }
  } catch (error) {
    console.error('刷新统计数据失败:', error)
  }
}

const handleUserAction = (command: string) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'favorites':
      router.push('/favorites')
      break
    case 'logout':
      authStore.logout()
      break
  }
}

const getDifficultyType = (difficulty: string): 'success' | 'warning' | 'danger' | 'info' => {
  const types: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
    easy: 'success',
    medium: 'warning',
    hard: 'danger'
  }
  return types[difficulty] || 'info'
}

const getDifficultyText = (difficulty: string) => {
  const texts = {
    easy: '简单',
    medium: '中等',
    hard: '困难'
  }
  return texts[difficulty as keyof typeof texts] || difficulty
}

onMounted(async () => {
  try {
    // 并行获取统计数据和热门题库
    const [statsData, banksData] = await Promise.all([
      getPublicStats(),
      getPopularBanks(6)
    ])

    // 设置统计数据
    stats.value = {
      totalUsers: statsData.totalUsers,
      totalBanks: statsData.totalBanks,
      totalQuestions: statsData.totalQuestions
    }

    // 设置热门题库
    popularBanks.value = Array.isArray(banksData) ? banksData.slice(0, 6) : []

    // 启动定时刷新统计数据（每60秒刷新一次）
    refreshInterval.value = setInterval(() => {
      refreshStats()
    }, 60000)

  } catch (error) {
    console.error('获取首页数据失败:', error)
    // 设置默认值
    popularBanks.value = []
    stats.value = {
      totalBanks: 0,
      totalQuestions: 0,
      totalUsers: 0
    }
  }
})

onUnmounted(() => {
  // 清理定时器
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
    refreshInterval.value = null
  }
})
</script>

<style scoped>
.home-page {
  min-height: 100vh;
}

.navbar {
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 0;
}

.nav-brand h1 {
  margin: 0;
  font-size: 24px;
  color: var(--primary-color);
}

.tagline {
  font-size: 12px;
  color: var(--text-secondary);
  margin-left: 8px;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 12px;
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

.hero-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 80px 0;
  text-align: center;
}

.hero-title {
  font-size: 48px;
  font-weight: bold;
  margin-bottom: 16px;
}

.hero-description {
  font-size: 20px;
  margin-bottom: 32px;
  opacity: 0.9;
}

.hero-actions {
  margin-bottom: 60px;
}

.hero-actions .el-button {
  margin: 0 8px;
}

.hero-stats {
  display: flex;
  justify-content: center;
  gap: 60px;
}

.stat-item {
  text-align: center;
}

.stat-number {
  font-size: 36px;
  font-weight: bold;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  opacity: 0.8;
}

.features-section,
.popular-banks-section {
  padding: 80px 0;
}

.section-title {
  text-align: center;
  font-size: 32px;
  margin-bottom: 48px;
  color: var(--text-primary);
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 32px;
}

.feature-card {
  text-align: center;
  padding: 32px 24px;
  border-radius: 12px;
  background: white;
  box-shadow: var(--shadow-base);
  transition: transform 0.3s, box-shadow 0.3s;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-light);
}

.feature-icon {
  color: var(--primary-color);
  margin-bottom: 16px;
}

.feature-card h4 {
  font-size: 20px;
  margin-bottom: 12px;
  color: var(--text-primary);
}

.feature-card p {
  color: var(--text-regular);
  line-height: 1.6;
}

.banks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
}

.bank-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: var(--shadow-base);
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s;
}

.bank-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-light);
}

.bank-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.bank-header h4 {
  margin: 0;
  color: var(--text-primary);
}

.bank-description {
  color: var(--text-regular);
  margin-bottom: 16px;
  line-height: 1.5;
}

.bank-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 14px;
  color: var(--text-secondary);
}

.bank-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.footer {
  background: #2c3e50;
  color: white;
  padding: 48px 0 24px;
}

.footer-content {
  display: flex;
  justify-content: space-between;
  margin-bottom: 32px;
}

.footer-brand h4 {
  margin-bottom: 12px;
  color: var(--primary-color);
}

.footer-brand p {
  color: #bdc3c7;
}

.footer-links {
  display: flex;
  gap: 48px;
}

.link-group h5 {
  margin-bottom: 16px;
  color: white;
}

.link-group a {
  display: block;
  color: #bdc3c7;
  text-decoration: none;
  margin-bottom: 8px;
  transition: color 0.3s;
}

.link-group a:hover {
  color: var(--primary-color);
}

.footer-bottom {
  text-align: center;
  padding-top: 24px;
  border-top: 1px solid #34495e;
  color: #95a5a6;
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 32px;
  }
  
  .hero-description {
    font-size: 16px;
  }
  
  .hero-stats {
    flex-direction: column;
    gap: 24px;
  }
  
  .features-grid,
  .banks-grid {
    grid-template-columns: 1fr;
  }
  
  .footer-content {
    flex-direction: column;
    gap: 32px;
  }
  
  .footer-links {
    gap: 24px;
  }
}
</style>
