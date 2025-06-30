<template>
  <div class="user-manage">
    <!-- 操作栏 -->
    <div class="manage-header">
      <div class="search-filters">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索用户..."
          :prefix-icon="Search"
          clearable
          @input="handleSearch"
          style="width: 250px; margin-right: 12px;"
        />
        
        <el-select
          v-model="selectedRole"
          placeholder="用户角色"
          clearable
          @change="handleFilter"
          style="width: 120px; margin-right: 12px;"
        >
          <el-option label="管理员" value="admin" />
          <el-option label="普通用户" value="user" />
        </el-select>
        
        <el-select
          v-model="selectedStatus"
          placeholder="账户状态"
          clearable
          @change="handleFilter"
          style="width: 120px;"
        >
          <el-option label="正常" value="active" />
          <el-option label="禁用" value="inactive" />
        </el-select>
      </div>
      
      <div class="header-actions">
        <el-button type="primary" @click="showCreateDialog = true">
          添加用户
        </el-button>
        <el-button @click="exportUsers">
          导出数据
        </el-button>
      </div>
    </div>

    <!-- 用户表格 -->
    <div class="table-container">
      <el-table
        :data="users"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="80" />
        
        <el-table-column label="用户信息" min-width="200">
          <template #default="{ row }">
            <div class="user-info">
              <el-avatar :src="row.avatar_url" :size="40">
                {{ row.username?.charAt(0).toUpperCase() }}
              </el-avatar>
              <div class="user-details">
                <div class="username">{{ row.username }}</div>
                <div class="email">{{ row.email }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'primary'">
              {{ row.role === 'admin' ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="注册时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="最后登录" width="180">
          <template #default="{ row }">
            {{ row.last_login ? formatDate(row.last_login) : '从未登录' }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewUser(row)">
              查看
            </el-button>
            <el-button size="small" @click="editUser(row)">
              编辑
            </el-button>
            <el-button 
              size="small" 
              :type="row.is_active ? 'warning' : 'success'"
              @click="toggleUserStatus(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
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

    <!-- 创建用户对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="添加用户"
      width="500px"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="createForm.username" />
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="createForm.email" />
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <el-input v-model="createForm.password" type="password" />
        </el-form-item>
        
        <el-form-item label="角色" prop="role">
          <el-select v-model="createForm.role" style="width: 100%">
            <el-option label="普通用户" value="user" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" :loading="createLoading" @click="handleCreateUser">
            创建
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 用户详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      title="用户详情"
      width="600px"
    >
      <div v-if="selectedUser" class="user-detail">
        <div class="detail-section">
          <h4>基本信息</h4>
          <div class="detail-grid">
            <div class="detail-item">
              <span class="label">用户名：</span>
              <span class="value">{{ selectedUser.username }}</span>
            </div>
            <div class="detail-item">
              <span class="label">邮箱：</span>
              <span class="value">{{ selectedUser.email }}</span>
            </div>
            <div class="detail-item">
              <span class="label">角色：</span>
              <span class="value">{{ selectedUser.role === 'admin' ? '管理员' : '普通用户' }}</span>
            </div>
            <div class="detail-item">
              <span class="label">状态：</span>
              <span class="value">{{ selectedUser.is_active ? '正常' : '禁用' }}</span>
            </div>
          </div>
        </div>
        
        <div class="detail-section">
          <h4>统计信息</h4>
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-number">{{ userStats.total_banks }}</div>
              <div class="stat-label">创建题库</div>
            </div>
            <div class="stat-item">
              <div class="stat-number">{{ userStats.total_answers }}</div>
              <div class="stat-label">答题总数</div>
            </div>
            <div class="stat-item">
              <div class="stat-number">{{ userStats.accuracy_rate }}%</div>
              <div class="stat-label">正确率</div>
            </div>
            <div class="stat-item">
              <div class="stat-number">{{ userStats.total_points }}</div>
              <div class="stat-label">总积分</div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import type { User } from '@/types/auth'
import {
  getUserList,
  createUser,
  updateUser,
  toggleUserStatus as toggleUserStatusAPI,
  deleteUser,
  getUserStats,
  exportUsers as exportUsersAPI
} from '@/api/admin'
import dayjs from 'dayjs'

const loading = ref(false)
const users = ref<User[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 搜索和筛选
const searchKeyword = ref('')
const selectedRole = ref('')
const selectedStatus = ref('')

// 对话框状态
const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const createLoading = ref(false)
const selectedUser = ref<User | null>(null)
const userStats = ref({
  total_banks: 0,
  total_answers: 0,
  accuracy_rate: 0,
  total_points: 0
})

// 创建用户表单
const createFormRef = ref<FormInstance>()
const createForm = reactive({
  username: '',
  email: '',
  password: '',
  role: 'user'
})

const createRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度为3-20个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

const formatDate = (dateString: string) => {
  return dayjs(dateString).format('YYYY-MM-DD HH:mm')
}

const fetchUsers = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      per_page: pageSize.value,
      search: searchKeyword.value || undefined,
      role: selectedRole.value || undefined,
      status: selectedStatus.value || undefined
    }

    const response = await getUserList(params)
    users.value = response.users
    total.value = response.total
  } catch (error) {
    console.error('获取用户列表失败:', error)
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchUsers()
}

const handleFilter = () => {
  currentPage.value = 1
  fetchUsers()
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchUsers()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  fetchUsers()
}

const viewUser = async (user: User) => {
  selectedUser.value = user

  // 获取用户统计信息
  try {
    const stats = await getUserStats(user.id)
    userStats.value = stats
  } catch (error) {
    console.error('获取用户统计失败:', error)
    userStats.value = {
      total_banks: 0,
      total_answers: 0,
      correct_answers: 0,
      accuracy_rate: 0,
      total_points: 0
    }
  }

  showDetailDialog.value = true
}

const editUser = (user: User) => {
  ElMessage.info('编辑用户功能开发中...')
}

const toggleUserStatus = async (user: User) => {
  try {
    const action = user.is_active ? '禁用' : '启用'
    await ElMessageBox.confirm(
      `确定要${action}用户 ${user.username} 吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await toggleUserStatusAPI(user.id, !user.is_active)
    user.is_active = !user.is_active
    ElMessage.success(`用户${action}成功`)
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

const handleCreateUser = async () => {
  if (!createFormRef.value) return

  try {
    await createFormRef.value.validate()

    createLoading.value = true

    await createUser(createForm)
    ElMessage.success('用户创建成功')

    showCreateDialog.value = false
    createFormRef.value.resetFields()
    fetchUsers()
  } catch (error: any) {
    if (error.response?.data?.message) {
      ElMessage.error(error.response.data.message)
    } else {
      ElMessage.error('创建用户失败')
    }
  } finally {
    createLoading.value = false
  }
}

const exportUsers = async () => {
  try {
    const params = {
      search: searchKeyword.value || undefined,
      role: selectedRole.value || undefined,
      status: selectedStatus.value || undefined
    }

    await exportUsersAPI(params)
    ElMessage.success('用户数据导出成功')
  } catch (error) {
    console.error('导出用户数据失败:', error)
    ElMessage.error('导出失败')
  }
}

onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
.user-manage {
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

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-details {
  flex: 1;
}

.username {
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.email {
  font-size: 12px;
  color: var(--text-secondary);
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.user-detail {
  max-height: 500px;
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
}

.detail-item {
  display: flex;
  align-items: center;
}

.detail-item .label {
  font-weight: 500;
  color: var(--text-secondary);
  margin-right: 8px;
  min-width: 60px;
}

.detail-item .value {
  color: var(--text-primary);
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
