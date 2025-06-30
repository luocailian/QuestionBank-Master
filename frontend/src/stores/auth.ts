import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import type { User, LoginForm, RegisterForm } from '@/types/auth'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refreshToken'))
  const loading = ref(false)

  // 计算属性
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  // 设置认证信息
  const setAuth = (authData: { access_token: string; refresh_token: string; user: User }) => {
    token.value = authData.access_token
    refreshToken.value = authData.refresh_token
    user.value = authData.user
    
    localStorage.setItem('token', authData.access_token)
    localStorage.setItem('refreshToken', authData.refresh_token)
  }

  // 清除认证信息
  const clearAuth = () => {
    token.value = null
    refreshToken.value = null
    user.value = null
    
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
  }

  // 登录
  const login = async (loginForm: LoginForm) => {
    loading.value = true
    try {
      const response = await authApi.login(loginForm)
      setAuth(response.data)
      return response
    } finally {
      loading.value = false
    }
  }

  // 注册
  const register = async (registerForm: RegisterForm) => {
    loading.value = true
    try {
      const response = await authApi.register(registerForm)
      setAuth(response.data)
      return response
    } finally {
      loading.value = false
    }
  }

  // 登出
  const logout = () => {
    clearAuth()
  }

  // 检查认证状态
  const checkAuth = async () => {
    if (!token.value) {
      return false
    }

    try {
      const response = await authApi.getCurrentUser()
      user.value = response.data.user
      return true
    } catch (error) {
      clearAuth()
      return false
    }
  }

  // 刷新令牌
  const refreshAccessToken = async () => {
    if (!refreshToken.value) {
      throw new Error('No refresh token available')
    }

    try {
      const response = await authApi.refreshToken()
      token.value = response.data.access_token
      localStorage.setItem('token', response.data.access_token)
      return response.data.access_token
    } catch (error) {
      clearAuth()
      throw error
    }
  }

  // 更新用户信息
  const updateUser = (userData: Partial<User>) => {
    if (user.value) {
      user.value = { ...user.value, ...userData }
    }
  }

  return {
    // 状态
    user: readonly(user),
    token: readonly(token),
    loading: readonly(loading),
    
    // 计算属性
    isAuthenticated,
    isAdmin,
    
    // 方法
    login,
    register,
    logout,
    checkAuth,
    refreshAccessToken,
    updateUser,
    setAuth,
    clearAuth
  }
})
