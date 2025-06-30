import request from './request'
import type { QuestionCreateForm, QuestionQuery, AnswerSubmitForm } from '@/types/questions'

export const questionsApi = {
  // 获取题目列表
  getQuestions: (params: QuestionQuery) => {
    return request.get('/questions', { params })
  },

  // 获取题目详情
  getQuestionDetail: (id: number) => {
    return request.get(`/questions/${id}`)
  },

  // 创建题目
  createQuestion: (data: QuestionCreateForm) => {
    return request.post('/questions', data)
  },

  // 更新题目
  updateQuestion: (id: number, data: Partial<QuestionCreateForm>) => {
    return request.put(`/questions/${id}`, data)
  },

  // 删除题目
  deleteQuestion: (id: number) => {
    return request.delete(`/questions/${id}`)
  },

  // 提交答案
  submitAnswer: (id: number, data: AnswerSubmitForm) => {
    return request.post(`/questions/${id}/answer`, data)
  },

  // 收藏题目
  favoriteQuestion: (id: number) => {
    return request.post(`/questions/${id}/favorite`)
  },

  // 取消收藏题目
  unfavoriteQuestion: (id: number) => {
    return request.delete(`/questions/${id}/favorite`)
  },

  // 获取收藏的题目
  getFavoriteQuestions: (params?: { page?: number; per_page?: number }) => {
    return request.get('/questions/favorites', { params })
  }
}
