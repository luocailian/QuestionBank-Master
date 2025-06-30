export interface ProfileUpdateForm {
  username?: string
  email?: string
  avatar_url?: string
}

export interface PasswordChangeForm {
  old_password: string
  new_password: string
}

export interface LeaderboardEntry {
  rank: number
  user: {
    id: number
    username: string
    avatar_url?: string
  }
  points: number
}

export interface LeaderboardResponse {
  period: string
  leaderboard: LeaderboardEntry[]
}
