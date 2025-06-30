<template>
  <div class="profile-page">
    <div class="page-container">
      <div class="container">
        <div class="page-header">
          <h2>个人资料</h2>
          <p>管理你的个人信息和账户设置</p>
        </div>

        <div class="profile-content">
          <!-- 基本信息 -->
          <div class="profile-section">
            <div class="section-header">
              <h3>基本信息</h3>
            </div>
            
            <el-form
              ref="profileFormRef"
              :model="profileForm"
              :rules="profileRules"
              label-width="100px"
            >
              <el-form-item label="头像">
                <div class="avatar-upload">
                  <el-avatar :src="profileForm.avatar_url" :size="80">
                    {{ profileForm.username?.charAt(0).toUpperCase() }}
                  </el-avatar>
                  <div class="avatar-actions">
                    <el-button size="small" @click="handleAvatarUpload">
                      更换头像
                    </el-button>
                  </div>
                </div>
              </el-form-item>
              
              <el-form-item label="用户名" prop="username">
                <el-input v-model="profileForm.username" />
              </el-form-item>
              
              <el-form-item label="邮箱" prop="email">
                <el-input v-model="profileForm.email" />
              </el-form-item>
              
              <el-form-item>
                <el-button 
                  type="primary" 
                  :loading="profileLoading"
                  @click="handleUpdateProfile"
                >
                  保存修改
                </el-button>
              </el-form-item>
            </el-form>
          </div>

          <!-- 修改密码 -->
          <div class="profile-section">
            <div class="section-header">
              <h3>修改密码</h3>
            </div>
            
            <el-form
              ref="passwordFormRef"
              :model="passwordForm"
              :rules="passwordRules"
              label-width="100px"
            >
              <el-form-item label="当前密码" prop="old_password">
                <el-input 
                  v-model="passwordForm.old_password" 
                  type="password"
                  show-password
                />
              </el-form-item>
              
              <el-form-item label="新密码" prop="new_password">
                <el-input 
                  v-model="passwordForm.new_password" 
                  type="password"
                  show-password
                />
              </el-form-item>
              
              <el-form-item label="确认密码" prop="confirm_password">
                <el-input 
                  v-model="passwordForm.confirm_password" 
                  type="password"
                  show-password
                />
              </el-form-item>
              
              <el-form-item>
                <el-button 
                  type="primary" 
                  :loading="passwordLoading"
                  @click="handleChangePassword"
                >
                  修改密码
                </el-button>
              </el-form-item>
            </el-form>
          </div>

          <!-- 账户统计 -->
          <div class="profile-section">
            <div class="section-header">
              <h3>账户统计</h3>
            </div>
            
            <div class="stats-grid" v-if="statistics">
              <div class="stat-card">
                <div class="stat-icon">
                  <el-icon size="24"><Document /></el-icon>
                </div>
                <div class="stat-content">
                  <div class="stat-number">{{ statistics.total_banks }}</div>
                  <div class="stat-label">参与题库</div>
                </div>
              </div>
              
              <div class="stat-card">
                <div class="stat-icon">
                  <el-icon size="24"><Edit /></el-icon>
                </div>
                <div class="stat-content">
                  <div class="stat-number">{{ statistics.total_answers }}</div>
                  <div class="stat-label">答题总数</div>
                </div>
              </div>
              
              <div class="stat-card">
                <div class="stat-icon">
                  <el-icon size="24"><Check /></el-icon>
                </div>
                <div class="stat-content">
                  <div class="stat-number">{{ statistics.accuracy_rate }}%</div>
                  <div class="stat-label">正确率</div>
                </div>
              </div>
              
              <div class="stat-card">
                <div class="stat-icon">
                  <el-icon size="24"><Trophy /></el-icon>
                </div>
                <div class="stat-content">
                  <div class="stat-number">{{ statistics.total_points }}</div>
                  <div class="stat-label">总积分</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Document, Edit, Check, Trophy } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { usersApi } from '@/api/users'
import type { ProfileUpdateForm, PasswordChangeForm } from '@/types/users'
import type { UserStatistics } from '@/types/auth'

const authStore = useAuthStore()

const profileFormRef = ref<FormInstance>()
const passwordFormRef = ref<FormInstance>()
const profileLoading = ref(false)
const passwordLoading = ref(false)
const statistics = ref<UserStatistics | null>(null)

const profileForm = reactive<ProfileUpdateForm>({
  username: '',
  email: '',
  avatar_url: ''
})

const passwordForm = reactive<PasswordChangeForm & { confirm_password: string }>({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const validateConfirmPassword = (rule: any, value: string, callback: any) => {
  if (value !== passwordForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const profileRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度为3-20个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ]
}

const passwordRules: FormRules = {
  old_password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 50, message: '密码长度为6-50个字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const handleUpdateProfile = async () => {
  if (!profileFormRef.value) return
  
  try {
    await profileFormRef.value.validate()
    
    profileLoading.value = true
    await usersApi.updateProfile(profileForm)
    
    // 更新store中的用户信息
    authStore.updateUser(profileForm)
    
    ElMessage.success('个人信息更新成功')
  } catch (error: any) {
    if (error.response?.data?.message) {
      ElMessage.error(error.response.data.message)
    }
  } finally {
    profileLoading.value = false
  }
}

const handleChangePassword = async () => {
  if (!passwordFormRef.value) return
  
  try {
    await passwordFormRef.value.validate()
    
    passwordLoading.value = true
    await usersApi.changePassword({
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password
    })
    
    ElMessage.success('密码修改成功')
    
    // 清空表单
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
  } catch (error: any) {
    if (error.response?.data?.message) {
      ElMessage.error(error.response.data.message)
    }
  } finally {
    passwordLoading.value = false
  }
}

const handleAvatarUpload = () => {
  ElMessage.info('头像上传功能开发中...')
}

const fetchUserData = async () => {
  try {
    // 获取用户资料
    const profileResponse = await usersApi.getProfile()
    const userData = profileResponse.data
    
    profileForm.username = userData.username
    profileForm.email = userData.email
    profileForm.avatar_url = userData.avatar_url || ''
    
    // 获取统计数据
    const statsResponse = await usersApi.getUserStatistics()
    statistics.value = statsResponse.data
  } catch (error) {
    console.error('获取用户数据失败:', error)
  }
}

onMounted(() => {
  fetchUserData()
})
</script>

<style scoped>
.profile-page {
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

.profile-content {
  max-width: 800px;
  margin: 0 auto;
}

.profile-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: var(--shadow-base);
}

.section-header {
  margin-bottom: 24px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-lighter);
}

.section-header h3 {
  margin: 0;
  font-size: 18px;
  color: var(--text-primary);
}

.avatar-upload {
  display: flex;
  align-items: center;
  gap: 16px;
}

.avatar-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  transition: all 0.3s;
}

.stat-card:hover {
  border-color: var(--primary-color);
  box-shadow: var(--shadow-base);
}

.stat-icon {
  color: var(--primary-color);
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
  .profile-content {
    padding: 0 16px;
  }
  
  .profile-section {
    padding: 16px;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .avatar-upload {
    flex-direction: column;
    text-align: center;
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
