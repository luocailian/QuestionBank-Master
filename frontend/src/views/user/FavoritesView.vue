<template>
  <div class="favorites-page">
    <div class="page-container">
      <div class="container">
        <div class="page-header">
          <h2>我的收藏</h2>
          <p>查看你收藏的题目</p>
        </div>

        <div class="favorites-content">
          <!-- 筛选器 -->
          <div class="filters">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索题目..."
              :prefix-icon="Search"
              clearable
              @input="handleSearch"
            />
            
            <el-select
              v-model="selectedType"
              placeholder="题目类型"
              clearable
              @change="handleFilter"
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
            >
              <el-option label="简单" value="easy" />
              <el-option label="中等" value="medium" />
              <el-option label="困难" value="hard" />
            </el-select>
          </div>

          <!-- 题目列表 -->
          <div class="questions-list" v-loading="loading">
            <div 
              v-for="question in filteredQuestions" 
              :key="question.id"
              class="question-card"
              @click="handleQuestionClick(question)"
            >
              <div class="question-header">
                <div class="question-meta">
                  <el-tag 
                    :type="getTypeTagType(question.type)" 
                    size="small"
                    class="question-type-tag"
                  >
                    {{ getTypeText(question.type) }}
                  </el-tag>
                  
                  <el-tag 
                    :type="getDifficultyTagType(question.difficulty)"
                    size="small"
                  >
                    {{ getDifficultyText(question.difficulty) }}
                  </el-tag>
                  
                  <span class="points">{{ question.points }} 分</span>
                </div>
                
                <el-button
                  type="danger"
                  size="small"
                  :icon="Delete"
                  @click.stop="handleUnfavorite(question)"
                >
                  取消收藏
                </el-button>
              </div>
              
              <h3 class="question-title">{{ question.title }}</h3>
              
              <div class="question-content" v-if="question.type === 'choice'">
                <div class="options">
                  <div 
                    v-for="option in question.content.options?.slice(0, 2)" 
                    :key="option.key"
                    class="option-preview"
                  >
                    {{ option.key }}. {{ option.text }}
                  </div>
                  <div v-if="question.content.options?.length > 2" class="more-options">
                    ...还有 {{ question.content.options.length - 2 }} 个选项
                  </div>
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
                  <span v-if="question.tags.length > 3" class="more-tags">
                    +{{ question.tags.length - 3 }}
                  </span>
                </div>
                
                <div class="question-actions">
                  <el-button 
                    size="small" 
                    @click.stop="$router.push(`/practice/${question.bank_id}?question=${question.id}`)"
                  >
                    开始答题
                  </el-button>
                </div>
              </div>
            </div>
          </div>

          <!-- 空状态 -->
          <div v-if="!loading && questions.length === 0" class="empty-state">
            <el-icon size="64"><Star /></el-icon>
            <h3>还没有收藏的题目</h3>
            <p>去题库中收藏一些有趣的题目吧</p>
            <el-button type="primary" @click="$router.push('/banks')">
              浏览题库
            </el-button>
          </div>

          <!-- 无搜索结果 -->
          <div v-if="!loading && questions.length > 0 && filteredQuestions.length === 0" class="empty-state">
            <el-icon size="64"><Search /></el-icon>
            <h3>没有找到匹配的题目</h3>
            <p>尝试调整搜索条件</p>
            <el-button @click="clearFilters">清除筛选</el-button>
          </div>

          <!-- 分页 -->
          <div class="pagination" v-if="total > 0">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :total="total"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange"
              @current-change="handlePageChange"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Star, Delete } from '@element-plus/icons-vue'
import { questionsApi } from '@/api/questions'
import type { Question } from '@/types/questions'

const router = useRouter()

const questions = ref<Question[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 筛选条件
const searchKeyword = ref('')
const selectedType = ref('')
const selectedDifficulty = ref('')

// 计算属性：过滤后的题目
const filteredQuestions = computed(() => {
  let filtered = questions.value

  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(q => 
      q.title.toLowerCase().includes(keyword) ||
      q.tags?.some(tag => tag.toLowerCase().includes(keyword))
    )
  }

  if (selectedType.value) {
    filtered = filtered.filter(q => q.type === selectedType.value)
  }

  if (selectedDifficulty.value) {
    filtered = filtered.filter(q => q.difficulty === selectedDifficulty.value)
  }

  return filtered
})

const getTypeText = (type: string) => {
  const typeMap = {
    choice: '选择题',
    true_false: '判断题',
    qa: '问答题',
    math: '数学题',
    programming: '编程题'
  }
  return typeMap[type as keyof typeof typeMap] || type
}

const getTypeTagType = (type: string) => {
  const typeMap = {
    choice: 'success',
    true_false: 'warning',
    qa: 'info',
    math: 'danger',
    programming: ''
  }
  return typeMap[type as keyof typeof typeMap] || ''
}

const getDifficultyText = (difficulty: string) => {
  const difficultyMap = {
    easy: '简单',
    medium: '中等',
    hard: '困难'
  }
  return difficultyMap[difficulty as keyof typeof difficultyMap] || difficulty
}

const getDifficultyTagType = (difficulty: string) => {
  const difficultyMap = {
    easy: 'success',
    medium: 'warning',
    hard: 'danger'
  }
  return difficultyMap[difficulty as keyof typeof difficultyMap] || ''
}

const fetchFavorites = async () => {
  loading.value = true
  try {
    const response = await questionsApi.getFavoriteQuestions({
      page: currentPage.value,
      per_page: pageSize.value
    })
    questions.value = response.data.data
    total.value = response.data.total
  } catch (error) {
    console.error('获取收藏题目失败:', error)
    ElMessage.error('获取收藏题目失败')
  } finally {
    loading.value = false
  }
}

const handleQuestionClick = (question: Question) => {
  router.push(`/banks/${question.bank_id}/questions/${question.id}`)
}

const handleUnfavorite = async (question: Question) => {
  try {
    await ElMessageBox.confirm(
      '确定要取消收藏这道题目吗？',
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await questionsApi.unfavoriteQuestion(question.id)
    
    // 从列表中移除
    questions.value = questions.value.filter(q => q.id !== question.id)
    total.value--
    
    ElMessage.success('已取消收藏')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('取消收藏失败')
    }
  }
}

const handleSearch = () => {
  // 搜索是通过计算属性实现的，这里可以添加防抖逻辑
}

const handleFilter = () => {
  // 筛选是通过计算属性实现的
}

const clearFilters = () => {
  searchKeyword.value = ''
  selectedType.value = ''
  selectedDifficulty.value = ''
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchFavorites()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  fetchFavorites()
}

onMounted(() => {
  fetchFavorites()
})
</script>

<style scoped>
.favorites-page {
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

.favorites-content {
  max-width: 1000px;
  margin: 0 auto;
}

.filters {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: var(--shadow-base);
}

.filters .el-input {
  flex: 1;
}

.questions-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.question-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: var(--shadow-base);
  cursor: pointer;
  transition: all 0.3s;
}

.question-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-light);
}

.question-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
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

.question-title {
  font-size: 16px;
  color: var(--text-primary);
  margin-bottom: 12px;
  line-height: 1.5;
}

.question-content {
  margin-bottom: 16px;
}

.options {
  font-size: 14px;
  color: var(--text-regular);
}

.option-preview {
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.more-options {
  color: var(--text-secondary);
  font-style: italic;
}

.question-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.question-tags {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.more-tags {
  font-size: 12px;
  color: var(--text-secondary);
}

.question-actions {
  display: flex;
  gap: 8px;
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
  margin-top: 32px;
}

@media (max-width: 768px) {
  .filters {
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
  
  .question-tags {
    flex-wrap: wrap;
  }
}
</style>
