import request from './request'
import type { LoginForm, RegisterForm, User } from '@/types/auth'

export const authApi = {
  // 用户登录
  login: (data: LoginForm) => {
    return request.post('/auth/login', data)
  },

  // 用户注册
  register: (data: RegisterForm) => {
    return request.post('/auth/register', data)
  },

  // 刷新token
  refreshToken: () => {
    return request.post('/auth/refresh')
  },

  // 获取当前用户信息
  getCurrentUser: () => {
    return request.get('/auth/me')
  },

  // 登出
  logout: () => {
    return request.post('/auth/logout')
  }
}
