<template>
  <div class="question-detail-page">
    <div class="page-container">
      <div class="container">
        <!-- 导航栏 -->
        <div class="question-nav">
          <el-button @click="$router.back()" :icon="ArrowLeft">
            返回
          </el-button>
          <div class="nav-info" v-if="question">
            <span class="bank-name">{{ bankName }}</span>
            <el-divider direction="vertical" />
            <span class="question-index">第 {{ questionIndex }} 题</span>
          </div>
          <div class="nav-actions" v-if="authStore.isAuthenticated && question">
            <el-button 
              :type="question.is_favorited ? 'danger' : 'primary'"
              :icon="question.is_favorited ? StarFilled : Star"
              @click="toggleFavorite"
            >
              {{ question.is_favorited ? '取消收藏' : '收藏' }}
            </el-button>
          </div>
        </div>

        <!-- 题目内容 -->
        <div class="question-content" v-if="question">
          <div class="question-header">
            <div class="question-meta">
              <el-tag :type="getTypeTagType(question.type)">
                {{ getTypeText(question.type) }}
              </el-tag>
              <el-tag :type="getDifficultyType(question.difficulty)">
                {{ getDifficultyText(question.difficulty) }}
              </el-tag>
              <span class="points">{{ question.points }} 分</span>
            </div>
            
            <div class="question-tags" v-if="question.tags?.length">
              <el-tag 
                v-for="tag in question.tags" 
                :key="tag"
                size="small"
                effect="plain"
              >
                {{ tag }}
              </el-tag>
            </div>
          </div>
          
          <h1 class="question-title">{{ question.title }}</h1>
          
          <!-- 答题区域 -->
          <div class="answer-section">
            <!-- 选择题 -->
            <div v-if="question.type === 'choice'" class="choice-question">
              <div class="options">
                <div 
                  v-for="option in question.content.options" 
                  :key="option.key"
                  class="option-item"
                  :class="{ 
                    'selected': userAnswer === option.key,
                    'correct': showResult && option.key === question.answer?.correct_option,
                    'incorrect': showResult && userAnswer === option.key && option.key !== question.answer?.correct_option
                  }"
                  @click="!showResult && selectOption(option.key)"
                >
                  <span class="option-key">{{ option.key }}</span>
                  <span class="option-text">{{ option.text }}</span>
                  <el-icon v-if="showResult && option.key === question.answer?.correct_option" class="correct-icon">
                    <Check />
                  </el-icon>
                  <el-icon v-if="showResult && userAnswer === option.key && option.key !== question.answer?.correct_option" class="incorrect-icon">
                    <Close />
                  </el-icon>
                </div>
              </div>
            </div>
            
            <!-- 判断题 -->
            <div v-if="question.type === 'true_false'" class="true-false-question">
              <div class="tf-options">
                <div 
                  class="tf-option"
                  :class="{ 
                    'selected': userAnswer === true,
                    'correct': showResult && question.answer?.is_true === true,
                    'incorrect': showResult && userAnswer === true && question.answer?.is_true !== true
                  }"
                  @click="!showResult && selectTrueFalse(true)"
                >
                  <el-icon><Check /></el-icon>
                  <span>正确</span>
                </div>
                <div 
                  class="tf-option"
                  :class="{ 
                    'selected': userAnswer === false,
                    'correct': showResult && question.answer?.is_true === false,
                    'incorrect': showResult && userAnswer === false && question.answer?.is_true !== false
                  }"
                  @click="!showResult && selectTrueFalse(false)"
                >
                  <el-icon><Close /></el-icon>
                  <span>错误</span>
                </div>
              </div>
            </div>
            
            <!-- 问答题 -->
            <div v-if="question.type === 'qa'" class="qa-question">
              <el-input
                v-model="textAnswer"
                type="textarea"
                :rows="6"
                placeholder="请输入你的答案..."
                :disabled="showResult"
              />
            </div>
            
            <!-- 数学题 -->
            <div v-if="question.type === 'math'" class="math-question">
              <el-input-number
                v-model="numberAnswer"
                :precision="2"
                placeholder="请输入数值答案"
                :disabled="showResult"
                style="width: 200px;"
              />
            </div>
            
            <!-- 编程题 -->
            <div v-if="question.type === 'programming'" class="programming-question">
              <el-input
                v-model="textAnswer"
                type="textarea"
                :rows="10"
                placeholder="请输入你的代码..."
                :disabled="showResult"
              />
            </div>
          </div>
          
          <!-- 答题按钮 -->
          <div class="submit-section" v-if="!showResult">
            <el-button 
              type="primary" 
              size="large"
              :loading="submitting"
              :disabled="!hasAnswer"
              @click="submitAnswer"
            >
              提交答案
            </el-button>
            <div class="timer" v-if="startTime">
              <el-icon><Timer /></el-icon>
              <span>{{ formatTime(elapsedTime) }}</span>
            </div>
          </div>
          
          <!-- 答题结果 -->
          <div class="result-section" v-if="showResult && answerResult">
            <div class="result-card" :class="{ 'correct': answerResult.is_correct, 'incorrect': !answerResult.is_correct }">
              <div class="result-header">
                <el-icon size="32">
                  <Check v-if="answerResult.is_correct" />
                  <Close v-else />
                </el-icon>
                <div class="result-info">
                  <h3>{{ answerResult.is_correct ? '回答正确！' : '回答错误' }}</h3>
                  <p>得分：{{ answerResult.score }}/{{ question.points }} 分</p>
                </div>
              </div>
              
              <div class="result-details">
                <div class="answer-comparison">
                  <div class="user-answer">
                    <h4>你的答案：</h4>
                    <p>{{ formatUserAnswer(answerResult.user_answer) }}</p>
                  </div>
                  <div class="correct-answer">
                    <h4>正确答案：</h4>
                    <p>{{ formatCorrectAnswer(answerResult.correct_answer) }}</p>
                  </div>
                </div>
                
                <div class="explanation" v-if="answerResult.explanation">
                  <h4>题目解析：</h4>
                  <p>{{ answerResult.explanation }}</p>
                </div>
              </div>
            </div>
            
            <div class="result-actions">
              <el-button @click="resetAnswer">重新答题</el-button>
              <el-button type="primary" @click="nextQuestion">下一题</el-button>
              <el-button @click="$router.push(`/practice/${question.bank_id}`)">
                继续练习
              </el-button>
            </div>
          </div>
        </div>
        
        <!-- 加载状态 -->
        <div v-else class="loading-state">
          <el-skeleton :rows="8" animated />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  ArrowLeft, Star, StarFilled, Check, Close, Timer 
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { questionsApi } from '@/api/questions'
import type { Question, AnswerResult } from '@/types/questions'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const question = ref<Question | null>(null)
const answerResult = ref<AnswerResult | null>(null)
const showResult = ref(false)
const submitting = ref(false)

// 答案相关
const userAnswer = ref<any>(null)
const textAnswer = ref('')
const numberAnswer = ref(0)

// 计时相关
const startTime = ref<Date | null>(null)
const elapsedTime = ref(0)
const timer = ref<NodeJS.Timeout | null>(null)

// 题库信息
const bankName = ref('')
const questionIndex = ref(1)

const bankId = computed(() => Number(route.params.bankId))
const questionId = computed(() => Number(route.params.questionId))

const hasAnswer = computed(() => {
  if (!question.value) return false
  
  switch (question.value.type) {
    case 'choice':
      return userAnswer.value !== null
    case 'true_false':
      return userAnswer.value !== null
    case 'qa':
    case 'programming':
      return textAnswer.value.trim() !== ''
    case 'math':
      return numberAnswer.value !== null && numberAnswer.value !== 0
    default:
      return false
  }
})

const getTypeText = (type: string) => {
  const typeMap = {
    choice: '选择题', true_false: '判断题', qa: '问答题',
    math: '数学题', programming: '编程题'
  }
  return typeMap[type as keyof typeof typeMap] || type
}

const getTypeTagType = (type: string) => {
  const typeMap = {
    choice: 'success', true_false: 'warning', qa: 'info',
    math: 'danger', programming: ''
  }
  return typeMap[type as keyof typeof typeMap] || ''
}

const getDifficultyType = (difficulty: string) => {
  const types = { easy: 'success', medium: 'warning', hard: 'danger' }
  return types[difficulty as keyof typeof types] || 'info'
}

const getDifficultyText = (difficulty: string) => {
  const texts = { easy: '简单', medium: '中等', hard: '困难' }
  return texts[difficulty as keyof typeof texts] || difficulty
}

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

const formatUserAnswer = (answer: any) => {
  if (!question.value) return ''
  
  switch (question.value.type) {
    case 'choice':
      return answer.selected_option || answer
    case 'true_false':
      return answer.answer ? '正确' : '错误'
    case 'qa':
    case 'programming':
      return answer.answer || answer
    case 'math':
      return answer.result || answer
    default:
      return String(answer)
  }
}

const formatCorrectAnswer = (answer: any) => {
  if (!question.value) return ''
  
  switch (question.value.type) {
    case 'choice':
      return answer.correct_option
    case 'true_false':
      return answer.is_true ? '正确' : '错误'
    case 'qa':
      return answer.keywords?.join(', ') || ''
    case 'math':
      return String(answer.result)
    case 'programming':
      return answer.test_cases || ''
    default:
      return String(answer)
  }
}

const startTimer = () => {
  startTime.value = new Date()
  timer.value = setInterval(() => {
    if (startTime.value) {
      elapsedTime.value = Math.floor((Date.now() - startTime.value.getTime()) / 1000)
    }
  }, 1000)
}

const stopTimer = () => {
  if (timer.value) {
    clearInterval(timer.value)
    timer.value = null
  }
}

const selectOption = (key: string) => {
  userAnswer.value = key
}

const selectTrueFalse = (value: boolean) => {
  userAnswer.value = value
}

const submitAnswer = async () => {
  if (!question.value || !hasAnswer.value) return
  
  submitting.value = true
  
  try {
    let answerData: any
    
    switch (question.value.type) {
      case 'choice':
        answerData = { selected_option: userAnswer.value }
        break
      case 'true_false':
        answerData = { answer: userAnswer.value }
        break
      case 'qa':
      case 'programming':
        answerData = { answer: textAnswer.value }
        break
      case 'math':
        answerData = { result: numberAnswer.value }
        break
    }
    
    const response = await questionsApi.submitAnswer(question.value.id, {
      user_answer: answerData,
      time_spent: elapsedTime.value
    })
    
    answerResult.value = response.data
    showResult.value = true
    stopTimer()
    
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '提交失败')
  } finally {
    submitting.value = false
  }
}

const toggleFavorite = async () => {
  if (!question.value) return
  
  try {
    if (question.value.is_favorited) {
      await questionsApi.unfavoriteQuestion(question.value.id)
      question.value.is_favorited = false
      ElMessage.success('已取消收藏')
    } else {
      await questionsApi.favoriteQuestion(question.value.id)
      question.value.is_favorited = true
      ElMessage.success('已收藏')
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '操作失败')
  }
}

const resetAnswer = () => {
  userAnswer.value = null
  textAnswer.value = ''
  numberAnswer.value = 0
  showResult.value = false
  answerResult.value = null
  startTimer()
}

const nextQuestion = () => {
  // TODO: 实现下一题逻辑
  ElMessage.info('下一题功能开发中...')
}

const fetchQuestion = async () => {
  try {
    const response = await questionsApi.getQuestionDetail(questionId.value)
    question.value = response.data
    
    // 如果用户已经答过题，显示结果
    if (question.value.user_answer) {
      showResult.value = true
      answerResult.value = {
        is_correct: question.value.user_answer.is_correct,
        score: question.value.user_answer.score,
        correct_answer: question.value.answer || {},
        explanation: question.value.explanation,
        user_answer: question.value.user_answer.user_answer
      }
    } else {
      startTimer()
    }
  } catch (error) {
    console.error('获取题目详情失败:', error)
    ElMessage.error('题目不存在或无权访问')
    router.back()
  }
}

onMounted(() => {
  fetchQuestion()
})

onUnmounted(() => {
  stopTimer()
})
</script>

<style scoped>
.question-detail-page {
  min-height: 100vh;
  background-color: var(--background-base);
}

.question-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 0;
  margin-bottom: 24px;
}

.nav-info {
  display: flex;
  align-items: center;
  color: var(--text-secondary);
}

.bank-name {
  font-weight: 500;
}

.question-content {
  background: white;
  border-radius: 12px;
  padding: 32px;
  box-shadow: var(--shadow-base);
  max-width: 800px;
  margin: 0 auto;
}

.question-header {
  margin-bottom: 24px;
}

.question-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.points {
  font-size: 14px;
  color: var(--text-secondary);
}

.question-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.question-title {
  font-size: 24px;
  color: var(--text-primary);
  line-height: 1.5;
  margin-bottom: 32px;
}

.answer-section {
  margin-bottom: 32px;
}

/* 选择题样式 */
.options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.option-item {
  display: flex;
  align-items: center;
  padding: 16px;
  border: 2px solid var(--border-light);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
}

.option-item:hover {
  border-color: var(--primary-color);
}

.option-item.selected {
  border-color: var(--primary-color);
  background-color: #f0f9ff;
}

.option-item.correct {
  border-color: var(--success-color);
  background-color: #f6ffed;
}

.option-item.incorrect {
  border-color: var(--danger-color);
  background-color: #fff2f0;
}

.option-key {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: var(--background-base);
  border-radius: 50%;
  font-weight: bold;
  margin-right: 16px;
  flex-shrink: 0;
}

.option-text {
  flex: 1;
  line-height: 1.5;
}

.correct-icon,
.incorrect-icon {
  position: absolute;
  right: 16px;
  font-size: 20px;
}

.correct-icon {
  color: var(--success-color);
}

.incorrect-icon {
  color: var(--danger-color);
}

/* 判断题样式 */
.tf-options {
  display: flex;
  gap: 24px;
  justify-content: center;
}

.tf-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px;
  border: 2px solid var(--border-light);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
  min-width: 120px;
}

.tf-option:hover {
  border-color: var(--primary-color);
}

.tf-option.selected {
  border-color: var(--primary-color);
  background-color: #f0f9ff;
}

.tf-option.correct {
  border-color: var(--success-color);
  background-color: #f6ffed;
}

.tf-option.incorrect {
  border-color: var(--danger-color);
  background-color: #fff2f0;
}

.tf-option .el-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.submit-section {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 24px 0;
  border-top: 1px solid var(--border-lighter);
}

.timer {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-secondary);
  font-size: 16px;
}

.result-section {
  border-top: 1px solid var(--border-lighter);
  padding-top: 24px;
}

.result-card {
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
}

.result-card.correct {
  background: #f6ffed;
  border: 1px solid var(--success-color);
}

.result-card.incorrect {
  background: #fff2f0;
  border: 1px solid var(--danger-color);
}

.result-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.result-header .el-icon {
  color: inherit;
}

.result-card.correct .el-icon {
  color: var(--success-color);
}

.result-card.incorrect .el-icon {
  color: var(--danger-color);
}

.result-info h3 {
  margin: 0 0 4px 0;
  font-size: 20px;
}

.result-info p {
  margin: 0;
  color: var(--text-secondary);
}

.answer-comparison {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 20px;
}

.user-answer,
.correct-answer {
  padding: 16px;
  background: white;
  border-radius: 8px;
}

.user-answer h4,
.correct-answer h4,
.explanation h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: var(--text-secondary);
}

.user-answer p,
.correct-answer p,
.explanation p {
  margin: 0;
  color: var(--text-primary);
  line-height: 1.5;
}

.explanation {
  padding: 16px;
  background: white;
  border-radius: 8px;
}

.result-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.loading-state {
  background: white;
  border-radius: 12px;
  padding: 32px;
  box-shadow: var(--shadow-base);
  max-width: 800px;
  margin: 0 auto;
}

@media (max-width: 768px) {
  .question-nav {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .question-content {
    padding: 20px;
  }
  
  .question-title {
    font-size: 20px;
  }
  
  .tf-options {
    flex-direction: column;
    align-items: center;
  }
  
  .answer-comparison {
    grid-template-columns: 1fr;
  }
  
  .result-actions {
    flex-direction: column;
  }
  
  .submit-section {
    flex-direction: column;
  }
}
</style>
