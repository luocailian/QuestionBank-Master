<template>
  <el-dialog
    v-model="visible"
    title="导出题库"
    width="500px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="export-content">
      <div class="bank-info">
        <h4>{{ bank?.name }}</h4>
        <p class="bank-desc">{{ bank?.description || '暂无描述' }}</p>
        <div class="bank-stats">
          <el-tag size="small">{{ bank?.question_count || 0 }} 道题目</el-tag>
          <el-tag size="small" type="info">{{ bank?.category || '未分类' }}</el-tag>
          <el-tag 
            size="small" 
            :type="getDifficultyType(bank?.difficulty)"
          >
            {{ getDifficultyText(bank?.difficulty) }}
          </el-tag>
        </div>
      </div>

      <el-divider />

      <div class="format-selection">
        <h5>选择导出格式</h5>
        <el-radio-group v-model="selectedFormat" class="format-options">
          <el-radio
            v-for="format in availableFormats"
            :key="format"
            :label="format"
            class="format-option"
          >
            <div class="format-info">
              <div class="format-name">
                <el-icon class="format-icon">
                  <component :is="getFormatIcon(format)" />
                </el-icon>
                {{ getFormatName(format) }}
              </div>
              <div class="format-desc">{{ getFormatDescription(format) }}</div>
            </div>
          </el-radio>
        </el-radio-group>
      </div>

      <div class="export-tips" v-if="selectedFormat">
        <el-alert
          :title="getFormatTips(selectedFormat)"
          type="info"
          :closable="false"
          show-icon
        />
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="primary"
          :loading="exporting"
          :disabled="!selectedFormat"
          @click="handleExport"
        >
          <el-icon><Download /></el-icon>
          导出
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Download, 
  Document, 
  Files, 
  Tickets, 
  Reading,
  Grid
} from '@element-plus/icons-vue'
import { banksApi } from '@/api/banks'
import type { QuestionBank } from '@/types/banks'

interface Props {
  modelValue: boolean
  bank?: QuestionBank | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
}

const props = withDefaults(defineProps<Props>(), {
  bank: null
})

const emit = defineEmits<Emits>()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const exporting = ref(false)
const selectedFormat = ref('')
const availableFormats = ref<string[]>([])
const formatDescriptions = ref<Record<string, string>>({})

// 获取可用的导出格式
const fetchExportFormats = async () => {
  try {
    const response = await banksApi.getExportFormats()
    availableFormats.value = response.data.formats || []
    formatDescriptions.value = response.data.format_descriptions || {}
    
    // 默认选择JSON格式
    if (availableFormats.value.length > 0 && !selectedFormat.value) {
      selectedFormat.value = availableFormats.value[0]
    }
  } catch (error) {
    console.error('获取导出格式失败:', error)
    ElMessage.error('获取导出格式失败')
  }
}

const getDifficultyType = (difficulty?: string) => {
  const types = {
    easy: 'success',
    medium: 'warning',
    hard: 'danger'
  }
  return types[difficulty as keyof typeof types] || 'info'
}

const getDifficultyText = (difficulty?: string) => {
  const texts = {
    easy: '简单',
    medium: '中等',
    hard: '困难'
  }
  return texts[difficulty as keyof typeof texts] || '未设置'
}

const getFormatIcon = (format: string) => {
  const icons = {
    json: Files,
    markdown: Reading,
    docx: Document,
    pdf: Tickets,
    xlsx: Grid
  }
  return icons[format as keyof typeof icons] || Document
}

const getFormatName = (format: string) => {
  const names = {
    json: 'JSON',
    markdown: 'Markdown',
    docx: 'Word文档',
    pdf: 'PDF文档',
    xlsx: 'Excel表格'
  }
  return names[format as keyof typeof names] || format.toUpperCase()
}

const getFormatDescription = (format: string) => {
  return formatDescriptions.value[format] || '标准格式'
}

const getFormatTips = (format: string) => {
  const tips = {
    json: '包含完整的题库数据，适合程序处理和数据备份',
    markdown: '文本格式，适合阅读和在线文档，支持GitHub等平台',
    docx: 'Microsoft Word格式，适合编辑和打印，需要Office软件',
    pdf: '便携式文档格式，适合分享和打印，保持格式不变',
    xlsx: 'Microsoft Excel格式，适合数据分析和表格处理'
  }
  return tips[format as keyof typeof tips] || '标准导出格式'
}

const handleExport = async () => {
  if (!props.bank || !selectedFormat.value) {
    ElMessage.error('请选择导出格式')
    return
  }

  try {
    exporting.value = true
    
    const response = await banksApi.exportBank(props.bank.id, selectedFormat.value)
    
    // 创建下载链接
    const blob = new Blob([response.data])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    // 生成文件名
    const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '')
    const extension = selectedFormat.value === 'markdown' ? 'md' : selectedFormat.value
    link.download = `${props.bank.name}_题库导出_${timestamp}.${extension}`
    
    // 触发下载
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('导出成功')
    handleClose()
  } catch (error: any) {
    console.error('导出失败:', error)
    if (error.response?.data?.message) {
      ElMessage.error(error.response.data.message)
    } else {
      ElMessage.error('导出失败，请稍后重试')
    }
  } finally {
    exporting.value = false
  }
}

const handleClose = () => {
  visible.value = false
  selectedFormat.value = ''
}

// 监听对话框显示
watch(visible, (show) => {
  if (show) {
    fetchExportFormats()
  }
})

onMounted(() => {
  fetchExportFormats()
})
</script>

<style scoped>
.export-content {
  padding: 8px 0;
}

.bank-info h4 {
  margin: 0 0 8px 0;
  color: var(--el-text-color-primary);
}

.bank-desc {
  margin: 0 0 12px 0;
  color: var(--el-text-color-regular);
  font-size: 14px;
}

.bank-stats {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.format-selection h5 {
  margin: 0 0 16px 0;
  color: var(--el-text-color-primary);
}

.format-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.format-option {
  margin: 0;
  padding: 12px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  transition: all 0.2s;
}

.format-option:hover {
  border-color: var(--el-color-primary);
  background-color: var(--el-color-primary-light-9);
}

.format-option.is-checked {
  border-color: var(--el-color-primary);
  background-color: var(--el-color-primary-light-9);
}

.format-info {
  margin-left: 8px;
}

.format-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
}

.format-icon {
  font-size: 16px;
}

.format-desc {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.export-tips {
  margin-top: 16px;
}

.dialog-footer {
  text-align: right;
}
</style>
