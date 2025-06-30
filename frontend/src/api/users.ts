import request from './request'
import type { ProfileUpdateForm, PasswordChangeForm } from '@/types/users'

export const usersApi = {
  // 获取用户资料
  getProfile: () => {
    return request.get('/users/profile')
  },

  // 更新用户资料
  updateProfile: (data: ProfileUpdateForm) => {
    return request.put('/users/profile', data)
  },

  // 修改密码
  changePassword: (data: PasswordChangeForm) => {
    return request.post('/users/change-password', data)
  },

  // 获取用户统计
  getUserStatistics: () => {
    return request.get('/users/statistics')
  },

  // 获取排行榜
  getLeaderboard: (params?: { period?: string; limit?: number }) => {
    return request.get('/users/leaderboard', { params })
  }
}
