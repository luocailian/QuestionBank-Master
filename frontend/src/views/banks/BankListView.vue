<template>
  <div class="banks-page">
    <div class="page-container">
      <div class="container">
        <div class="page-header">
          <h2>题库浏览</h2>
          <p>发现有趣的题库，开始学习之旅</p>
        </div>

        <!-- 搜索和筛选 -->
        <div class="search-filters">
          <div class="search-bar">
            <el-input
              v-model="searchQuery"
              placeholder="搜索题库..."
              :prefix-icon="Search"
              size="large"
              clearable
              @input="handleSearch"
            />
          </div>
          
          <div class="filters">
            <el-select
              v-model="selectedCategory"
              placeholder="选择分类"
              clearable
              @change="handleFilter"
            >
              <el-option
                v-for="category in categories"
                :key="category"
                :label="category"
                :value="category"
              />
            </el-select>
            
            <el-select
              v-model="selectedDifficulty"
              placeholder="选择难度"
              clearable
              @change="handleFilter"
            >
              <el-option label="简单" value="easy" />
              <el-option label="中等" value="medium" />
              <el-option label="困难" value="hard" />
            </el-select>
            
            <el-button-group>
              <el-button
                :type="showMyBanks ? 'primary' : ''"
                @click="toggleMyBanks"
                v-if="authStore.isAuthenticated"
              >
                我的题库
              </el-button>
              <el-button
                :icon="Refresh"
                @click="refreshBanks"
                :loading="loading"
              >
                刷新
              </el-button>
              <el-button
                type="primary"
                @click="showCreateDialog = true"
                v-if="authStore.isAuthenticated"
              >
                创建题库
              </el-button>
            </el-button-group>
          </div>
        </div>

        <!-- 题库列表 -->
        <div class="banks-grid" v-loading="loading">
          <div 
            v-for="bank in banks" 
            :key="bank.id"
            class="bank-card"
            @click="$router.push(`/banks/${bank.id}`)"
          >
            <div class="bank-header">
              <div class="bank-title">
                <h3>{{ bank.name }}</h3>
                <div class="bank-meta">
                  <el-tag 
                    v-if="bank.category" 
                    size="small"
                    type="info"
                  >
                    {{ bank.category }}
                  </el-tag>
                  <el-tag 
                    :type="getDifficultyType(bank.difficulty)"
                    size="small"
                  >
                    {{ getDifficultyText(bank.difficulty) }}
                  </el-tag>
                </div>
              </div>
              
              <div class="bank-actions" v-if="authStore.isAuthenticated">
                <el-dropdown 
                  @command="(command) => handleBankAction(command, bank)"
                  v-if="canEditBank(bank)"
                >
                  <el-button size="small" :icon="MoreFilled" circle />
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
            
            <p class="bank-description">{{ bank.description || '暂无描述' }}</p>
            
            <div class="bank-tags" v-if="bank.tags?.length">
              <el-tag 
                v-for="tag in bank.tags.slice(0, 3)" 
                :key="tag"
                size="small"
                effect="plain"
              >
                {{ tag }}
              </el-tag>
              <span v-if="bank.tags.length > 3" class="more-tags">
                +{{ bank.tags.length - 3 }}
              </span>
            </div>
            
            <div class="bank-stats">
              <div class="stat-item">
                <el-icon><Document /></el-icon>
                <span>{{ bank.question_count }} 题</span>
              </div>
              <div class="stat-item">
                <el-icon><User /></el-icon>
                <span>{{ bank.creator_name }}</span>
              </div>
              <div class="stat-item" v-if="bank.user_progress">
                <el-icon><TrendCharts /></el-icon>
                <span>{{ bank.user_progress.progress_rate }}% 完成</span>
              </div>
            </div>
            
            <div class="bank-footer">
              <el-button 
                type="primary" 
                size="small"
                @click.stop="startPractice(bank)"
              >
                开始练习
              </el-button>
              <span class="update-time">
                {{ formatDate(bank.updated_at) }}
              </span>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="!loading && banks.length === 0" class="empty-state">
          <el-icon size="64"><Document /></el-icon>
          <h3>{{ getEmptyStateText() }}</h3>
          <p>{{ getEmptyStateDescription() }}</p>
          <el-button 
            type="primary" 
            @click="handleEmptyAction"
            v-if="authStore.isAuthenticated"
          >
            {{ getEmptyActionText() }}
          </el-button>
        </div>

        <!-- 分页 -->
        <div class="pagination" v-if="total > 0">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :total="total"
            :page-sizes="[12, 24, 48]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handlePageChange"
          />
        </div>
      </div>
    </div>

    <!-- 创建题库对话框 -->
    <BankCreateDialog
      v-model="showCreateDialog"
      @success="handleCreateSuccess"
    />

    <!-- 编辑题库对话框 -->
    <BankEditDialog
      v-model="showEditDialog"
      :bank="selectedBank"
      @success="handleEditSuccess"
    />

    <!-- 导出题库对话框 -->
    <BankExportDialog
      v-model="showExportDialog"
      :bank="selectedBank"
    />

    <!-- 重命名题库对话框 -->
    <BankRenameDialog
      v-model="showRenameDialog"
      :bank="selectedBank"
      @success="handleRenameSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Document, User, TrendCharts, MoreFilled, Refresh } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useBanksStore } from '@/stores/banks'
import BankCreateDialog from '@/components/BankCreateDialog.vue'
import BankEditDialog from '@/components/banks/BankEditDialog.vue'
import BankExportDialog from '@/components/banks/BankExportDialog.vue'
import BankRenameDialog from '@/components/banks/BankRenameDialog.vue'
import type { QuestionBank } from '@/types/banks'
import dayjs from 'dayjs'

const router = useRouter()
const authStore = useAuthStore()
const banksStore = useBanksStore()

const loading = ref(false)
const banks = ref<QuestionBank[]>([])
const categories = ref<string[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(12)

// 搜索和筛选
const searchQuery = ref('')
const selectedCategory = ref('')
const selectedDifficulty = ref('')
const showMyBanks = ref(false)
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const showExportDialog = ref(false)
const showRenameDialog = ref(false)
const selectedBank = ref<QuestionBank | null>(null)

const canEditBank = (bank: QuestionBank) => {
  return authStore.isAuthenticated && 
         (authStore.user?.id === bank.creator_id || authStore.isAdmin)
}

const getDifficultyType = (difficulty: string) => {
  const types = {
    easy: 'success',
    medium: 'warning',
    hard: 'danger'
  }
  return types[difficulty as keyof typeof types] || 'info'
}

const getDifficultyText = (difficulty: string) => {
  const texts = {
    easy: '简单',
    medium: '中等',
    hard: '困难'
  }
  return texts[difficulty as keyof typeof texts] || difficulty
}

const formatDate = (dateString: string) => {
  return dayjs(dateString).format('YYYY-MM-DD')
}

const getEmptyStateText = () => {
  if (showMyBanks.value) return '还没有创建题库'
  if (searchQuery.value) return '没有找到匹配的题库'
  return '暂无题库'
}

const getEmptyStateDescription = () => {
  if (showMyBanks.value) return '创建你的第一个题库吧'
  if (searchQuery.value) return '尝试调整搜索条件'
  return '等待更多题库上线'
}

const getEmptyActionText = () => {
  if (showMyBanks.value) return '创建题库'
  return '清除筛选'
}

const fetchBanks = async () => {
  loading.value = true
  try {
    const response = await banksStore.fetchBanks({
      page: currentPage.value,
      per_page: pageSize.value,
      search: searchQuery.value || undefined,
      category: selectedCategory.value || undefined,
      difficulty: selectedDifficulty.value || undefined,
      my_banks: showMyBanks.value
    })

    // 修复：正确处理后端返回的数据格式
    banks.value = response.data.banks || response.data
    total.value = response.data.pagination?.total || banks.value.length
  } catch (error) {
    console.error('获取题库列表失败:', error)
  } finally {
    loading.value = false
  }
}

const fetchCategories = async () => {
  try {
    await banksStore.fetchCategories()
    categories.value = banksStore.categories
  } catch (error) {
    console.error('获取分类失败:', error)
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchBanks()
}

const handleFilter = () => {
  currentPage.value = 1
  fetchBanks()
}

const toggleMyBanks = () => {
  showMyBanks.value = !showMyBanks.value
  currentPage.value = 1
  fetchBanks()
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchBanks()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  fetchBanks()
}

const startPractice = (bank: QuestionBank) => {
  if (authStore.isAuthenticated) {
    router.push(`/practice/${bank.id}`)
  } else {
    router.push(`/login?redirect=/practice/${bank.id}`)
  }
}

const handleBankAction = async (command: string, bank: QuestionBank) => {
  selectedBank.value = bank

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
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        await banksStore.deleteBank(bank.id)
        ElMessage.success('题库删除成功')
        fetchBanks()
      } catch (error: any) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败')
        }
      }
      break
  }
}

const handleCreateSuccess = () => {
  showCreateDialog.value = false
  fetchBanks()
}

const handleEditSuccess = () => {
  showEditDialog.value = false
  selectedBank.value = null
  fetchBanks()
}

const handleRenameSuccess = () => {
  showRenameDialog.value = false
  selectedBank.value = null
  fetchBanks()
}

const refreshBanks = async () => {
  await fetchBanks()
  ElMessage.success('题库列表已刷新')
}

const handleEmptyAction = () => {
  if (showMyBanks.value) {
    showCreateDialog.value = true
  } else {
    // 清除筛选
    searchQuery.value = ''
    selectedCategory.value = ''
    selectedDifficulty.value = ''
    showMyBanks.value = false
    fetchBanks()
  }
}

onMounted(() => {
  fetchBanks()
  fetchCategories()
})
</script>

<style scoped>
.banks-page {
  min-height: 100vh;
  background-color: var(--background-base);
}

.page-header {
  text-align: center;
  margin-bottom: 32px;
}

.page-header h2 {
  font-size: 28px;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.page-header p {
  color: var(--text-secondary);
}

.search-filters {
  background: white;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: var(--shadow-base);
}

.search-bar {
  margin-bottom: 16px;
}

.filters {
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
}

.banks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.bank-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: var(--shadow-base);
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  flex-direction: column;
}

.bank-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-light);
}

.bank-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.bank-title h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: var(--text-primary);
  line-height: 1.4;
}

.bank-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.bank-description {
  color: var(--text-regular);
  line-height: 1.5;
  margin-bottom: 16px;
  flex: 1;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.bank-tags {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.more-tags {
  font-size: 12px;
  color: var(--text-secondary);
}

.bank-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  font-size: 14px;
  color: var(--text-secondary);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.bank-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: auto;
}

.update-time {
  font-size: 12px;
  color: var(--text-placeholder);
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
}

@media (max-width: 768px) {
  .banks-grid {
    grid-template-columns: 1fr;
  }
  
  .filters {
    flex-direction: column;
    align-items: stretch;
  }
  
  .bank-header {
    flex-direction: column;
    gap: 12px;
  }
  
  .bank-stats {
    flex-direction: column;
    gap: 8px;
  }
  
  .bank-footer {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
}
</style>
