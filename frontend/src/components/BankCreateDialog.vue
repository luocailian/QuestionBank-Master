<template>
  <el-dialog
    v-model="visible"
    title="创建题库"
    width="500px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="80px"
    >
      <el-form-item label="题库名称" prop="name">
        <el-input v-model="form.name" placeholder="请输入题库名称" />
      </el-form-item>
      
      <el-form-item label="题库描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="请输入题库描述"
        />
      </el-form-item>
      
      <el-form-item label="分类" prop="category">
        <el-input v-model="form.category" placeholder="如：计算机、数学、英语等" />
      </el-form-item>
      
      <el-form-item label="难度" prop="difficulty">
        <el-select v-model="form.difficulty" placeholder="选择难度">
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
      
      <el-form-item label="公开设置">
        <el-switch
          v-model="form.is_public"
          active-text="公开"
          inactive-text="私有"
        />
        <div class="form-tip">
          公开题库所有用户都可以访问，私有题库只有你可以访问
        </div>
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
import { useBanksStore } from '@/stores/banks'
import type { BankCreateForm } from '@/types/banks'

interface Props {
  modelValue: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const banksStore = useBanksStore()

const visible = ref(false)
const loading = ref(false)
const formRef = ref<FormInstance>()

const form = reactive<BankCreateForm>({
  name: '',
  description: '',
  category: '',
  difficulty: 'medium',
  tags: [],
  is_public: true
})

const commonTags = [
  '基础知识', '进阶', '实战', '面试', '考试',
  '编程', '算法', '数据结构', '前端', '后端',
  '数学', '英语', '物理', '化学', '历史'
]

const rules: FormRules = {
  name: [
    { required: true, message: '请输入题库名称', trigger: 'blur' },
    { min: 2, max: 50, message: '题库名称长度为2-50个字符', trigger: 'blur' }
  ],
  description: [
    { max: 500, message: '描述不能超过500个字符', trigger: 'blur' }
  ],
  category: [
    { max: 20, message: '分类不能超过20个字符', trigger: 'blur' }
  ],
  difficulty: [
    { required: true, message: '请选择难度', trigger: 'change' }
  ]
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    loading.value = true
    await banksStore.createBank(form)
    
    ElMessage.success('题库创建成功')
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
  Object.assign(form, {
    name: '',
    description: '',
    category: '',
    difficulty: 'medium',
    tags: [],
    is_public: true
  })
}

watch(
  () => props.modelValue,
  (val) => {
    visible.value = val
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
.form-tip {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
