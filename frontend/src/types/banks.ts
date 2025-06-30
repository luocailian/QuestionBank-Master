export interface QuestionBank {
  id: number
  name: string
  description?: string
  category?: string
  difficulty: 'easy' | 'medium' | 'hard'
  tags: string[]
  creator_id: number
  creator_name?: string
  is_public: boolean
  question_count: number
  created_at: string
  updated_at: string
  user_progress?: UserProgress
}

export interface BankCreateForm {
  name: string
  description?: string
  category?: string
  difficulty?: 'easy' | 'medium' | 'hard'
  tags?: string[]
  is_public?: boolean
}

export interface BankQuery {
  page?: number
  per_page?: number
  category?: string
  difficulty?: string
  search?: string
  my_banks?: boolean
}

export interface BankStatistics {
  question_types: Record<string, number>
  total_attempts: number
  correct_attempts: number
  accuracy_rate: number
}

export interface UserProgress {
  id: number
  user_id: number
  bank_id: number
  bank_name: string
  total_questions: number
  answered_questions: number
  correct_answers: number
  total_score: number
  total_time: number
  accuracy_rate: number
  progress_rate: number
  last_answered_at?: string
  created_at: string
  updated_at: string
}
