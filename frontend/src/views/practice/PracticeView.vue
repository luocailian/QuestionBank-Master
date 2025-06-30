<template>
  <div class="practice-page">
    <div class="page-container">
      <div class="container">
        <!-- 练习头部 -->
        <div class="practice-header" v-if="bank">
          <div class="header-info">
            <h1>{{ bank.name }} - 练习模式</h1>
            <div class="practice-meta">
              <span>共 {{ bank.question_count }} 题</span>
              <span v-if="progress">
                已完成 {{ progress.answered_questions }} 题
              </span>
              <span v-if="progress">
                正确率 {{ progress.accuracy_rate }}%
              </span>
            </div>
          </div>
          
          <div class="header-actions">
            <el-button @click="$router.push('/dashboard')">
              <el-icon><House /></el-icon>
              仪表盘
            </el-button>
            <el-button @click="$router.push(`/banks/${bankId}`)">
              <el-icon><ArrowLeft /></el-icon>
              返回题库
            </el-button>
            <el-button type="primary" @click="showModeDialog = true">
              <el-icon><Setting /></el-icon>
              练习设置
            </el-button>
          </div>
        </div>

        <!-- 练习进度 -->
        <div class="progress-section" v-if="progress">
          <div class="progress-card">
            <div class="progress-info">
              <h3>学习进度</h3>
              <div class="progress-stats">
                <div class="stat-item">
                  <span class="stat-value">{{ progress.answered_questions }}</span>
                  <span class="stat-label">已答题</span>
                </div>
                <div class="stat-item">
                  <span class="stat-value">{{ progress.correct_answers }}</span>
                  <span class="stat-label">答对题</span>
                </div>
                <div class="stat-item">
                  <span class="stat-value">{{ progress.accuracy_rate }}%</span>
                  <span class="stat-label">正确率</span>
                </div>
                <div class="stat-item">
                  <span class="stat-value">{{ progress.total_score }}</span>
                  <span class="stat-label">总分</span>
                </div>
              </div>
            </div>
            <el-progress 
              :percentage="progress.progress_rate" 
              :stroke-width="12"
              class="progress-bar"
            />
          </div>
        </div>

        <!-- 练习模式选择 -->
        <div class="practice-modes">
          <div class="mode-grid">
            <div 
              class="mode-card"
              @click="startPractice('sequential')"
            >
              <div class="mode-icon">
                <el-icon size="32"><List /></el-icon>
              </div>
              <h3>顺序练习</h3>
              <p>按题目顺序依次练习</p>
              <div class="mode-stats">
                <span>{{ bank?.question_count || 0 }} 题</span>
              </div>
            </div>
            
            <div 
              class="mode-card"
              @click="startPractice('random')"
            >
              <div class="mode-icon">
                <el-icon size="32"><Refresh /></el-icon>
              </div>
              <h3>随机练习</h3>
              <p>随机选择题目练习</p>
              <div class="mode-stats">
                <span>{{ bank?.question_count || 0 }} 题</span>
              </div>
            </div>
            
            <div 
              class="mode-card"
              @click="startPractice('wrong')"
              v-if="hasWrongQuestions"
            >
              <div class="mode-icon">
                <el-icon size="32"><Warning /></el-icon>
              </div>
              <h3>错题练习</h3>
              <p>重新练习答错的题目</p>
              <div class="mode-stats">
                <span>{{ wrongQuestionsCount }} 题</span>
              </div>
            </div>
            
            <div 
              class="mode-card"
              @click="startPractice('unanswered')"
              v-if="hasUnansweredQuestions"
            >
              <div class="mode-icon">
                <el-icon size="32"><Document /></el-icon>
              </div>
              <h3>未答题目</h3>
              <p>练习还未回答的题目</p>
              <div class="mode-stats">
                <span>{{ unansweredQuestionsCount }} 题</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 题目类型筛选 -->
        <div class="type-filter" v-if="questionTypes.length > 1">
          <h3>按题型练习</h3>
          <div class="type-grid">
            <div 
              v-for="type in questionTypes" 
              :key="type.type"
              class="type-card"
              @click="startPractice('type', type.type)"
            >
              <div class="type-info">
                <el-tag :type="getTypeTagType(type.type)">
                  {{ type.type_name || getTypeText(type.type) }}
                </el-tag>
                <span class="type-count">{{ type.count }} 题</span>
              </div>
              <el-button size="small">开始练习</el-button>
            </div>
          </div>
        </div>

        <!-- 最近练习记录 -->
        <div class="recent-practice" v-if="recentAnswers.length > 0">
          <h3>最近练习</h3>
          <div class="recent-list">
            <div 
              v-for="answer in recentAnswers" 
              :key="answer.id"
              class="recent-item"
              @click="$router.push(`/banks/${bankId}/questions/${answer.question_id}`)"
            >
              <div class="recent-info">
                <h4>{{ answer.question?.title || '题目' }}</h4>
                <div class="recent-meta">
                  <el-tag 
                    :type="getTypeTagType(answer.question?.type || '')"
                    size="small"
                  >
                    {{ getTypeText(answer.question?.type || '') }}
                  </el-tag>
                  <span class="answer-result" :class="{ correct: answer.is_correct }">
                    {{ answer.is_correct ? '答对' : '答错' }}
                  </span>
                  <span class="answer-time">
                    {{ formatDate(answer.answered_at) }}
                  </span>
                </div>
              </div>
              <div class="recent-score">
                {{ answer.score }}/{{ answer.question?.points || 1 }} 分
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 练习设置对话框 -->
    <el-dialog
      v-model="showModeDialog"
      title="练习设置"
      width="500px"
    >
      <el-form label-width="100px">
        <el-form-item label="题目数量">
          <el-input-number 
            v-model="practiceSettings.questionCount" 
            :min="1" 
            :max="bank?.question_count || 100"
          />
        </el-form-item>
        
        <el-form-item label="题目类型">
          <el-select 
            v-model="practiceSettings.questionType" 
            placeholder="全部类型"
            clearable
          >
            <el-option label="全部类型" value="" />
            <el-option label="选择题" value="choice" />
            <el-option label="判断题" value="true_false" />
            <el-option label="问答题" value="qa" />
            <el-option label="数学题" value="math" />
            <el-option label="编程题" value="programming" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="难度">
          <el-select 
            v-model="practiceSettings.difficulty" 
            placeholder="全部难度"
            clearable
          >
            <el-option label="全部难度" value="" />
            <el-option label="简单" value="easy" />
            <el-option label="中等" value="medium" />
            <el-option label="困难" value="hard" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="练习模式">
          <el-radio-group v-model="practiceSettings.mode">
            <el-radio label="sequential">顺序练习</el-radio>
            <el-radio label="random">随机练习</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showModeDialog = false">取消</el-button>
          <el-button type="primary" @click="startCustomPractice">
            开始练习
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { List, Refresh, Warning, Document, House, ArrowLeft, Setting } from '@element-plus/icons-vue'
import { useBanksStore } from '@/stores/banks'
import { questionsApi } from '@/api/questions'
import type { QuestionBank, UserProgress } from '@/types/banks'
import type { UserAnswer } from '@/types/questions'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const banksStore = useBanksStore()

const bankId = computed(() => Number(route.params.bankId))
const bank = ref<QuestionBank | null>(null)
const progress = ref<UserProgress | null>(null)
const questionTypes = ref<Array<{ type: string; count: number }>>([])
const recentAnswers = ref<UserAnswer[]>([])
const showModeDialog = ref(false)

const practiceSettings = ref({
  questionCount: 10,
  questionType: '',
  difficulty: '',
  mode: 'sequential'
})

const hasWrongQuestions = computed(() => {
  return progress.value && (progress.value.answered_questions - progress.value.correct_answers) > 0
})

const wrongQuestionsCount = computed(() => {
  return progress.value ? progress.value.answered_questions - progress.value.correct_answers : 0
})

const hasUnansweredQuestions = computed(() => {
  return progress.value && progress.value.answered_questions < progress.value.total_questions
})

const unansweredQuestionsCount = computed(() => {
  return progress.value ? progress.value.total_questions - progress.value.answered_questions : 0
})

const getTypeText = (type: string) => {
  const typeMap = {
    single_choice: '单选题',
    multiple_choice: '多选题',
    choice: '选择题',
    true_false: '判断题',
    qa: '问答题',
    math: '数学题',
    programming: '编程题',
    fill_blank: '填空题'
  }
  return typeMap[type as keyof typeof typeMap] || type
}

const getTypeTagType = (type: string) => {
  const typeMap = {
    single_choice: 'success',
    multiple_choice: 'primary',
    choice: 'success',
    true_false: 'warning',
    qa: 'info',
    math: 'danger',
    programming: '',
    fill_blank: 'info'
  }
  return typeMap[type as keyof typeof typeMap] || ''
}

const formatDate = (dateString: string) => {
  return dayjs(dateString).format('MM-DD HH:mm')
}

const startPractice = (mode: string, filter?: string) => {
  const query: any = { mode }

  if (filter) {
    if (mode === 'type') {
      query.type = filter
      query.typeName = getTypeText(filter)
    }
  }

  router.push({
    path: `/practice/${bankId.value}/session`,
    query
  })
}

const startCustomPractice = () => {
  const query: any = {
    mode: practiceSettings.value.mode,
    count: practiceSettings.value.questionCount
  }
  
  if (practiceSettings.value.questionType) {
    query.type = practiceSettings.value.questionType
  }
  
  if (practiceSettings.value.difficulty) {
    query.difficulty = practiceSettings.value.difficulty
  }
  
  showModeDialog.value = false
  router.push({
    path: `/practice/${bankId.value}/session`,
    query
  })
}

const fetchBankDetail = async () => {
  try {
    const response = await banksStore.fetchBankDetail(bankId.value)
    bank.value = response.data
    progress.value = response.data.user_progress || null
  } catch (error) {
    console.error('获取题库详情失败:', error)
    ElMessage.error('题库不存在或无权访问')
    router.push('/banks')
  }
}

const fetchQuestionTypes = async () => {
  try {
    const token = localStorage.getItem('token')
    const response = await fetch(`/api/v1/questions/types-stats?bank_id=${bankId.value}`, {
      headers: token ? {
        'Authorization': `Bearer ${token}`
      } : {}
    })

    if (response.ok) {
      const data = await response.json()
      if (data.type_stats) {
        questionTypes.value = data.type_stats.filter((stat: any) => stat.count > 0)
      }
    }
  } catch (error) {
    console.error('获取题目类型统计失败:', error)
  }
}

const fetchRecentAnswers = async () => {
  try {
    // 这里需要后端提供最近答题记录接口
    // 暂时模拟数据
    recentAnswers.value = []
  } catch (error) {
    console.error('获取最近练习记录失败:', error)
  }
}

onMounted(() => {
  fetchBankDetail()
  fetchQuestionTypes()
  fetchRecentAnswers()
})
</script>

<style scoped>
.practice-page {
  min-height: 100vh;
  background-color: var(--background-base);
}

.practice-header {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: var(--shadow-base);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.header-info h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: var(--text-primary);
}

.practice-meta {
  display: flex;
  gap: 16px;
  color: var(--text-secondary);
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.progress-section {
  margin-bottom: 32px;
}

.progress-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: var(--shadow-base);
}

.progress-info h3 {
  margin: 0 0 16px 0;
  color: var(--text-primary);
}

.progress-stats {
  display: flex;
  gap: 32px;
  margin-bottom: 16px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 20px;
  font-weight: bold;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
}

.practice-modes {
  margin-bottom: 32px;
}

.mode-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.mode-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: var(--shadow-base);
  cursor: pointer;
  transition: all 0.3s;
  text-align: center;
}

.mode-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-light);
}

.mode-icon {
  color: var(--primary-color);
  margin-bottom: 16px;
}

.mode-card h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: var(--text-primary);
}

.mode-card p {
  margin: 0 0 16px 0;
  color: var(--text-secondary);
  line-height: 1.5;
}

.mode-stats {
  font-size: 14px;
  color: var(--text-secondary);
}

.type-filter,
.recent-practice {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: var(--shadow-base);
}

.type-filter h3,
.recent-practice h3 {
  margin: 0 0 20px 0;
  color: var(--text-primary);
}

.type-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.type-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.type-card:hover {
  border-color: var(--primary-color);
  box-shadow: var(--shadow-base);
}

.type-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.type-count {
  font-size: 14px;
  color: var(--text-secondary);
}

.recent-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recent-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.recent-item:hover {
  border-color: var(--primary-color);
  box-shadow: var(--shadow-base);
}

.recent-info h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  color: var(--text-primary);
}

.recent-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.answer-result {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 4px;
  background: #fff2f0;
  color: #ff4d4f;
}

.answer-result.correct {
  background: #f6ffed;
  color: #52c41a;
}

.answer-time {
  font-size: 12px;
  color: var(--text-placeholder);
}

.recent-score {
  font-weight: bold;
  color: var(--text-primary);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 768px) {
  .practice-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .header-actions {
    align-self: stretch;
  }
  
  .progress-stats {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }
  
  .mode-grid {
    grid-template-columns: 1fr;
  }
  
  .practice-meta {
    flex-direction: column;
    gap: 8px;
  }
  
  .recent-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .recent-meta {
    flex-wrap: wrap;
  }
}
</style>
