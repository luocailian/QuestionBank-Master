<template>
  <el-dialog
    v-model="visible"
    title="编辑题库"
    width="600px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="80px"
      @submit.prevent="handleSubmit"
    >
      <el-form-item label="题库名称" prop="name">
        <el-input
          v-model="form.name"
          placeholder="请输入题库名称"
          maxlength="100"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="题库描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="请输入题库描述"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="分类" prop="category">
        <el-select
          v-model="form.category"
          placeholder="请选择分类"
          filterable
          allow-create
          style="width: 100%"
        >
          <el-option
            v-for="category in categories"
            :key="category"
            :label="category"
            :value="category"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="难度等级" prop="difficulty">
        <el-select
          v-model="form.difficulty"
          placeholder="请选择难度等级"
          style="width: 100%"
        >
          <el-option label="简单" value="easy" />
          <el-option label="中等" value="medium" />
          <el-option label="困难" value="hard" />
        </el-select>
      </el-form-item>

      <el-form-item label="标签" prop="tags">
        <el-select
          v-model="form.tags"
          multiple
          filterable
          allow-create
          placeholder="请选择或输入标签"
          style="width: 100%"
        >
          <el-option
            v-for="tag in availableTags"
            :key="tag"
            :label="tag"
            :value="tag"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="公开设置" prop="is_public">
        <el-switch
          v-model="form.is_public"
          active-text="公开"
          inactive-text="私有"
        />
        <div class="form-tip">
          公开的题库其他用户可以查看和练习
        </div>
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="primary"
          :loading="loading"
          @click="handleSubmit"
        >
          保存
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { banksApi } from '@/api/banks'
import type { QuestionBank, BankCreateForm } from '@/types/banks'

interface Props {
  modelValue: boolean
  bank?: QuestionBank | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = withDefaults(defineProps<Props>(), {
  bank: null
})

const emit = defineEmits<Emits>()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const formRef = ref<FormInstance>()
const loading = ref(false)
const categories = ref<string[]>([])
const availableTags = ref<string[]>([])

const form = reactive<BankCreateForm>({
  name: '',
  description: '',
  category: '',
  difficulty: '',
  tags: [],
  is_public: false
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入题库名称', trigger: 'blur' },
    { min: 2, max: 100, message: '题库名称长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  description: [
    { max: 500, message: '描述不能超过 500 个字符', trigger: 'blur' }
  ],
  category: [
    { required: true, message: '请选择分类', trigger: 'change' }
  ]
}

// 监听bank变化，初始化表单
watch(() => props.bank, (bank) => {
  if (bank) {
    form.name = bank.name
    form.description = bank.description || ''
    form.category = bank.category || ''
    form.difficulty = bank.difficulty || ''
    form.tags = bank.tags || []
    form.is_public = bank.is_public || false
  }
}, { immediate: true })

// 监听对话框显示，获取分类数据
watch(visible, async (show) => {
  if (show) {
    await fetchCategories()
  }
})

const fetchCategories = async () => {
  try {
    const response = await banksApi.getCategories()
    categories.value = response.data || []
    
    // 从分类中提取常用标签
    availableTags.value = [
      '计算机', '数学', '英语', '物理', '化学', '生物',
      '历史', '地理', '政治', '语文', '考试', '练习',
      '基础', '进阶', '专业', '综合'
    ]
  } catch (error) {
    console.error('获取分类失败:', error)
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    
    if (!props.bank) {
      ElMessage.error('题库信息不存在')
      return
    }

    loading.value = true
    
    await banksApi.updateBank(props.bank.id, form)
    
    ElMessage.success('题库更新成功')
    emit('success')
    handleClose()
  } catch (error: any) {
    if (error.response?.data?.message) {
      ElMessage.error(error.response.data.message)
    } else {
      ElMessage.error('更新失败，请稍后重试')
    }
  } finally {
    loading.value = false
  }
}

const handleClose = () => {
  visible.value = false
  formRef.value?.resetFields()
}
</script>

<style scoped>
.form-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

.dialog-footer {
  text-align: right;
}
</style>
