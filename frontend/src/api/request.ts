import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

// 创建axios实例
const request = axios.create({
  baseURL: 'http://localhost:5000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    
    // 添加认证token
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    return response
  },
  async (error) => {
    const authStore = useAuthStore()
    
    if (error.response) {
      const { status, data } = error.response
      
      switch (status) {
        case 401:
          // Token过期，尝试刷新
          if (authStore.token && !error.config._retry) {
            error.config._retry = true
            
            try {
              await authStore.refreshAccessToken()
              // 重新发送原请求
              error.config.headers.Authorization = `Bearer ${authStore.token}`
              return request(error.config)
            } catch (refreshError) {
              // 刷新失败，清除认证信息并跳转到登录页
              authStore.clearAuth()
              window.location.href = '/login'
              return Promise.reject(refreshError)
            }
          } else {
            // 没有token或刷新失败
            authStore.clearAuth()
            if (window.location.pathname !== '/login') {
              window.location.href = '/login'
            }
          }
          break
          
        case 403:
          ElMessage.error(data.message || '权限不足')
          break
          
        case 404:
          ElMessage.error(data.message || '资源不存在')
          break
          
        case 422:
          // 表单验证错误
          if (data.errors) {
            const errorMessages = Object.values(data.errors).flat()
            ElMessage.error(errorMessages.join(', '))
          } else {
            ElMessage.error(data.message || '请求参数错误')
          }
          break
          
        case 500:
          ElMessage.error(data.message || '服务器内部错误')
          break
          
        default:
          ElMessage.error(data.message || `请求失败 (${status})`)
      }
    } else if (error.request) {
      // 网络错误
      ElMessage.error('网络连接失败，请检查网络设置')
    } else {
      // 其他错误
      ElMessage.error('请求失败，请稍后重试')
    }
    
    return Promise.reject(error)
  }
)

export default request
