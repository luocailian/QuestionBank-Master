export interface User {
  id: number
  username: string
  email: string
  role: 'admin' | 'user'
  avatar_url?: string
  created_at: string
  updated_at: string
  is_active: boolean
  last_login?: string
}

export interface LoginForm {
  username: string
  password: string
}

export interface RegisterForm {
  username: string
  email: string
  password: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  user: User
}

export interface UserStatistics {
  total_banks: number
  total_answers: number
  correct_answers: number
  accuracy_rate: number
  total_points: number
  progress: UserProgress[]
  points: UserPoints
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

export interface UserPoints {
  id: number
  user_id: number
  total_points: number
  daily_points: number
  weekly_points: number
  monthly_points: number
  created_at: string
  updated_at: string
}
