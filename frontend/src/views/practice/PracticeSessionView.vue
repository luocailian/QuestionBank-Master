<template>
  <div class="practice-session">
    <div class="session-container">
      <!-- 练习头部 -->
      <div class="session-header">
        <div class="header-left">
          <el-button @click="exitPractice" size="small">
            <el-icon><ArrowLeft /></el-icon>
            退出练习
          </el-button>
          <div class="session-info">
            <span class="bank-name">{{ bank?.name }}</span>
            <span class="mode-text">{{ getModeText() }}</span>
          </div>
        </div>
        
        <div class="header-right">
          <div class="progress-info">
            <span>{{ currentIndex + 1 }} / {{ questions.length }}</span>
          </div>
          <div class="timer" v-if="showTimer">
            <el-icon><Timer /></el-icon>
            {{ formatTime(elapsedTime) }}
          </div>
        </div>
      </div>

      <!-- 进度条 -->
      <div class="progress-bar">
        <el-progress 
          :percentage="progressPercentage" 
          :stroke-width="6"
          :show-text="false"
        />
      </div>

      <!-- 题目内容 -->
      <div class="question-content" v-if="currentQuestion">
        <div class="question-card">
          <div class="question-header">
            <div class="question-meta">
              <el-tag :type="getTypeTagType(currentQuestion.type)" size="small">
                {{ getTypeText(currentQuestion.type) }}
              </el-tag>
              <el-tag v-if="currentQuestion.difficulty" size="small">
                {{ getDifficultyText(currentQuestion.difficulty) }}
              </el-tag>
              <span class="question-points">{{ currentQuestion.points || 1 }} 分</span>
            </div>
            <div class="question-actions">
              <el-button 
                @click="toggleFavorite" 
                :type="isFavorited ? 'primary' : 'default'"
                size="small"
                circle
              >
                <el-icon><Star /></el-icon>
              </el-button>
            </div>
          </div>
          
          <div class="question-title">
            <h2>{{ currentQuestion.title }}</h2>
          </div>
          
          <div class="question-body">
            <!-- 选择题 -->
            <div v-if="currentQuestion.type === 'choice'" class="choice-question">
              <div class="question-text" v-html="currentQuestion.content.question"></div>
              <div class="question-hint" v-if="isMultipleChoice">
                <el-tag type="info" size="small">多选题：可选择多个答案</el-tag>
              </div>
              <div class="choices">
                <div
                  v-for="(option, index) in currentQuestion.content.options"
                  :key="index"
                  class="choice-option"
                  :class="{ selected: isOptionSelected(option.key) }"
                  @click="selectChoice(option.key)"
                >
                  <div class="option-key">{{ option.key }}</div>
                  <div class="option-text">{{ option.text }}</div>
                  <div class="option-check" v-if="isMultipleChoice">
                    <el-icon v-if="isOptionSelected(option.key)"><Check /></el-icon>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 判断题 -->
            <div v-else-if="currentQuestion.type === 'true_false'" class="true-false-question">
              <div class="question-text" v-html="currentQuestion.content.question || currentQuestion.content"></div>
              <div class="true-false-options">
                <div
                  class="tf-option"
                  :class="{ selected: userAnswer === true }"
                  @click="userAnswer = true"
                >
                  <el-icon><Check /></el-icon>
                  <span>正确</span>
                </div>
                <div
                  class="tf-option"
                  :class="{ selected: userAnswer === false }"
                  @click="userAnswer = false"
                >
                  <el-icon><Close /></el-icon>
                  <span>错误</span>
                </div>
              </div>
            </div>
            
            <!-- 问答题 -->
            <div v-else-if="currentQuestion.type === 'qa'" class="qa-question">
              <div class="question-text" v-html="currentQuestion.content.question || currentQuestion.content"></div>
              <el-input
                v-model="userAnswer"
                type="textarea"
                :rows="6"
                placeholder="请输入您的答案..."
                class="answer-input"
              />
            </div>
            
            <!-- 数学题 -->
            <div v-else-if="currentQuestion.type === 'math'" class="math-question">
              <div class="question-text" v-html="currentQuestion.content.question || currentQuestion.content"></div>
              <el-input
                v-model="userAnswer"
                placeholder="请输入数值答案..."
                class="answer-input"
                type="number"
              />
            </div>
            
            <!-- 编程题 -->
            <div v-else-if="currentQuestion.type === 'programming'" class="programming-question">
              <div class="question-text" v-html="currentQuestion.content.question || currentQuestion.content"></div>
              <div class="code-editor">
                <el-input
                  v-model="userAnswer"
                  type="textarea"
                  :rows="12"
                  placeholder="请输入您的代码..."
                  class="code-input"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="session-actions">
        <el-button 
          @click="previousQuestion" 
          :disabled="currentIndex === 0"
        >
          上一题
        </el-button>
        
        <div class="center-actions">
          <el-button @click="skipQuestion" v-if="!isAnswered">
            跳过
          </el-button>
          <el-button
            type="primary"
            @click="submitAnswer"
            :disabled="!hasAnswer"
            :loading="submitting"
          >
            {{ isAnswered ? '查看解析' : '提交答案' }}
          </el-button>
          <el-button @click="showAnswerCard = true" type="info">
            答题卡
          </el-button>
        </div>
        
        <el-button 
          @click="nextQuestion" 
          :disabled="currentIndex === questions.length - 1"
        >
          下一题
        </el-button>
      </div>
    </div>

    <!-- 答题卡抽屉 -->
    <el-drawer
      v-model="showAnswerCard"
      title="答题卡"
      :size="400"
      direction="rtl"
    >
      <div class="answer-card">
        <!-- 答题统计 -->
        <div class="answer-stats">
          <div class="stat-item">
            <span class="stat-label">总题数：</span>
            <span class="stat-value">{{ questions.length }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">已答题：</span>
            <span class="stat-value answered">{{ answeredCount }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">未答题：</span>
            <span class="stat-value unanswered">{{ questions.length - answeredCount }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">正确题：</span>
            <span class="stat-value correct">{{ correctCount }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">错误题：</span>
            <span class="stat-value incorrect">{{ incorrectCount }}</span>
          </div>
          <div class="stat-item" v-if="answeredCount > 0">
            <span class="stat-label">正确率：</span>
            <span class="stat-value" :class="{ correct: accuracyRate >= 60, incorrect: accuracyRate < 60 }">
              {{ accuracyRate.toFixed(1) }}%
            </span>
          </div>
        </div>

        <!-- 题目网格 -->
        <div class="question-grid">
          <div
            v-for="(question, index) in questions"
            :key="question.id"
            class="question-item"
            :class="getQuestionItemClass(index)"
            @click="jumpToQuestion(index)"
          >
            {{ index + 1 }}
          </div>
        </div>

        <!-- 快捷操作 -->
        <div class="quick-actions">
          <el-button @click="jumpToFirstUnanswered" size="small" type="primary">
            跳转到第一个未答题
          </el-button>
          <el-button @click="jumpToFirstIncorrect" size="small" type="danger" v-if="incorrectCount > 0">
            跳转到第一个错题
          </el-button>
        </div>

        <!-- 图例 -->
        <div class="legend">
          <div class="legend-item">
            <div class="legend-color current"></div>
            <span>当前题目</span>
          </div>
          <div class="legend-item">
            <div class="legend-color correct"></div>
            <span>答对</span>
          </div>
          <div class="legend-item">
            <div class="legend-color incorrect"></div>
            <span>答错</span>
          </div>
          <div class="legend-item">
            <div class="legend-color answered"></div>
            <span>已答</span>
          </div>
          <div class="legend-item">
            <div class="legend-color unanswered"></div>
            <span>未答</span>
          </div>
        </div>

        <!-- 快捷键提示 -->
        <div class="shortcuts-hint">
          <div class="hint-title">快捷键：</div>
          <div class="hint-item">← → 切换题目</div>
          <div class="hint-item">Enter 提交答案</div>
          <div class="hint-item">Tab 打开/关闭答题卡</div>
          <div class="hint-item">Esc 关闭弹窗</div>
        </div>
      </div>
    </el-drawer>

    <!-- 答案结果对话框 -->
    <el-dialog
      v-model="showResultDialog"
      title="答题结果"
      width="500px"
      :close-on-click-modal="false"
    >
      <div class="result-content">
        <div class="result-header">
          <div class="result-icon" :class="{ correct: lastResult?.is_correct }">
            <el-icon v-if="lastResult?.is_correct"><Check /></el-icon>
            <el-icon v-else><Close /></el-icon>
          </div>
          <div class="result-text">
            <h3>{{ lastResult?.is_correct ? '回答正确！' : '回答错误' }}</h3>
            <p>得分：{{ lastResult?.score || 0 }} / {{ currentQuestion?.points || 1 }} 分</p>
          </div>
        </div>
        
        <div class="answer-comparison" v-if="lastResult">
          <div class="answer-item">
            <label>您的答案：</label>
            <div class="answer-value">{{ formatAnswer(lastResult.user_answer) }}</div>
          </div>
          <div class="answer-item">
            <label>正确答案：</label>
            <div class="answer-value correct">{{ formatAnswer(lastResult.correct_answer) }}</div>
          </div>
        </div>
        
        <div class="explanation" v-if="currentQuestion?.explanation">
          <label>题目解析：</label>
          <div class="explanation-content" v-html="currentQuestion.explanation"></div>
        </div>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showResultDialog = false">关闭</el-button>
          <el-button type="primary" @click="continueNext">
            {{ currentIndex === questions.length - 1 ? '完成练习' : '下一题' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  ArrowLeft, Timer, Star, Check, Close
} from '@element-plus/icons-vue'
import { useBanksStore } from '@/stores/banks'
import { questionsApi } from '@/api/questions'
import type { QuestionBank, Question } from '@/types/banks'

const route = useRoute()
const router = useRouter()
const banksStore = useBanksStore()

const bankId = computed(() => Number(route.params.bankId))
const mode = computed(() => route.query.mode as string || 'sequential')
const questionType = computed(() => route.query.type as string)
const practiceTypeName = computed(() => route.query.typeName as string || '')
const difficulty = computed(() => route.query.difficulty as string)
const questionCount = computed(() => Number(route.query.count) || 0)

const bank = ref<QuestionBank | null>(null)
const questions = ref<Question[]>([])
const currentIndex = ref(0)
const userAnswer = ref<any>(null)
const answers = ref<Map<number, any>>(new Map())
const answerResults = ref<Map<number, any>>(new Map()) // 存储答题结果
const submitting = ref(false)
const showResultDialog = ref(false)
const lastResult = ref<any>(null)
const isFavorited = ref(false)
const showAnswerCard = ref(false)

// 计时器
const startTime = ref<Date | null>(null)
const elapsedTime = ref(0)
const timer = ref<NodeJS.Timeout | null>(null)
const showTimer = ref(true)

const currentQuestion = computed(() => questions.value[currentIndex.value])
const progressPercentage = computed(() =>
  questions.value.length > 0 ? ((currentIndex.value + 1) / questions.value.length) * 100 : 0
)
const isAnswered = computed(() => answers.value.has(currentQuestion.value?.id || 0))

// 判断是否为多选题（根据选项数量判断，超过4个选项通常是多选）
const isMultipleChoice = computed(() => {
  if (!currentQuestion.value || currentQuestion.value.type !== 'choice') return false
  // 如果选项超过4个，很可能是多选题
  const optionCount = currentQuestion.value.content.options?.length || 0
  return optionCount > 4
})

const hasAnswer = computed(() => {
  if (!currentQuestion.value) return false

  if (currentQuestion.value.type === 'true_false') {
    return userAnswer.value !== null && userAnswer.value !== undefined
  }

  if (currentQuestion.value.type === 'choice' && isMultipleChoice.value) {
    return Array.isArray(userAnswer.value) && userAnswer.value.length > 0
  }

  return userAnswer.value !== null && userAnswer.value !== undefined && userAnswer.value !== ''
})

// 答题卡统计
const answeredCount = computed(() => answers.value.size)
const correctCount = computed(() => {
  let count = 0
  for (const [questionId, result] of answerResults.value) {
    if (result && result.is_correct) {
      count++
    }
  }
  return count
})
const incorrectCount = computed(() => {
  let count = 0
  for (const [questionId, result] of answerResults.value) {
    if (result && !result.is_correct) {
      count++
    }
  }
  return count
})
const accuracyRate = computed(() => {
  const total = correctCount.value + incorrectCount.value
  return total > 0 ? (correctCount.value / total) * 100 : 0
})

// 题型映射
const getQuestionTypeLabel = (type: string) => {
  const typeMap: Record<string, string> = {
    'choice': '选择题',
    'true_false': '判断题',
    'qa': '问答题',
    'math': '数学题',
    'programming': '编程题',
    'fill_blank': '填空题'
  }
  return typeMap[type] || '未知题型'
}

// 判断是否为多选题的标签
const getChoiceTypeLabel = (question: any) => {
  if (question.type !== 'choice') return ''

  // 如果选项超过4个，很可能是多选题
  const optionCount = question.content.options?.length || 0
  if (optionCount > 4) {
    return '多选题'
  }
  return '单选题'
}

const getModeText = () => {
  if (mode.value === 'type' && practiceTypeName.value) {
    return `${practiceTypeName.value}练习`
  }

  const modeMap = {
    sequential: '顺序练习',
    random: '随机练习',
    wrong: '错题练习',
    unanswered: '未答题目',
    type: '分类练习'
  }
  return modeMap[mode.value as keyof typeof modeMap] || '练习模式'
}

const getTypeText = (type: string) => {
  if (type === 'choice' && currentQuestion.value) {
    // 判断是单选还是多选
    const optionCount = currentQuestion.value.content.options?.length || 0
    return optionCount > 4 ? '多选题' : '单选题'
  }

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

const getDifficultyText = (difficulty: string) => {
  const difficultyMap = {
    easy: '简单', medium: '中等', hard: '困难'
  }
  return difficultyMap[difficulty as keyof typeof difficultyMap] || difficulty
}

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

const formatAnswer = (answer: any) => {
  if (answer === null || answer === undefined) {
    return '无答案'
  }

  if (typeof answer === 'boolean') {
    return answer ? '正确' : '错误'
  }

  if (Array.isArray(answer)) {
    return answer.join(', ')
  }

  if (typeof answer === 'object') {
    // 处理对象类型的答案
    if (answer.correct_option) {
      return answer.correct_option
    }
    if (answer.correct_answer !== undefined) {
      return typeof answer.correct_answer === 'boolean'
        ? (answer.correct_answer ? '正确' : '错误')
        : String(answer.correct_answer)
    }
    if (answer.sample_answer !== undefined) {
      return String(answer.sample_answer)
    }
    if (answer.is_true !== undefined) {
      return answer.is_true ? '正确' : '错误'
    }
    if (answer.keywords && Array.isArray(answer.keywords)) {
      return answer.keywords.join(', ')
    }
    if (answer.result !== undefined) {
      return String(answer.result)
    }
    // 如果是其他对象，尝试转换为JSON字符串
    try {
      return JSON.stringify(answer)
    } catch {
      return String(answer)
    }
  }

  return String(answer)
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

const selectChoice = (key: string) => {
  if (isMultipleChoice.value) {
    // 多选题逻辑
    if (!Array.isArray(userAnswer.value)) {
      userAnswer.value = []
    }
    const index = userAnswer.value.indexOf(key)
    if (index > -1) {
      // 已选中，取消选择
      userAnswer.value.splice(index, 1)
    } else {
      // 未选中，添加选择
      userAnswer.value.push(key)
    }
  } else {
    // 单选题逻辑
    userAnswer.value = key
  }
}

const isOptionSelected = (key: string) => {
  if (isMultipleChoice.value) {
    return Array.isArray(userAnswer.value) && userAnswer.value.includes(key)
  } else {
    return userAnswer.value === key
  }
}

const loadCurrentAnswer = () => {
  if (currentQuestion.value) {
    const savedAnswer = answers.value.get(currentQuestion.value.id)
    if (savedAnswer !== undefined) {
      userAnswer.value = savedAnswer
    } else {
      // 根据题目类型初始化答案
      if (currentQuestion.value.type === 'choice' && isMultipleChoice.value) {
        userAnswer.value = []
      } else {
        userAnswer.value = null
      }
    }
  }
}

const saveCurrentAnswer = () => {
  if (currentQuestion.value && hasAnswer.value) {
    answers.value.set(currentQuestion.value.id, userAnswer.value)
  }
}

const previousQuestion = () => {
  if (currentIndex.value > 0) {
    saveCurrentAnswer()
    currentIndex.value--
    loadCurrentAnswer()
    checkFavoriteStatus()
  }
}

const nextQuestion = () => {
  if (currentIndex.value < questions.value.length - 1) {
    saveCurrentAnswer()
    currentIndex.value++
    loadCurrentAnswer()
    checkFavoriteStatus()
  }
}

const skipQuestion = () => {
  nextQuestion()
}

const submitAnswer = async () => {
  if (!currentQuestion.value) return

  if (isAnswered.value) {
    // 已答过，显示解析
    showResultDialog.value = true
    return
  }

  if (!hasAnswer.value) {
    ElMessage.warning('请先选择或输入答案')
    return
  }

  submitting.value = true

  try {
    const timeSpent = startTime.value ?
      Math.floor((Date.now() - startTime.value.getTime()) / 1000) : 0

    // 处理多选题答案格式
    let submitAnswer = userAnswer.value
    if (currentQuestion.value.type === 'choice' && isMultipleChoice.value && Array.isArray(userAnswer.value)) {
      submitAnswer = userAnswer.value.join('')
    }

    const response = await questionsApi.submitAnswer(currentQuestion.value.id, {
      user_answer: submitAnswer,
      time_spent: timeSpent
    })

    lastResult.value = response.data
    answers.value.set(currentQuestion.value.id, userAnswer.value)
    answerResults.value.set(currentQuestion.value.id, response.data)

    // 如果答对了，自动跳转下一题
    if (response.data.is_correct) {
      ElMessage.success('回答正确！')
      setTimeout(() => {
        if (currentIndex.value < questions.value.length - 1) {
          nextQuestion()
        } else {
          finishPractice()
        }
      }, 1000)
    } else {
      // 答错了，显示解析
      showResultDialog.value = true
    }

  } catch (error) {
    console.error('提交答案失败:', error)
    ElMessage.error('提交失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

const continueNext = () => {
  showResultDialog.value = false
  
  if (currentIndex.value === questions.value.length - 1) {
    // 练习完成
    finishPractice()
  } else {
    nextQuestion()
  }
}

const finishPractice = () => {
  stopTimer()
  ElMessageBox.confirm(
    '恭喜完成练习！是否查看练习报告？',
    '练习完成',
    {
      confirmButtonText: '查看报告',
      cancelButtonText: '返回题库',
      type: 'success'
    }
  ).then(() => {
    // 跳转到练习报告页面
    router.push(`/practice/${bankId.value}/report`)
  }).catch(() => {
    router.push(`/banks/${bankId.value}`)
  })
}

const exitPractice = () => {
  ElMessageBox.confirm(
    '确定要退出练习吗？当前进度将会保存。',
    '退出练习',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    stopTimer()
    router.push(`/practice/${bankId.value}`)
  })
}

const toggleFavorite = async () => {
  if (!currentQuestion.value) return
  
  try {
    if (isFavorited.value) {
      await questionsApi.unfavoriteQuestion(currentQuestion.value.id)
      isFavorited.value = false
      ElMessage.success('已取消收藏')
    } else {
      await questionsApi.favoriteQuestion(currentQuestion.value.id)
      isFavorited.value = true
      ElMessage.success('已添加收藏')
    }
  } catch (error) {
    console.error('收藏操作失败:', error)
    ElMessage.error('操作失败，请稍后重试')
  }
}

const checkFavoriteStatus = async () => {
  if (!currentQuestion.value) return

  try {
    const response = await questionsApi.getQuestionDetail(currentQuestion.value.id)
    isFavorited.value = response.data.is_favorited || false
  } catch (error) {
    console.error('检查收藏状态失败:', error)
  }
}

// 答题卡相关方法
const getQuestionItemClass = (index: number) => {
  const question = questions.value[index]
  if (!question) return ''

  const classes = []

  // 当前题目
  if (index === currentIndex.value) {
    classes.push('current')
    return classes.join(' ')
  }

  // 答题状态
  if (answers.value.has(question.id)) {
    const result = answerResults.value.get(question.id)
    if (result) {
      // 已提交答案，根据结果显示
      if (result.is_correct) {
        classes.push('correct')
      } else {
        classes.push('incorrect')
      }
    } else {
      // 已答但未提交
      classes.push('answered')
    }
  } else {
    classes.push('unanswered')
  }

  return classes.join(' ')
}

const jumpToQuestion = (index: number) => {
  if (index >= 0 && index < questions.value.length) {
    saveCurrentAnswer()
    currentIndex.value = index
    loadCurrentAnswer()
    checkFavoriteStatus()
    showAnswerCard.value = false
  }
}

const jumpToFirstUnanswered = () => {
  for (let i = 0; i < questions.value.length; i++) {
    const question = questions.value[i]
    if (!answers.value.has(question.id)) {
      jumpToQuestion(i)
      return
    }
  }
  ElMessage.info('所有题目都已答完')
}

const jumpToFirstIncorrect = () => {
  for (let i = 0; i < questions.value.length; i++) {
    const question = questions.value[i]
    const result = answerResults.value.get(question.id)
    if (result && !result.is_correct) {
      jumpToQuestion(i)
      return
    }
  }
  ElMessage.info('没有找到错题')
}

const fetchQuestions = async () => {
  try {
    let questionList = []

    if (mode.value === 'type' && questionType.value) {
      // 按题型练习模式，使用专门的API
      const response = await fetch(`/api/v1/questions/by-type?bank_id=${bankId.value}&type=${questionType.value}&per_page=${questionCount.value || 2000}`)
      const data = await response.json()
      questionList = data.questions || []
    } else {
      // 普通练习模式
      const params: any = {
        bank_id: bankId.value,
        per_page: questionCount.value || 2000  // 增加限制以支持更多题目
      }

      if (questionType.value) {
        params.type = questionType.value
      }

      if (difficulty.value) {
        params.difficulty = difficulty.value
      }

      const response = await questionsApi.getQuestions(params)
      questionList = response.data.data
    }
    
    // 根据模式处理题目顺序
    if (mode.value === 'random') {
      questionList = questionList.sort(() => Math.random() - 0.5)
    }
    
    if (questionCount.value > 0) {
      questionList = questionList.slice(0, questionCount.value)
    }
    
    questions.value = questionList
    
    if (questions.value.length === 0) {
      ElMessage.warning('没有找到符合条件的题目')
      router.push(`/practice/${bankId.value}`)
      return
    }
    
    loadCurrentAnswer()
    checkFavoriteStatus()
    
  } catch (error) {
    console.error('获取题目失败:', error)
    ElMessage.error('获取题目失败')
    router.push(`/practice/${bankId.value}`)
  }
}

const fetchBankDetail = async () => {
  try {
    const response = await banksStore.fetchBankDetail(bankId.value)
    bank.value = response.data
  } catch (error) {
    console.error('获取题库详情失败:', error)
    ElMessage.error('题库不存在或无权访问')
    router.push('/banks')
  }
}

// 键盘快捷键处理
const handleKeydown = (event: KeyboardEvent) => {
  // 如果正在输入文本，不处理快捷键
  if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
    return
  }

  switch (event.key) {
    case 'ArrowLeft':
      event.preventDefault()
      if (currentIndex.value > 0) {
        previousQuestion()
      }
      break
    case 'ArrowRight':
      event.preventDefault()
      if (currentIndex.value < questions.value.length - 1) {
        nextQuestion()
      }
      break
    case 'Enter':
      event.preventDefault()
      if (hasAnswer.value && !submitting.value) {
        submitAnswer()
      }
      break
    case 'Escape':
      event.preventDefault()
      if (showAnswerCard.value) {
        showAnswerCard.value = false
      } else if (showResultDialog.value) {
        showResultDialog.value = false
      }
      break
    case 'Tab':
      event.preventDefault()
      showAnswerCard.value = !showAnswerCard.value
      break
  }
}

onMounted(() => {
  fetchBankDetail()
  fetchQuestions()
  startTimer()
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  stopTimer()
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.practice-session {
  min-height: 100vh;
  background-color: var(--background-base);
  padding: 0;
}

.session-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.session-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 16px 24px;
  border-radius: 12px;
  box-shadow: var(--shadow-base);
  margin-bottom: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.session-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.bank-name {
  font-weight: 600;
  color: var(--text-primary);
}

.mode-text {
  font-size: 14px;
  color: var(--text-secondary);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.progress-info {
  font-weight: 600;
  color: var(--text-primary);
}

.timer {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--primary-color);
  font-weight: 600;
}

.progress-bar {
  margin-bottom: 24px;
}

.question-content {
  margin-bottom: 32px;
}

.question-card {
  background: white;
  border-radius: 12px;
  padding: 32px;
  box-shadow: var(--shadow-base);
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.question-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.type-tag {
  font-size: 12px;
  font-weight: 600;
}

.question-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.question-points {
  font-size: 14px;
  color: var(--text-secondary);
}

.question-title h2 {
  margin: 0 0 24px 0;
  font-size: 20px;
  line-height: 1.6;
  color: var(--text-primary);
}

.question-text {
  margin-bottom: 24px;
  line-height: 1.8;
  color: var(--text-primary);
}

.question-hint {
  margin-bottom: 16px;
}

.choices {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.choice-option {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border: 2px solid var(--border-light);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
}

.choice-option:hover {
  border-color: var(--primary-color);
  background-color: var(--primary-light);
}

.choice-option.selected {
  border-color: var(--primary-color);
  background-color: var(--primary-light);
}

.option-key {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary-color);
  color: white;
  border-radius: 50%;
  font-weight: 600;
  flex-shrink: 0;
}

.option-text {
  flex: 1;
  line-height: 1.6;
}

.option-check {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--primary-color);
  font-size: 18px;
}

.true-false-options {
  display: flex;
  gap: 24px;
  justify-content: center;
}

.tf-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px;
  border: 2px solid var(--border-light);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
  min-width: 120px;
}

.tf-option:hover {
  border-color: var(--primary-color);
  background-color: var(--primary-light);
}

.tf-option.selected {
  border-color: var(--primary-color);
  background-color: var(--primary-light);
}

.tf-option .el-icon {
  font-size: 32px;
  color: var(--primary-color);
}

.answer-input,
.code-input {
  margin-top: 16px;
}

.code-editor {
  margin-top: 16px;
}

.session-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 20px 24px;
  border-radius: 12px;
  box-shadow: var(--shadow-base);
}

.center-actions {
  display: flex;
  gap: 12px;
}

.result-content {
  padding: 8px 0;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.result-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ff4d4f;
  color: white;
  font-size: 24px;
}

.result-icon.correct {
  background: #52c41a;
}

.result-text h3 {
  margin: 0 0 4px 0;
  font-size: 18px;
}

.result-text p {
  margin: 0;
  color: var(--text-secondary);
}

.answer-comparison {
  margin-bottom: 24px;
}

.answer-item {
  margin-bottom: 12px;
}

.answer-item label {
  display: block;
  font-weight: 600;
  margin-bottom: 4px;
  color: var(--text-primary);
}

.answer-value {
  padding: 8px 12px;
  background: var(--background-light);
  border-radius: 6px;
  border-left: 3px solid #ff4d4f;
}

.answer-value.correct {
  border-left-color: #52c41a;
}

.explanation label {
  display: block;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.explanation-content {
  padding: 16px;
  background: var(--background-light);
  border-radius: 8px;
  line-height: 1.6;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 答题卡样式 */
.answer-card {
  padding: 16px 0;
}

.answer-stats {
  margin-bottom: 24px;
  padding: 16px;
  background: var(--background-light);
  border-radius: 8px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.stat-item:last-child {
  margin-bottom: 0;
}

.stat-label {
  color: var(--text-secondary);
  font-size: 14px;
}

.stat-value {
  font-weight: 600;
  font-size: 16px;
}

.stat-value.answered {
  color: #409eff;
}

.stat-value.unanswered {
  color: #909399;
}

.stat-value.correct {
  color: #67c23a;
}

.stat-value.incorrect {
  color: #f56c6c;
}

.question-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}

.question-item {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--border-light);
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s;
  background: white;
}

.question-item:hover {
  border-color: var(--primary-color);
  transform: translateY(-2px);
}

.question-item.current {
  border-color: var(--primary-color);
  background: var(--primary-color);
  color: white;
}

.question-item.answered {
  border-color: #409eff;
  background: #409eff;
  color: white;
}

.question-item.correct {
  border-color: #67c23a;
  background: #67c23a;
  color: white;
}

.question-item.incorrect {
  border-color: #f56c6c;
  background: #f56c6c;
  color: white;
}

.question-item.unanswered {
  border-color: #dcdfe6;
  background: white;
  color: var(--text-primary);
}

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  border: 2px solid;
}

.legend-color.current {
  background: var(--primary-color);
  border-color: var(--primary-color);
}

.legend-color.correct {
  background: #67c23a;
  border-color: #67c23a;
}

.legend-color.incorrect {
  background: #f56c6c;
  border-color: #f56c6c;
}

.legend-color.answered {
  background: #409eff;
  border-color: #409eff;
}

.legend-color.unanswered {
  background: white;
  border-color: #dcdfe6;
}

.quick-actions {
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.shortcuts-hint {
  margin-top: 20px;
  padding: 12px;
  background: var(--background-light);
  border-radius: 6px;
  font-size: 12px;
  color: var(--text-secondary);
}

.hint-title {
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.hint-item {
  margin-bottom: 4px;
}

@media (max-width: 768px) {
  .session-container {
    padding: 12px;
  }

  .session-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }

  .header-left,
  .header-right {
    justify-content: space-between;
  }

  .question-card {
    padding: 20px;
  }

  .question-header {
    flex-direction: column;
    gap: 12px;
  }

  .true-false-options {
    flex-direction: column;
    align-items: stretch;
  }

  .session-actions {
    flex-direction: column;
    gap: 16px;
  }

  .center-actions {
    order: -1;
  }

  .question-grid {
    grid-template-columns: repeat(4, 1fr);
  }

  .question-item {
    width: 40px;
    height: 40px;
  }

  .legend {
    flex-direction: column;
    gap: 8px;
  }
}
</style>
