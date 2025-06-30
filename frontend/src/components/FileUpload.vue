<template>
  <div class="file-upload">
    <div class="upload-area">
      <el-upload
        ref="uploadRef"
        :action="uploadAction"
        :headers="uploadHeaders"
        :data="uploadData"
        :before-upload="beforeUpload"
        :on-success="handleSuccess"
        :on-error="handleError"
        :show-file-list="false"
        drag
        accept=".pdf,.docx,.xlsx,.json"
      >
        <div class="upload-content">
          <el-icon size="48"><UploadFilled /></el-icon>
          <div class="upload-text">
            <p>将文件拖到此处，或<em>点击上传</em></p>
            <p class="upload-hint">支持 PDF、Word、Excel、JSON 格式</p>
          </div>
        </div>
      </el-upload>
    </div>

    <!-- 题库选择 -->
    <div class="bank-selection" v-if="banks.length > 0">
      <el-form-item label="导入到题库：">
        <el-select
          v-model="selectedBankId"
          placeholder="选择现有题库或创建新题库"
          clearable
          style="width: 100%"
        >
          <el-option
            v-for="bank in banks"
            :key="bank.id"
            :label="bank.name"
            :value="bank.id"
          />
        </el-select>
        <div class="form-tip">
          如果不选择题库，将自动创建新题库
        </div>
      </el-form-item>
    </div>

    <!-- 上传进度 -->
    <div class="upload-progress" v-if="uploading">
      <el-progress :percentage="uploadProgress" />
      <p>正在上传文件...</p>
    </div>

    <!-- 解析进度 -->
    <div class="parse-progress" v-if="parsing">
      <el-progress :percentage="100" :indeterminate="true" />
      <p>正在解析文件，请稍候...</p>
    </div>

    <!-- 支持的格式说明 -->
    <div class="format-info">
      <h4>支持的文件格式：</h4>
      <ul>
        <li><strong>PDF：</strong>自动识别题目内容，支持文字和简单格式</li>
        <li><strong>Word：</strong>解析文档中的题目，保持原有格式</li>
        <li><strong>Excel：</strong>按表格结构导入，支持批量题目</li>
        <li><strong>JSON：</strong>标准题库格式，完整保留所有信息</li>
      </ul>
      <p class="size-limit">文件大小限制：50MB</p>
    </div>

    <!-- 导入记录 -->
    <div class="import-history" v-if="importRecords.length > 0">
      <h4>最近导入记录：</h4>
      <div class="record-list">
        <div 
          v-for="record in importRecords.slice(0, 5)" 
          :key="record.id"
          class="record-item"
        >
          <div class="record-info">
            <span class="filename">{{ record.filename }}</span>
            <span class="file-type">{{ record.file_type.toUpperCase() }}</span>
          </div>
          <div class="record-status">
            <el-tag 
              :type="getStatusType(record.status)"
              size="small"
            >
              {{ getStatusText(record.status) }}
            </el-tag>
            <span v-if="record.status === 'completed'" class="question-count">
              {{ record.questions_imported }} 题
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, type UploadInstance } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useBanksStore } from '@/stores/banks'
import { filesApi } from '@/api/files'
import type { QuestionBank } from '@/types/banks'
import type { FileImport } from '@/types/files'

interface Emits {
  (e: 'success', data: any): void
}

const emit = defineEmits<Emits>()

const authStore = useAuthStore()
const banksStore = useBanksStore()

const uploadRef = ref<UploadInstance>()
const uploading = ref(false)
const parsing = ref(false)
const uploadProgress = ref(0)
const selectedBankId = ref<number>()
const banks = ref<QuestionBank[]>([])
const importRecords = ref<FileImport[]>([])

const uploadAction = computed(() => '/api/v1/files/upload')
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${authStore.token}`
}))
const uploadData = computed(() => ({
  bank_id: selectedBankId.value
}))

const beforeUpload = (file: File) => {
  const isValidType = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/json'].includes(file.type)
  const isValidSize = file.size / 1024 / 1024 < 50

  if (!isValidType) {
    ElMessage.error('只支持 PDF、Word、Excel、JSON 格式的文件')
    return false
  }

  if (!isValidSize) {
    ElMessage.error('文件大小不能超过 50MB')
    return false
  }

  uploading.value = true
  uploadProgress.value = 0
  
  return true
}

const handleSuccess = async (response: any) => {
  uploading.value = false
  uploadProgress.value = 100
  
  try {
    // 开始解析文件
    parsing.value = true
    const parseResponse = await filesApi.parseFile(response.import_id)
    
    ElMessage.success(`文件解析成功，导入了 ${parseResponse.data.questions_imported} 道题目`)
    emit('success', parseResponse.data)
    
    // 刷新导入记录
    fetchImportRecords()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '文件解析失败')
  } finally {
    parsing.value = false
  }
}

const handleError = (error: any) => {
  uploading.value = false
  parsing.value = false
  ElMessage.error('文件上传失败')
  console.error('Upload error:', error)
}

const getStatusType = (status: string) => {
  const types = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return types[status as keyof typeof types] || 'info'
}

const getStatusText = (status: string) => {
  const texts = {
    pending: '等待处理',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return texts[status as keyof typeof texts] || status
}

const fetchBanks = async () => {
  try {
    const response = await banksStore.fetchBanks({ my_banks: true })
    banks.value = response.data
  } catch (error) {
    console.error('获取题库列表失败:', error)
  }
}

const fetchImportRecords = async () => {
  try {
    const response = await filesApi.getFileImports({ per_page: 10 })
    importRecords.value = response.data
  } catch (error) {
    console.error('获取导入记录失败:', error)
  }
}

onMounted(() => {
  if (authStore.isAuthenticated) {
    fetchBanks()
    fetchImportRecords()
  }
})
</script>

<style scoped>
.file-upload {
  max-width: 600px;
}

.upload-area {
  margin-bottom: 24px;
}

.upload-content {
  text-align: center;
  padding: 40px 20px;
}

.upload-text {
  margin-top: 16px;
}

.upload-text p {
  margin: 8px 0;
  color: var(--text-regular);
}

.upload-text em {
  color: var(--primary-color);
  font-style: normal;
}

.upload-hint {
  font-size: 12px;
  color: var(--text-secondary);
}

.bank-selection {
  margin-bottom: 24px;
  padding: 16px;
  background: var(--background-base);
  border-radius: 8px;
}

.form-tip {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.upload-progress,
.parse-progress {
  margin-bottom: 24px;
  padding: 16px;
  background: var(--background-base);
  border-radius: 8px;
  text-align: center;
}

.upload-progress p,
.parse-progress p {
  margin-top: 8px;
  color: var(--text-secondary);
}

.format-info {
  margin-bottom: 24px;
  padding: 16px;
  background: var(--background-base);
  border-radius: 8px;
}

.format-info h4 {
  margin-bottom: 12px;
  color: var(--text-primary);
}

.format-info ul {
  margin-bottom: 12px;
  padding-left: 20px;
}

.format-info li {
  margin-bottom: 8px;
  color: var(--text-regular);
  line-height: 1.5;
}

.size-limit {
  font-size: 12px;
  color: var(--text-secondary);
  margin: 0;
}

.import-history {
  padding: 16px;
  background: var(--background-base);
  border-radius: 8px;
}

.import-history h4 {
  margin-bottom: 12px;
  color: var(--text-primary);
}

.record-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.record-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid var(--border-light);
}

.record-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filename {
  font-size: 14px;
  color: var(--text-primary);
}

.file-type {
  font-size: 12px;
  color: var(--text-secondary);
  background: var(--border-extra-light);
  padding: 2px 6px;
  border-radius: 4px;
}

.record-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.question-count {
  font-size: 12px;
  color: var(--text-secondary);
}

@media (max-width: 768px) {
  .record-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .record-status {
    align-self: flex-end;
  }
}
</style>
