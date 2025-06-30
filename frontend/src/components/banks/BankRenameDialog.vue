<template>
  <el-dialog
    v-model="visible"
    title="重命名题库"
    width="400px"
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
          placeholder="请输入新的题库名称"
          maxlength="100"
          show-word-limit
          @keyup.enter="handleSubmit"
        />
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
          确定
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { banksApi } from '@/api/banks'
import type { QuestionBank } from '@/types/banks'

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

const form = reactive({
  name: ''
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入题库名称', trigger: 'blur' },
    { min: 2, max: 100, message: '题库名称长度在 2 到 100 个字符', trigger: 'blur' }
  ]
}

// 监听bank变化，初始化表单
watch(() => props.bank, (bank) => {
  if (bank) {
    form.name = bank.name
  }
}, { immediate: true })

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    
    if (!props.bank) {
      ElMessage.error('题库信息不存在')
      return
    }

    if (form.name === props.bank.name) {
      ElMessage.info('题库名称未发生变化')
      return
    }

    loading.value = true
    
    await banksApi.updateBank(props.bank.id, { name: form.name })
    
    ElMessage.success('题库重命名成功')
    emit('success')
    handleClose()
  } catch (error: any) {
    if (error.response?.data?.message) {
      ElMessage.error(error.response.data.message)
    } else {
      ElMessage.error('重命名失败，请稍后重试')
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
.dialog-footer {
  text-align: right;
}
</style>
