export interface FileImport {
  id: number
  user_id: number
  bank_id?: number
  bank_name?: string
  filename: string
  file_type: 'pdf' | 'docx' | 'xlsx' | 'json'
  file_size: number
  status: 'pending' | 'processing' | 'completed' | 'failed'
  questions_imported: number
  error_message?: string
  created_at: string
  completed_at?: string
}

export interface SupportedFormat {
  extension: string
  description: string
  max_size: string
}

export interface SupportedFormatsResponse {
  formats: SupportedFormat[]
  max_file_size: number
}
