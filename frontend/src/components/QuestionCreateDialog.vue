<template>
  <el-dialog
    v-model="visible"
    title="创建题目"
    width="800px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item label="题目类型" prop="type">
        <el-select v-model="form.type" @change="handleTypeChange">
          <el-option label="选择题" value="choice" />
          <el-option label="判断题" value="true_false" />
          <el-option label="问答题" value="qa" />
          <el-option label="数学题" value="math" />
          <el-option label="编程题" value="programming" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="题目标题" prop="title">
        <el-input 
          v-model="form.title" 
          type="textarea"
          :rows="3"
          placeholder="请输入题目内容"
        />
      </el-form-item>
      
      <!-- 选择题选项 -->
      <div v-if="form.type === 'choice'">
        <el-form-item 
          v-for="(option, index) in choiceOptions" 
          :key="index"
          :label="`选项${option.key}`"
          :prop="`options.${index}`"
        >
          <div class="option-input">
            <el-input 
              v-model="option.text" 
              placeholder="请输入选项内容"
            />
            <el-radio 
              v-model="correctOption" 
              :label="option.key"
              style="margin-left: 12px;"
            >
              正确答案
            </el-radio>
            <el-button 
              v-if="choiceOptions.length > 2"
              type="danger" 
              size="small"
              @click="removeOption(index)"
              style="margin-left: 8px;"
            >
              删除
            </el-button>
          </div>
        </el-form-item>
        
        <el-form-item>
          <el-button 
            v-if="choiceOptions.length < 6"
            @click="addOption"
            type="primary"
            plain
          >
            添加选项
          </el-button>
        </el-form-item>
      </div>
      
      <!-- 判断题答案 -->
      <el-form-item v-if="form.type === 'true_false'" label="正确答案" prop="answer">
        <el-radio-group v-model="trueFalseAnswer">
          <el-radio :label="true">正确</el-radio>
          <el-radio :label="false">错误</el-radio>
        </el-radio-group>
      </el-form-item>
      
      <!-- 问答题关键词 -->
      <el-form-item v-if="form.type === 'qa'" label="参考答案" prop="answer">
        <el-input 
          v-model="qaAnswer" 
          type="textarea"
          :rows="3"
          placeholder="请输入参考答案或关键词"
        />
      </el-form-item>
      
      <!-- 数学题答案 -->
      <el-form-item v-if="form.type === 'math'" label="数值答案" prop="answer">
        <el-input-number 
          v-model="mathAnswer" 
          :precision="2"
          placeholder="请输入数值答案"
        />
      </el-form-item>
      
      <!-- 编程题测试用例 -->
      <div v-if="form.type === 'programming'">
        <el-form-item label="测试用例" prop="answer">
          <el-input 
            v-model="programmingAnswer" 
            type="textarea"
            :rows="4"
            placeholder="请输入测试用例或预期输出"
          />
        </el-form-item>
      </div>
      
      <el-form-item label="题目解析">
        <el-input 
          v-model="form.explanation" 
          type="textarea"
          :rows="3"
          placeholder="请输入题目解析（可选）"
        />
      </el-form-item>
      
      <el-form-item label="难度" prop="difficulty">
        <el-select v-model="form.difficulty">
          <el-option label="简单" value="easy" />
          <el-option label="中等" value="medium" />
          <el-option label="困难" value="hard" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="分值" prop="points">
        <el-input-number 
          v-model="form.points" 
          :min="1" 
          :max="100"
        />
      </el-form-item>
      
      <el-form-item label="标签">
        <el-select
          v-model="form.tags"
          multiple
          filterable
          allow-create
          placeholder="添加标签"
          style="width: 100%"
        >
          <el-option
            v-for="tag in commonTags"
            :key="tag"
            :label="tag"
            :value="tag"
          />
        </el-select>
      </el-form-item>
    </el-form>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" :loading="loading" @click="handleSubmit">
          创建
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { questionsApi } from '@/api/questions'
import type { QuestionCreateForm, QuestionType } from '@/types/questions'

interface Props {
  modelValue: boolean
  bankId: number
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const visible = ref(false)
const loading = ref(false)
const formRef = ref<FormInstance>()

const form = reactive<QuestionCreateForm>({
  bank_id: props.bankId,
  type: 'choice',
  title: '',
  content: {},
  answer: {},
  explanation: '',
  difficulty: 'medium',
  tags: [],
  points: 1
})

// 选择题选项
const choiceOptions = ref([
  { key: 'A', text: '' },
  { key: 'B', text: '' },
  { key: 'C', text: '' },
  { key: 'D', text: '' }
])
const correctOption = ref('A')

// 其他题型答案
const trueFalseAnswer = ref(true)
const qaAnswer = ref('')
const mathAnswer = ref(0)
const programmingAnswer = ref('')

const commonTags = [
  '基础', '进阶', '重点', '难点', '常考',
  '概念', '计算', '应用', '分析', '综合'
]

const rules: FormRules = {
  type: [
    { required: true, message: '请选择题目类型', trigger: 'change' }
  ],
  title: [
    { required: true, message: '请输入题目标题', trigger: 'blur' },
    { min: 5, message: '题目标题至少5个字符', trigger: 'blur' }
  ],
  difficulty: [
    { required: true, message: '请选择难度', trigger: 'change' }
  ],
  points: [
    { required: true, message: '请设置分值', trigger: 'blur' },
    { type: 'number', min: 1, max: 100, message: '分值范围1-100', trigger: 'blur' }
  ]
}

const handleTypeChange = (type: QuestionType) => {
  // 重置相关数据
  form.content = {}
  form.answer = {}
  
  if (type === 'choice') {
    choiceOptions.value = [
      { key: 'A', text: '' },
      { key: 'B', text: '' },
      { key: 'C', text: '' },
      { key: 'D', text: '' }
    ]
    correctOption.value = 'A'
  }
}

const addOption = () => {
  const nextKey = String.fromCharCode(65 + choiceOptions.value.length) // A, B, C, D, E, F
  choiceOptions.value.push({ key: nextKey, text: '' })
}

const removeOption = (index: number) => {
  choiceOptions.value.splice(index, 1)
  // 重新分配选项键
  choiceOptions.value.forEach((option, i) => {
    option.key = String.fromCharCode(65 + i)
  })
  // 如果删除的是正确答案，重置为A
  if (!choiceOptions.value.find(opt => opt.key === correctOption.value)) {
    correctOption.value = 'A'
  }
}

const buildQuestionData = (): QuestionCreateForm => {
  const questionData = { ...form }
  
  switch (form.type) {
    case 'choice':
      questionData.content = {
        options: choiceOptions.value.filter(opt => opt.text.trim())
      }
      questionData.answer = {
        correct_option: correctOption.value
      }
      break
      
    case 'true_false':
      questionData.content = {}
      questionData.answer = {
        is_true: trueFalseAnswer.value
      }
      break
      
    case 'qa':
      questionData.content = {}
      questionData.answer = {
        keywords: qaAnswer.value.split(/[,，\n]/).map(k => k.trim()).filter(k => k)
      }
      break
      
    case 'math':
      questionData.content = {}
      questionData.answer = {
        result: mathAnswer.value
      }
      break
      
    case 'programming':
      questionData.content = {}
      questionData.answer = {
        test_cases: programmingAnswer.value
      }
      break
  }
  
  return questionData
}

const validateQuestionData = (): boolean => {
  switch (form.type) {
    case 'choice':
      const validOptions = choiceOptions.value.filter(opt => opt.text.trim())
      if (validOptions.length < 2) {
        ElMessage.error('选择题至少需要2个选项')
        return false
      }
      if (!validOptions.find(opt => opt.key === correctOption.value)) {
        ElMessage.error('请选择正确答案')
        return false
      }
      break
      
    case 'qa':
      if (!qaAnswer.value.trim()) {
        ElMessage.error('请输入参考答案')
        return false
      }
      break
  }
  
  return true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    if (!validateQuestionData()) {
      return
    }
    
    loading.value = true
    const questionData = buildQuestionData()
    
    await questionsApi.createQuestion(questionData)
    
    ElMessage.success('题目创建成功')
    emit('success')
    handleClose()
  } catch (error: any) {
    if (error.response?.data?.message) {
      ElMessage.error(error.response.data.message)
    }
  } finally {
    loading.value = false
  }
}

const handleClose = () => {
  visible.value = false
  emit('update:modelValue', false)
  
  // 重置表单
  if (formRef.value) {
    formRef.value.resetFields()
  }
  
  // 重置数据
  Object.assign(form, {
    bank_id: props.bankId,
    type: 'choice',
    title: '',
    content: {},
    answer: {},
    explanation: '',
    difficulty: 'medium',
    tags: [],
    points: 1
  })
  
  choiceOptions.value = [
    { key: 'A', text: '' },
    { key: 'B', text: '' },
    { key: 'C', text: '' },
    { key: 'D', text: '' }
  ]
  correctOption.value = 'A'
  trueFalseAnswer.value = true
  qaAnswer.value = ''
  mathAnswer.value = 0
  programmingAnswer.value = ''
}

watch(
  () => props.modelValue,
  (val) => {
    visible.value = val
    if (val) {
      form.bank_id = props.bankId
    }
  },
  { immediate: true }
)

watch(visible, (val) => {
  if (!val) {
    emit('update:modelValue', false)
  }
})
</script>

<style scoped>
.option-input {
  display: flex;
  align-items: center;
  width: 100%;
}

.option-input .el-input {
  flex: 1;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 768px) {
  .option-input {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
}
</style>
