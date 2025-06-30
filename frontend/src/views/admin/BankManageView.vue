<template>
  <div class="bank-manage">
    <!-- 操作栏 -->
    <div class="manage-header">
      <div class="search-filters">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索题库..."
          :prefix-icon="Search"
          clearable
          @input="handleSearch"
          style="width: 250px; margin-right: 12px;"
        />
        
        <el-select
          v-model="selectedCategory"
          placeholder="题库分类"
          clearable
          @change="handleFilter"
          style="width: 120px; margin-right: 12px;"
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
          placeholder="难度"
          clearable
          @change="handleFilter"
          style="width: 100px; margin-right: 12px;"
        >
          <el-option label="简单" value="easy" />
          <el-option label="中等" value="medium" />
          <el-option label="困难" value="hard" />
        </el-select>
        
        <el-select
          v-model="selectedStatus"
          placeholder="状态"
          clearable
          @change="handleFilter"
          style="width: 100px;"
        >
          <el-option label="公开" value="public" />
          <el-option label="私有" value="private" />
        </el-select>
      </div>
      
      <div class="header-actions">
        <el-button type="primary" @click="showCreateDialog = true">
          创建题库
        </el-button>
        <el-button @click="exportBanks">
          导出数据
        </el-button>
      </div>
    </div>

    <!-- 题库表格 -->
    <div class="table-container">
      <el-table
        :data="banks"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="80" />
        
        <el-table-column label="题库信息" min-width="250">
          <template #default="{ row }">
            <div class="bank-info">
              <div class="bank-title">{{ row.name }}</div>
              <div class="bank-description">{{ row.description || '暂无描述' }}</div>
              <div class="bank-tags" v-if="row.tags?.length">
                <el-tag 
                  v-for="tag in row.tags.slice(0, 3)" 
                  :key="tag"
                  size="small"
                  effect="plain"
                >
                  {{ tag }}
                </el-tag>
                <span v-if="row.tags.length > 3" class="more-tags">
                  +{{ row.tags.length - 3 }}
                </span>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="分类" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.category" type="info" size="small">
              {{ row.category }}
            </el-tag>
            <span v-else class="text-placeholder">-</span>
          </template>
        </el-table-column>
        
        <el-table-column label="难度" width="80">
          <template #default="{ row }">
            <el-tag :type="getDifficultyType(row.difficulty)" size="small">
              {{ getDifficultyText(row.difficulty) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="题目数" width="80">
          <template #default="{ row }">
            <span class="question-count">{{ row.question_count }}</span>
          </template>
        </el-table-column>
        
        <el-table-column label="创建者" width="120">
          <template #default="{ row }">
            <span>{{ row.creator_name }}</span>
          </template>
        </el-table-column>
        
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_public ? 'success' : 'warning'" size="small">
              {{ row.is_public ? '公开' : '私有' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewBank(row)">
              查看
            </el-button>
            <el-button size="small" @click="editBank(row)">
              编辑
            </el-button>
            <el-button 
              size="small" 
              type="danger"
              @click="deleteBank(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 创建题库对话框 -->
    <BankCreateDialog 
      v-model="showCreateDialog"
      @success="handleCreateSuccess"
    />

    <!-- 题库详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      title="题库详情"
      width="800px"
    >
      <div v-if="selectedBank" class="bank-detail">
        <div class="detail-section">
          <h4>基本信息</h4>
          <div class="detail-grid">
            <div class="detail-item">
              <span class="label">题库名称：</span>
              <span class="value">{{ selectedBank.name }}</span>
            </div>
            <div class="detail-item">
              <span class="label">分类：</span>
              <span class="value">{{ selectedBank.category || '未分类' }}</span>
            </div>
            <div class="detail-item">
              <span class="label">难度：</span>
              <span class="value">{{ getDifficultyText(selectedBank.difficulty) }}</span>
            </div>
            <div class="detail-item">
              <span class="label">状态：</span>
              <span class="value">{{ selectedBank.is_public ? '公开' : '私有' }}</span>
            </div>
            <div class="detail-item">
              <span class="label">创建者：</span>
              <span class="value">{{ selectedBank.creator_name }}</span>
            </div>
            <div class="detail-item">
              <span class="label">题目数量：</span>
              <span class="value">{{ selectedBank.question_count }}</span>
            </div>
          </div>
          
          <div class="detail-item full-width" v-if="selectedBank.description">
            <span class="label">描述：</span>
            <span class="value">{{ selectedBank.description }}</span>
          </div>
          
          <div class="detail-item full-width" v-if="selectedBank.tags?.length">
            <span class="label">标签：</span>
            <div class="tags-container">
              <el-tag 
                v-for="tag in selectedBank.tags" 
                :key="tag"
                effect="plain"
              >
                {{ tag }}
              </el-tag>
            </div>
          </div>
        </div>
        
        <div class="detail-section">
          <h4>统计信息</h4>
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-number">{{ bankStats.total_attempts }}</div>
              <div class="stat-label">总答题次数</div>
            </div>
            <div class="stat-item">
              <div class="stat-number">{{ bankStats.unique_users }}</div>
              <div class="stat-label">参与用户</div>
            </div>
            <div class="stat-item">
              <div class="stat-number">{{ bankStats.accuracy_rate }}%</div>
              <div class="stat-label">平均正确率</div>
            </div>
            <div class="stat-item">
              <div class="stat-number">{{ bankStats.avg_score }}</div>
              <div class="stat-label">平均分数</div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { useBanksStore } from '@/stores/banks'
import BankCreateDialog from '@/components/BankCreateDialog.vue'
import type { QuestionBank } from '@/types/banks'
import dayjs from 'dayjs'

const router = useRouter()
const banksStore = useBanksStore()

const loading = ref(false)
const banks = ref<QuestionBank[]>([])
const categories = ref<string[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 搜索和筛选
const searchKeyword = ref('')
const selectedCategory = ref('')
const selectedDifficulty = ref('')
const selectedStatus = ref('')

// 对话框状态
const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const selectedBank = ref<QuestionBank | null>(null)
const bankStats = ref({
  total_attempts: 0,
  unique_users: 0,
  accuracy_rate: 0,
  avg_score: 0
})

const getDifficultyType = (difficulty: string) => {
  const types = { easy: 'success', medium: 'warning', hard: 'danger' }
  return types[difficulty as keyof typeof types] || 'info'
}

const getDifficultyText = (difficulty: string) => {
  const texts = { easy: '简单', medium: '中等', hard: '困难' }
  return texts[difficulty as keyof typeof texts] || difficulty
}

const formatDate = (dateString: string) => {
  return dayjs(dateString).format('YYYY-MM-DD HH:mm')
}

const fetchBanks = async () => {
  loading.value = true
  try {
    const response = await banksStore.fetchBanks({
      page: currentPage.value,
      per_page: pageSize.value,
      search: searchKeyword.value || undefined,
      category: selectedCategory.value || undefined,
      difficulty: selectedDifficulty.value || undefined
    })
    
    banks.value = response.data
    total.value = response.data.length // 临时处理
  } catch (error) {
    console.error('获取题库列表失败:', error)
    ElMessage.error('获取题库列表失败')
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

const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchBanks()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  fetchBanks()
}

const viewBank = async (bank: QuestionBank) => {
  selectedBank.value = bank
  
  // 获取题库统计信息
  try {
    const stats = await banksStore.fetchBankStatistics(bank.id)
    bankStats.value = {
      total_attempts: stats.total_attempts || 0,
      unique_users: stats.unique_users || 0,
      accuracy_rate: stats.accuracy_rate || 0,
      avg_score: stats.avg_score || 0
    }
  } catch (error) {
    console.error('获取题库统计失败:', error)
    bankStats.value = {
      total_attempts: 0,
      unique_users: 0,
      accuracy_rate: 0,
      avg_score: 0
    }
  }
  
  showDetailDialog.value = true
}

const editBank = (bank: QuestionBank) => {
  router.push(`/banks/${bank.id}`)
}

const deleteBank = async (bank: QuestionBank) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除题库"${bank.name}"吗？此操作不可恢复。`,
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
}

const handleCreateSuccess = () => {
  showCreateDialog.value = false
  fetchBanks()
}

const exportBanks = () => {
  ElMessage.info('导出功能开发中...')
}

onMounted(() => {
  fetchBanks()
  fetchCategories()
})
</script>

<style scoped>
.bank-manage {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: var(--shadow-base);
}

.manage-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

.search-filters {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.table-container {
  margin-bottom: 24px;
}

.bank-info {
  max-width: 250px;
}

.bank-title {
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4px;
  line-height: 1.4;
}

.bank-description {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.bank-tags {
  display: flex;
  gap: 4px;
  align-items: center;
  flex-wrap: wrap;
}

.more-tags {
  font-size: 12px;
  color: var(--text-secondary);
}

.question-count {
  font-weight: 500;
  color: var(--primary-color);
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

.bank-detail {
  max-height: 600px;
  overflow-y: auto;
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section h4 {
  margin: 0 0 16px 0;
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-lighter);
  padding-bottom: 8px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.detail-item {
  display: flex;
  align-items: flex-start;
}

.detail-item.full-width {
  grid-column: 1 / -1;
  margin-bottom: 12px;
}

.detail-item .label {
  font-weight: 500;
  color: var(--text-secondary);
  margin-right: 8px;
  min-width: 80px;
  flex-shrink: 0;
}

.detail-item .value {
  color: var(--text-primary);
  line-height: 1.5;
}

.tags-container {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background: var(--background-base);
  border-radius: 8px;
}

.stat-number {
  font-size: 20px;
  font-weight: bold;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
}

@media (max-width: 768px) {
  .manage-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-filters {
    flex-direction: column;
  }
  
  .detail-grid {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
