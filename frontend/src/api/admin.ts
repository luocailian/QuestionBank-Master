import { request } from '@/utils/request'
import type { User } from '@/types/auth'

export interface AdminStats {
  totalUsers: number
  totalBanks: number
  totalQuestions: number
  totalAnswers: number
}

export interface UserListParams {
  page?: number
  per_page?: number
  search?: string
  role?: string
  status?: string
}

export interface UserListResponse {
  users: User[]
  total: number
  page: number
  per_page: number
  pages: number
}

export interface CreateUserData {
  username: string
  email: string
  password: string
  role: string
}

export interface UpdateUserData {
  username?: string
  email?: string
  role?: string
  is_active?: boolean
}

export interface RecentActivity {
  id: number
  description: string
  created_at: string
  user_id?: number
  type?: string
}

// 获取管理后台统计数据
export const getAdminStats = async (): Promise<AdminStats> => {
  try {
    // 使用专门的管理统计API
    const response = await request.get('/users/admin/statistics')
    const data = response.data

    return {
      totalUsers: data.total_users || 0,
      totalBanks: data.total_banks || 0,
      totalQuestions: data.total_questions || 0,
      totalAnswers: data.total_answers || 0
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
    // 如果新API失败，回退到原来的方法
    try {
      const [usersRes, banksRes] = await Promise.all([
        request.get('/users'),
        request.get('/banks')
      ])

      let totalQuestions = 0
      if (banksRes.data.data && Array.isArray(banksRes.data.data)) {
        totalQuestions = banksRes.data.data.reduce((sum: number, bank: any) => {
          return sum + (bank.question_count || 0)
        }, 0)
      }

      return {
        totalUsers: usersRes.data.total || usersRes.data.users?.length || 0,
        totalBanks: banksRes.data.total || banksRes.data.data?.length || 0,
        totalQuestions,
        totalAnswers: 0
      }
    } catch (fallbackError) {
      console.error('回退方法也失败:', fallbackError)
      return {
        totalUsers: 0,
        totalBanks: 0,
        totalQuestions: 0,
        totalAnswers: 0
      }
    }
  }
}

// 获取用户列表
export const getUserList = async (params: UserListParams = {}): Promise<UserListResponse> => {
  const response = await request.get('/users', { params })
  return response.data
}

// 创建用户
export const createUser = async (data: CreateUserData): Promise<User> => {
  const response = await request.post('/auth/register', data)
  return response.data.user
}

// 更新用户
export const updateUser = async (id: number, data: UpdateUserData): Promise<User> => {
  const response = await request.put(`/users/${id}`, data)
  return response.data
}

// 切换用户状态
export const toggleUserStatus = async (id: number, is_active: boolean): Promise<User> => {
  const response = await request.put(`/users/${id}`, { is_active })
  return response.data
}

// 删除用户
export const deleteUser = async (id: number): Promise<void> => {
  await request.delete(`/users/${id}`)
}

// 获取用户详细统计
export const getUserStats = async (id: number) => {
  try {
    const response = await request.get(`/users/${id}/statistics`)
    return response.data
  } catch (error) {
    console.error('获取用户统计失败:', error)
    return {
      total_banks: 0,
      total_answers: 0,
      correct_answers: 0,
      accuracy_rate: 0,
      total_points: 0
    }
  }
}

// 获取最近活动
export const getRecentActivities = async (): Promise<RecentActivity[]> => {
  try {
    // 这里可以从多个来源获取活动数据
    const activities: RecentActivity[] = []
    
    // 获取最近注册的用户
    const usersRes = await request.get('/users', {
      params: { page: 1, per_page: 5 }
    })

    if (usersRes.data.users) {
      usersRes.data.users.forEach((user: User) => {
        activities.push({
          id: user.id,
          description: `用户 ${user.username} 注册了账号`,
          created_at: user.created_at,
          user_id: user.id,
          type: 'user_register'
        })
      })
    }

    // 获取最近创建的题库
    const banksRes = await request.get('/banks', {
      params: { page: 1, per_page: 5 }
    })

    if (banksRes.data.data) {
      banksRes.data.data.forEach((bank: any) => {
        activities.push({
          id: bank.id,
          description: `题库《${bank.name}》被创建`,
          created_at: bank.created_at,
          user_id: bank.created_by,
          type: 'bank_create'
        })
      })
    }

    // 按时间排序，最新的在前
    return activities.sort((a, b) => 
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    ).slice(0, 10)
    
  } catch (error) {
    console.error('获取最近活动失败:', error)
    return []
  }
}

// 导出用户数据
export const exportUsers = async (params: UserListParams = {}) => {
  try {
    const response = await request.get('/users/export', {
      params,
      responseType: 'blob'
    })
    
    // 创建下载链接
    const blob = new Blob([response.data], { 
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `users_export_${new Date().toISOString().split('T')[0]}.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('导出用户数据失败:', error)
    throw error
  }
}
