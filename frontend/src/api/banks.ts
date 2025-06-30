import request from './request'
import type { BankCreateForm, BankQuery } from '@/types/banks'

export const banksApi = {
  // 获取题库列表
  getBanks: (params?: BankQuery) => {
    return request.get('/banks', { params })
  },

  // 获取题库详情
  getBankDetail: (id: number) => {
    return request.get(`/banks/${id}`)
  },

  // 创建题库
  createBank: (data: BankCreateForm) => {
    return request.post('/banks', data)
  },

  // 更新题库
  updateBank: (id: number, data: Partial<BankCreateForm>) => {
    return request.put(`/banks/${id}`, data)
  },

  // 删除题库
  deleteBank: (id: number) => {
    return request.delete(`/banks/${id}`)
  },

  // 获取题库统计
  getBankStatistics: (id: number) => {
    return request.get(`/banks/${id}/statistics`)
  },

  // 获取题库分类
  getCategories: () => {
    return request.get('/banks/categories')
  },

  // 更新题库统计信息
  updateBankStats: (id: number) => {
    return request.post(`/banks/${id}/update-stats`)
  },

  // 导出题库
  exportBank: (id: number, format: string = 'json') => {
    return request.get(`/banks/${id}/export`, {
      params: { format },
      responseType: 'blob'
    })
  },

  // 获取可用的导出格式
  getExportFormats: () => {
    return request.get('/banks/export-formats')
  }
}
