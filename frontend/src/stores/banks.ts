import { defineStore } from 'pinia'
import { ref } from 'vue'
import { banksApi } from '@/api/banks'
import type { QuestionBank, BankCreateForm, BankQuery } from '@/types/banks'

export const useBanksStore = defineStore('banks', () => {
  // 状态
  const banks = ref<QuestionBank[]>([])
  const currentBank = ref<QuestionBank | null>(null)
  const loading = ref(false)
  const categories = ref<string[]>([])

  // 获取题库列表
  const fetchBanks = async (query?: BankQuery) => {
    loading.value = true
    try {
      const response = await banksApi.getBanks(query)
      // 修复：正确解析后端返回的数据格式
      banks.value = response.data.banks || response.data
      return response
    } finally {
      loading.value = false
    }
  }

  // 获取题库详情
  const fetchBankDetail = async (id: number) => {
    loading.value = true
    try {
      const response = await banksApi.getBankDetail(id)
      currentBank.value = response.data
      return response
    } finally {
      loading.value = false
    }
  }

  // 创建题库
  const createBank = async (bankData: BankCreateForm) => {
    loading.value = true
    try {
      const response = await banksApi.createBank(bankData)
      banks.value.unshift(response.data)
      return response
    } finally {
      loading.value = false
    }
  }

  // 更新题库
  const updateBank = async (id: number, bankData: Partial<BankCreateForm>) => {
    loading.value = true
    try {
      const response = await banksApi.updateBank(id, bankData)
      
      // 更新列表中的题库
      const index = banks.value.findIndex(bank => bank.id === id)
      if (index !== -1) {
        banks.value[index] = response.data
      }
      
      // 更新当前题库
      if (currentBank.value?.id === id) {
        currentBank.value = response.data
      }
      
      return response
    } finally {
      loading.value = false
    }
  }

  // 删除题库
  const deleteBank = async (id: number) => {
    loading.value = true
    try {
      await banksApi.deleteBank(id)
      
      // 从列表中移除
      banks.value = banks.value.filter(bank => bank.id !== id)
      
      // 清除当前题库
      if (currentBank.value?.id === id) {
        currentBank.value = null
      }
    } finally {
      loading.value = false
    }
  }

  // 获取题库分类
  const fetchCategories = async () => {
    try {
      const response = await banksApi.getCategories()
      categories.value = response.data.categories
      return response
    } catch (error) {
      console.error('获取分类失败:', error)
    }
  }

  // 获取题库统计
  const fetchBankStatistics = async (id: number) => {
    try {
      const response = await banksApi.getBankStatistics(id)
      return response.data
    } catch (error) {
      console.error('获取题库统计失败:', error)
      throw error
    }
  }

  // 更新题库统计信息
  const updateBankStats = async (id: number) => {
    try {
      const response = await banksApi.updateBankStats(id)

      // 更新列表中的题库统计
      const index = banks.value.findIndex(bank => bank.id === id)
      if (index !== -1) {
        // 重新获取题库详情以更新统计信息
        const bankDetail = await banksApi.getBankDetail(id)
        banks.value[index] = bankDetail.data
      }

      return response
    } catch (error) {
      console.error('更新题库统计失败:', error)
      throw error
    }
  }

  // 清除当前题库
  const clearCurrentBank = () => {
    currentBank.value = null
  }

  return {
    // 状态
    banks: readonly(banks),
    currentBank: readonly(currentBank),
    loading: readonly(loading),
    categories: readonly(categories),
    
    // 方法
    fetchBanks,
    fetchBankDetail,
    createBank,
    updateBank,
    deleteBank,
    fetchCategories,
    fetchBankStatistics,
    updateBankStats,
    clearCurrentBank
  }
})
