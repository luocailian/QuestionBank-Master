<template>
  <div class="bank-detail-page">
    <div class="page-container">
      <div class="container">
        <!-- 题库信息 -->
        <div class="bank-header" v-if="bank">
          <div class="bank-info">
            <div class="bank-title">
              <h1>{{ bank.name }}</h1>
              <div class="bank-meta">
                <el-tag v-if="bank.category" type="info">{{ bank.category }}</el-tag>
                <el-tag :type="getDifficultyType(bank.difficulty)">
                  {{ getDifficultyText(bank.difficulty) }}
                </el-tag>
                <span class="question-count">
                  <el-icon><Document /></el-icon>
                  {{ bank.question_count }} 题
                </span>
                <span class="creator">
                  <el-icon><User /></el-icon>
                  {{ bank.creator_name }}
                </span>
              </div>
            </div>
            
            <div class="bank-actions">
              <el-button
                type="primary"
                size="large"
                @click="startPractice"
                v-if="bank.question_count > 0"
              >
                开始练习
              </el-button>
              <el-button
                @click="showUploadDialog = true"
                v-if="canEdit"
              >
                导入题目
              </el-button>
              <el-dropdown 
                @command="handleBankAction"
                v-if="canEdit"
              >
                <el-button :icon="MoreFilled" />
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="rename">重命名</el-dropdown-item>
                    <el-dropdown-item command="edit">编辑题库</el-dropdown-item>
                    <el-dropdown-item command="export">导出题库</el-dropdown-item>
                    <el-dropdown-item command="delete" divided>删除题库</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
          
          <p class="bank-description" v-if="bank.description">
            {{ bank.description }}
          </p>
          
          <div class="bank-tags" v-if="bank.tags?.length">
            <el-tag 
              v-for="tag in bank.tags" 
              :key="tag"
              effect="plain"
            >
              {{ tag }}
            </el-tag>
          </div>
        </div>

        <!-- 学习进度 -->
        <div class="progress-section" v-if="bank?.user_progress && authStore.isAuthenticated">
          <div class="progress-card">
            <h3>学习进度</h3>
            <div class="progress-stats">
              <div class="stat-item">
                <span class="stat-label">已完成</span>
                <span class="stat-value">{{ bank.user_progress.answered_questions }}/{{ bank.user_progress.total_questions }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">正确率</span>
                <span class="stat-value">{{ bank.user_progress.accuracy_rate }}%</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">总分</span>
                <span class="stat-value">{{ bank.user_progress.total_score }}</span>
              </div>
            </div>
            <el-progress 
              :percentage="bank.user_progress.progress_rate" 
              :stroke-width="12"
              class="progress-bar"
            />
          </div>
        </div>

        <!-- 题目列表 -->
        <div class="questions-section">
          <div class="section-header">
            <h3>题目列表</h3>
            <div class="section-actions">
              <el-input
                v-model="searchKeyword"
                placeholder="搜索题目..."
                :prefix-icon="Search"
                clearable
                @input="handleSearch"
                style="width: 200px; margin-right: 12px;"
              />
              
              <el-select
                v-model="selectedType"
                placeholder="题目类型"
                clearable
                @change="handleFilter"
                style="width: 120px; margin-right: 12px;"
              >
                <el-option label="选择题" value="choice" />
                <el-option label="判断题" value="true_false" />
                <el-option label="问答题" value="qa" />
                <el-option label="数学题" value="math" />
                <el-option label="编程题" value="programming" />
              </el-select>
              
              <el-select
                v-model="selectedDifficulty"
                placeholder="难度"
                clearable
                @change="handleFilter"
                style="width: 100px; margin-right: 12px;"
              >
                <el-option label="简单" value="easy" />
                <el-option label="中等" value="medium" />
                <el-option label="困难" value="hard" />
              </el-select>
              
              <el-button 
                type="primary"
                @click="showCreateQuestionDialog = true"
                v-if="canEdit"
              >
                添加题目
              </el-button>
            </div>
          </div>
          
          <div class="questions-list" v-loading="questionsLoading">
            <div
              v-for="(question, index) in questions"
              :key="question.id"
              class="question-item"
              @click="handleQuestionClick(question)"
            >
              <div class="question-header">
                <div class="question-number">
                  <span class="number-badge">{{ index + 1 }}</span>
                </div>

                <div class="question-meta">
                  <el-tag
                    :type="getTypeTagType(question.type)"
                    size="small"
                  >
                    {{ getTypeText(question.type) }}
                  </el-tag>
                  <el-tag
                    :type="getDifficultyType(question.difficulty)"
                    size="small"
                  >
                    {{ getDifficultyText(question.difficulty) }}
                  </el-tag>
                  <span class="points">{{ question.points }} 分</span>
                  <el-tag
                    v-if="!question.explanation"
                    type="warning"
                    size="small"
                  >
                    无解析
                  </el-tag>
                </div>

                <div class="question-actions" v-if="canEdit">
                  <el-button
                    size="small"
                    @click.stop="editQuestion(question)"
                    :icon="Edit"
                  >
                    编辑
                  </el-button>
                  <el-button
                    v-if="!question.explanation"
                    size="small"
                    type="primary"
                    @click.stop="addExplanation(question)"
                    :icon="Plus"
                  >
                    添加解析
                  </el-button>
                  <el-button
                    size="small"
                    type="danger"
                    @click.stop="deleteQuestion(question)"
                    :icon="Delete"
                  >
                    删除
                  </el-button>
                </div>
              </div>
              
              <h4 class="question-title">{{ question.title }}</h4>
              
              <div class="question-preview" v-if="question.type === 'choice'">
                <div class="options-preview">
                  <span 
                    v-for="option in question.content.options?.slice(0, 2)" 
                    :key="option.key"
                    class="option-item"
                  >
                    {{ option.key }}. {{ option.text }}
                  </span>
                  <span v-if="question.content.options?.length > 2" class="more-options">
                    ...
                  </span>
                </div>
              </div>
              
              <div class="question-footer">
                <div class="question-tags" v-if="question.tags?.length">
                  <el-tag 
                    v-for="tag in question.tags.slice(0, 3)" 
                    :key="tag"
                    size="small"
                    effect="plain"
                  >
                    {{ tag }}
                  </el-tag>
                </div>
                
                <div class="question-status" v-if="authStore.isAuthenticated">
                  <el-icon 
                    v-if="question.is_favorited"
                    color="#f56c6c"
                  >
                    <StarFilled />
                  </el-icon>
                  <span 
                    v-if="question.user_answer"
                    :class="['answer-status', question.user_answer.is_correct ? 'correct' : 'incorrect']"
                  >
                    {{ question.user_answer.is_correct ? '已答对' : '已答错' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 空状态 -->
          <div v-if="!questionsLoading && questions.length === 0" class="empty-state">
            <el-icon size="64"><Document /></el-icon>
            <h3>{{ getQuestionsEmptyText() }}</h3>
            <p>{{ getQuestionsEmptyDescription() }}</p>
            <el-button 
              type="primary" 
              @click="showCreateQuestionDialog = true"
              v-if="canEdit"
            >
              添加第一道题目
            </el-button>
          </div>
          
          <!-- 分页 -->
          <div class="pagination" v-if="questionsTotal > 0">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :total="questionsTotal"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange"
              @current-change="handlePageChange"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 文件上传对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="导入题目"
      width="600px"
    >
      <FileUpload @success="handleUploadSuccess" />
    </el-dialog>

    <!-- 创建题目对话框 -->
    <QuestionCreateDialog
      v-model="showCreateQuestionDialog"
      :bank-id="bankId"
      @success="handleQuestionCreateSuccess"
    />

    <!-- 编辑题库对话框 -->
    <BankEditDialog
      v-model="showEditDialog"
      :bank="bank"
      @success="handleBankEditSuccess"
    />

    <!-- 导出题库对话框 -->
    <BankExportDialog
      v-model="showExportDialog"
      :bank="bank"
    />

    <!-- 重命名题库对话框 -->
    <BankRenameDialog
      v-model="showRenameDialog"
      :bank="bank"
      @success="handleBankRenameSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Document, User, MoreFilled, Search, StarFilled, Edit, Plus, Delete
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useBanksStore } from '@/stores/banks'
import { questionsApi } from '@/api/questions'
import FileUpload from '@/components/FileUpload.vue'
import QuestionCreateDialog from '@/components/QuestionCreateDialog.vue'
import BankEditDialog from '@/components/banks/BankEditDialog.vue'
import BankExportDialog from '@/components/banks/BankExportDialog.vue'
import BankRenameDialog from '@/components/banks/BankRenameDialog.vue'
import type { QuestionBank } from '@/types/banks'
import type { Question } from '@/types/questions'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const banksStore = useBanksStore()

const bankId = computed(() => Number(route.params.id))
const bank = ref<QuestionBank | null>(null)
const questions = ref<Question[]>([])
const questionsLoading = ref(false)
const questionsTotal = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 搜索和筛选
const searchKeyword = ref('')
const selectedType = ref('')
const selectedDifficulty = ref('')

// 对话框状态
const showUploadDialog = ref(false)
const showCreateQuestionDialog = ref(false)
const showEditDialog = ref(false)
const showExportDialog = ref(false)
const showRenameDialog = ref(false)

const canEdit = computed(() => {
  return authStore.isAuthenticated && bank.value && 
         (authStore.user?.id === bank.value.creator_id || authStore.isAdmin)
})

const getDifficultyType = (difficulty: string) => {
  const types = { easy: 'success', medium: 'warning', hard: 'danger' }
  return types[difficulty as keyof typeof types] || 'info'
}

const getDifficultyText = (difficulty: string) => {
  const texts = { easy: '简单', medium: '中等', hard: '困难' }
  return texts[difficulty as keyof typeof texts] || difficulty
}

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

const getQuestionsEmptyText = () => {
  if (searchKeyword.value || selectedType.value || selectedDifficulty.value) {
    return '没有找到匹配的题目'
  }
  return '暂无题目'
}

const getQuestionsEmptyDescription = () => {
  if (searchKeyword.value || selectedType.value || selectedDifficulty.value) {
    return '尝试调整搜索条件'
  }
  return canEdit.value ? '添加一些题目开始使用' : '等待题目添加'
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

const fetchQuestions = async () => {
  questionsLoading.value = true
  try {
    const response = await questionsApi.getQuestions({
      bank_id: bankId.value,
      page: currentPage.value,
      per_page: pageSize.value,
      type: selectedType.value || undefined,
      difficulty: selectedDifficulty.value || undefined
    })

    questions.value = response.data.data
    questionsTotal.value = response.data.total
  } catch (error) {
    console.error('获取题目列表失败:', error)
  } finally {
    questionsLoading.value = false
  }
}

const startPractice = () => {
  if (authStore.isAuthenticated) {
    router.push(`/practice/${bankId.value}`)
  } else {
    router.push(`/login?redirect=/practice/${bankId.value}`)
  }
}

const handleBankAction = async (command: string) => {
  switch (command) {
    case 'rename':
      showRenameDialog.value = true
      break
    case 'edit':
      showEditDialog.value = true
      break
    case 'export':
      showExportDialog.value = true
      break
    case 'delete':
      try {
        await ElMessageBox.confirm(
          '确定要删除这个题库吗？此操作不可恢复。',
          '确认删除',
          { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
        )
        
        await banksStore.deleteBank(bankId.value)
        ElMessage.success('题库删除成功')
        router.push('/banks')
      } catch (error: any) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败')
        }
      }
      break
  }
}

const handleQuestionClick = (question: Question) => {
  router.push(`/banks/${bankId.value}/questions/${question.id}`)
}

const editQuestion = (question: Question) => {
  // 跳转到题目编辑页面
  router.push(`/banks/${bankId.value}/questions/${question.id}/edit`)
}

const addExplanation = async (question: Question) => {
  try {
    const { value: explanation } = await ElMessageBox.prompt(
      '请输入题目解析：',
      '添加解析',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputType: 'textarea',
        inputPlaceholder: '请输入详细的题目解析...'
      }
    )

    if (explanation && explanation.trim()) {
      // 调用API更新题目解析
      await questionsApi.updateQuestion(question.id, {
        explanation: explanation.trim()
      })

      ElMessage.success('解析添加成功')
      fetchQuestions() // 刷新题目列表
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('添加解析失败')
    }
  }
}

const deleteQuestion = async (question: Question) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这道题目吗？',
      '确认删除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    
    await questionsApi.deleteQuestion(question.id)
    ElMessage.success('题目删除成功')
    fetchQuestions()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchQuestions()
}

const handleFilter = () => {
  currentPage.value = 1
  fetchQuestions()
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchQuestions()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  fetchQuestions()
}

const handleUploadSuccess = () => {
  showUploadDialog.value = false
  fetchQuestions()
  fetchBankDetail() // 刷新题库信息
}

const handleQuestionCreateSuccess = () => {
  showCreateQuestionDialog.value = false
  fetchQuestions()
  fetchBankDetail()
}

const handleBankEditSuccess = () => {
  showEditDialog.value = false
  fetchBankDetail() // 重新获取题库信息
}

const handleBankRenameSuccess = () => {
  showRenameDialog.value = false
  fetchBankDetail() // 重新获取题库信息
}

onMounted(() => {
  fetchBankDetail()
  fetchQuestions()
})
</script>

<style scoped>
.bank-detail-page {
  min-height: 100vh;
  background-color: var(--background-base);
}

.bank-header {
  background: white;
  border-radius: 12px;
  padding: 32px;
  margin-bottom: 24px;
  box-shadow: var(--shadow-base);
}

.bank-info {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.bank-title h1 {
  margin: 0 0 12px 0;
  font-size: 28px;
  color: var(--text-primary);
}

.bank-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.question-count,
.creator {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: var(--text-secondary);
}

.bank-actions {
  display: flex;
  gap: 12px;
}

.bank-description {
  color: var(--text-regular);
  line-height: 1.6;
  margin-bottom: 16px;
}

.bank-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.progress-section {
  margin-bottom: 24px;
}

.progress-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: var(--shadow-base);
}

.progress-card h3 {
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

.stat-label {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.stat-value {
  display: block;
  font-size: 18px;
  font-weight: bold;
  color: var(--text-primary);
}

.progress-bar {
  margin-top: 16px;
}

.questions-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: var(--shadow-base);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

.section-header h3 {
  margin: 0;
  color: var(--text-primary);
}

.section-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.questions-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.question-item {
  border: 1px solid var(--border-light);
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s;
}

.question-item:hover {
  border-color: var(--primary-color);
  box-shadow: var(--shadow-base);
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  gap: 16px;
}

.question-number {
  flex-shrink: 0;
}

.number-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: var(--el-color-primary);
  color: white;
  border-radius: 50%;
  font-weight: 600;
  font-size: 14px;
}

.question-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.points {
  font-size: 12px;
  color: var(--text-secondary);
}

.question-actions {
  display: flex;
  gap: 8px;
}

.question-title {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: var(--text-primary);
  line-height: 1.5;
}

.question-preview {
  margin-bottom: 12px;
}

.options-preview {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: var(--text-regular);
}

.option-item {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

.more-options {
  color: var(--text-secondary);
}

.question-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.question-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.question-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.answer-status {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 4px;
}

.answer-status.correct {
  background: #f0f9ff;
  color: #1890ff;
}

.answer-status.incorrect {
  background: #fff2f0;
  color: #ff4d4f;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary);
}

.empty-state .el-icon {
  color: var(--text-placeholder);
  margin-bottom: 16px;
}

.empty-state h3 {
  margin-bottom: 8px;
  color: var(--text-primary);
}

.empty-state p {
  margin-bottom: 20px;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

@media (max-width: 768px) {
  .bank-info {
    flex-direction: column;
    gap: 16px;
  }
  
  .bank-actions {
    align-self: stretch;
  }
  
  .progress-stats {
    flex-direction: column;
    gap: 16px;
  }
  
  .section-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .section-actions {
    flex-direction: column;
  }
  
  .question-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .question-footer {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .options-preview {
    flex-direction: column;
    gap: 8px;
  }
}
</style>
