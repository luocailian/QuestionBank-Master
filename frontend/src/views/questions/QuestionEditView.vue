<template>
  <div class="question-edit-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button @click="$router.go(-1)" circle>
          <el-icon><ArrowLeft /></el-icon>
        </el-button>
        <div class="header-info">
          <h1 class="page-title">编辑题目</h1>
          <p class="page-subtitle" v-if="question">题目ID: {{ question.id }}</p>
        </div>
      </div>
      <div class="header-actions">
        <el-button @click="$router.go(-1)">取消</el-button>
        <el-button type="primary" @click="saveQuestion" :loading="saving">
          保存修改
        </el-button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="8" animated />
    </div>

    <!-- 编辑表单 -->
    <div v-else-if="question" class="edit-form">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <!-- 题目内容 -->
        <el-form-item label="题目内容" prop="content">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="4"
            placeholder="请输入题目内容"
          />
        </el-form-item>

        <!-- 题目类型 -->
        <el-form-item label="题目类型" prop="type">
          <el-select v-model="form.type" placeholder="请选择题目类型">
            <el-option label="单选题" value="single_choice" />
            <el-option label="多选题" value="multiple_choice" />
            <el-option label="判断题" value="true_false" />
            <el-option label="问答题" value="qa" />
            <el-option label="填空题" value="fill_blank" />
          </el-select>
        </el-form-item>

        <!-- 选择题选项 -->
        <div v-if="form.type === 'single_choice' || form.type === 'multiple_choice'">
          <el-form-item label="选项" prop="options">
            <div class="options-editor">
              <div 
                v-for="(option, index) in form.options" 
                :key="index"
                class="option-item"
              >
                <span class="option-label">{{ String.fromCharCode(65 + index) }}.</span>
                <el-input
                  v-model="option.text"
                  placeholder="请输入选项内容"
                  class="option-input"
                />
                <el-button 
                  v-if="form.options.length > 2"
                  @click="removeOption(index)"
                  :icon="Delete"
                  circle
                  size="small"
                  type="danger"
                />
              </div>
              <el-button 
                @click="addOption"
                :icon="Plus"
                type="primary"
                plain
                size="small"
              >
                添加选项
              </el-button>
            </div>
          </el-form-item>

          <!-- 正确答案 -->
          <el-form-item label="正确答案" prop="correctAnswer">
            <el-checkbox-group v-if="form.type === 'multiple_choice'" v-model="form.correctAnswer">
              <el-checkbox 
                v-for="(option, index) in form.options"
                :key="index"
                :label="String.fromCharCode(65 + index)"
              >
                {{ String.fromCharCode(65 + index) }}. {{ option.text }}
              </el-checkbox>
            </el-checkbox-group>
            <el-radio-group v-else v-model="form.correctAnswer">
              <el-radio 
                v-for="(option, index) in form.options"
                :key="index"
                :label="String.fromCharCode(65 + index)"
              >
                {{ String.fromCharCode(65 + index) }}. {{ option.text }}
              </el-radio>
            </el-radio-group>
          </el-form-item>
        </div>

        <!-- 判断题答案 -->
        <el-form-item v-if="form.type === 'true_false'" label="正确答案" prop="correctAnswer">
          <el-radio-group v-model="form.correctAnswer">
            <el-radio label="true">正确</el-radio>
            <el-radio label="false">错误</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 问答题答案 -->
        <el-form-item v-if="form.type === 'qa'" label="参考答案" prop="correctAnswer">
          <el-input
            v-model="form.correctAnswer"
            type="textarea"
            :rows="4"
            placeholder="请输入参考答案"
          />
        </el-form-item>

        <!-- 难度 -->
        <el-form-item label="难度" prop="difficulty">
          <el-select v-model="form.difficulty" placeholder="请选择难度">
            <el-option label="简单" value="easy" />
            <el-option label="中等" value="medium" />
            <el-option label="困难" value="hard" />
          </el-select>
        </el-form-item>

        <!-- 分值 -->
        <el-form-item label="分值" prop="points">
          <el-input-number v-model="form.points" :min="1" :max="100" />
        </el-form-item>

        <!-- 解析 -->
        <el-form-item label="题目解析">
          <el-input
            v-model="form.explanation"
            type="textarea"
            :rows="4"
            placeholder="请输入题目解析（可选）"
          />
        </el-form-item>
      </el-form>
    </div>

    <!-- 错误状态 -->
    <div v-else class="error-state">
      <el-result
        icon="error"
        title="加载失败"
        sub-title="无法加载题目信息"
      >
        <template #extra>
          <el-button type="primary" @click="fetchQuestion">重试</el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Delete, Plus } from '@element-plus/icons-vue'
import { questionsApi } from '@/api/questions'

const route = useRoute()
const router = useRouter()
const formRef = ref()

const bankId = parseInt(route.params.bankId as string)
const questionId = parseInt(route.params.questionId as string)

const loading = ref(true)
const saving = ref(false)
const question = ref<any>(null)

// 表单数据
const form = reactive({
  content: '',
  type: 'single_choice',
  options: [
    { text: '' },
    { text: '' }
  ],
  correctAnswer: '',
  difficulty: 'medium',
  points: 1,
  explanation: ''
})

// 表单验证规则
const rules = {
  content: [
    { required: true, message: '请输入题目内容', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择题目类型', trigger: 'change' }
  ],
  correctAnswer: [
    { required: true, message: '请设置正确答案', trigger: 'change' }
  ],
  difficulty: [
    { required: true, message: '请选择难度', trigger: 'change' }
  ],
  points: [
    { required: true, message: '请设置分值', trigger: 'blur' }
  ]
}

// 获取题目详情
const fetchQuestion = async () => {
  try {
    loading.value = true
    const response = await questionsApi.getQuestionDetail(questionId)
    question.value = response.data
    
    // 填充表单数据
    form.content = question.value.title || ''

    // 处理题目类型映射
    if (question.value.type === 'choice') {
      // 根据答案长度判断是单选还是多选
      const correctAnswer = question.value.answer?.correct_option || ''
      form.type = correctAnswer.length > 1 ? 'multiple_choice' : 'single_choice'
    } else {
      form.type = question.value.type || 'single_choice'
    }

    form.difficulty = question.value.difficulty || 'medium'
    form.points = question.value.points || 1
    form.explanation = question.value.explanation || ''

    // 处理选择题选项
    if (question.value.content?.options) {
      form.options = question.value.content.options.map((opt: any) => ({
        text: opt.text || opt
      }))
    }

    // 处理答案
    if (question.value.answer?.correct_option) {
      const correctOption = question.value.answer.correct_option
      if (form.type === 'multiple_choice') {
        // 多选题：将字符串拆分为数组
        form.correctAnswer = correctOption.split('')
      } else {
        // 单选题：直接使用
        form.correctAnswer = correctOption
      }
    } else if (question.value.answer?.is_correct !== undefined) {
      // 判断题
      form.correctAnswer = question.value.answer.is_correct ? 'true' : 'false'
    } else if (question.value.answer?.correct_answer) {
      // 问答题或其他类型
      form.correctAnswer = question.value.answer.correct_answer
    }
    
  } catch (error) {
    console.error('获取题目详情失败:', error)
    ElMessage.error('获取题目详情失败')
  } finally {
    loading.value = false
  }
}

// 添加选项
const addOption = () => {
  form.options.push({ text: '' })
}

// 删除选项
const removeOption = (index: number) => {
  form.options.splice(index, 1)
}

// 保存题目
const saveQuestion = async () => {
  try {
    await formRef.value.validate()
    saving.value = true
    
    // 构建更新数据
    const updateData: any = {
      content: {
        question: form.content
      },
      type: form.type,
      difficulty: form.difficulty,
      points: form.points,
      explanation: form.explanation
    }
    
    // 处理选择题数据
    if (form.type === 'single_choice' || form.type === 'multiple_choice') {
      updateData.content.options = form.options.map(opt => opt.text)
      updateData.answer = {
        correct_option: Array.isArray(form.correctAnswer) 
          ? form.correctAnswer.join('') 
          : form.correctAnswer
      }
    } else if (form.type === 'true_false') {
      updateData.answer = {
        correct_option: form.correctAnswer
      }
    } else if (form.type === 'qa') {
      updateData.answer = {
        correct_answer: form.correctAnswer
      }
    }
    
    await questionsApi.updateQuestion(questionId, updateData)
    ElMessage.success('题目更新成功')
    router.go(-1)
    
  } catch (error) {
    console.error('保存题目失败:', error)
    ElMessage.error('保存题目失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchQuestion()
})
</script>

<style scoped>
.question-edit-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--el-border-color-light);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0;
}

.page-subtitle {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin: 0;
}

.loading-container {
  padding: 24px;
}

.edit-form {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.options-editor {
  width: 100%;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.option-label {
  font-weight: 600;
  min-width: 24px;
}

.option-input {
  flex: 1;
}

.error-state {
  text-align: center;
  padding: 64px 24px;
}

@media (max-width: 768px) {
  .question-edit-container {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .header-actions {
    width: 100%;
    display: flex;
    justify-content: flex-end;
    gap: 12px;
  }
}
</style>
