export type QuestionType = 'choice' | 'true_false' | 'qa' | 'math' | 'programming'

export interface Question {
  id: number
  bank_id: number
  type: QuestionType
  title: string
  content: QuestionContent
  explanation?: string
  difficulty: 'easy' | 'medium' | 'hard'
  tags: string[]
  points: number
  order_index: number
  created_at: string
  updated_at: string
  answer?: QuestionAnswer
  is_favorited?: boolean
  user_answer?: UserAnswer
}

export interface QuestionContent {
  options?: QuestionOption[]
  [key: string]: any
}

export interface QuestionOption {
  key: string
  text: string
}

export interface QuestionAnswer {
  correct_option?: string
  is_true?: boolean
  keywords?: string[]
  result?: number
  [key: string]: any
}

export interface QuestionCreateForm {
  bank_id: number
  type: QuestionType
  title: string
  content: QuestionContent
  answer: QuestionAnswer
  explanation?: string
  difficulty?: 'easy' | 'medium' | 'hard'
  tags?: string[]
  points?: number
  order_index?: number
}

export interface QuestionQuery {
  bank_id: number
  page?: number
  per_page?: number
  type?: QuestionType
  difficulty?: string
}

export interface AnswerSubmitForm {
  user_answer: any
  time_spent?: number
}

export interface AnswerResult {
  is_correct: boolean
  score: number
  correct_answer: QuestionAnswer
  explanation?: string
  user_answer: any
}

export interface UserAnswer {
  id: number
  user_id: number
  question_id: number
  bank_id: number
  user_answer: any
  is_correct: boolean
  score: number
  time_spent: number
  answered_at: string
}

export interface QuestionStatistics {
  total_attempts: number
  correct_attempts: number
  accuracy_rate: number
  avg_time: number
  favorites_count: number
}
