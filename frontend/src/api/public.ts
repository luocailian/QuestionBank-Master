/**
 * 公共API - 不需要认证的接口
 */
import request from '@/utils/request'

// 公共统计数据类型
export interface PublicStats {
  totalUsers: number
  totalBanks: number
  totalQuestions: number
}

/**
 * 获取公共统计数据（不需要登录）
 */
export const getPublicStats = async (): Promise<PublicStats> => {
  try {
    // 使用专门的公共统计API
    const response = await request.get('/banks/public/statistics')
    const data = response.data

    return {
      totalUsers: data.total_users || 0,
      totalBanks: data.total_banks || 0,
      totalQuestions: data.total_questions || 0
    }
  } catch (error) {
    console.error('获取公共统计数据失败:', error)

    // 如果新API失败，回退到原来的方法
    try {
      const banksResponse = await request.get('/banks', {
        params: {
          per_page: 1000
        }
      })

      const banksData = banksResponse.data?.data || []
      const totalBanks = banksData.length
      const totalQuestions = Array.isArray(banksData)
        ? banksData.reduce((sum: number, bank: any) => sum + (bank.question_count || 0), 0)
        : 0

      return {
        totalUsers: Math.max(totalBanks * 5, 50), // 估算用户数
        totalBanks,
        totalQuestions
      }
    } catch (fallbackError) {
      console.error('回退方法也失败:', fallbackError)
      return {
        totalUsers: 0,
        totalBanks: 0,
        totalQuestions: 0
      }
    }
  }
}

/**
 * 获取热门题库（不需要登录）
 */
export const getPopularBanks = async (limit: number = 6) => {
  try {
    const response = await request.get('/banks', {
      params: {
        per_page: limit,
        sort_by: 'question_count', // 按题目数量排序，题目多的更热门
        sort_order: 'desc',
        is_public: true // 只获取公开题库
      }
    })

    // 处理不同的响应格式
    let banksData = []
    if (response.data?.banks) {
      banksData = response.data.banks
    } else if (response.data?.data) {
      banksData = response.data.data
    } else if (Array.isArray(response.data)) {
      banksData = response.data
    }
    return Array.isArray(banksData) ? banksData : []
  } catch (error) {
    console.error('获取热门题库失败:', error)
    return []
  }
}
