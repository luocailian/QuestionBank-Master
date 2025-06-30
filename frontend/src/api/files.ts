import request from './request'

export const filesApi = {
  // 上传文件
  uploadFile: (formData: FormData) => {
    return request.post('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 解析文件
  parseFile: (importId: number) => {
    return request.post(`/files/parse/${importId}`)
  },

  // 获取文件导入记录列表
  getFileImports: (params?: { page?: number; per_page?: number; status?: string }) => {
    return request.get('/files/imports', { params })
  },

  // 获取文件导入记录详情
  getFileImportDetail: (id: number) => {
    return request.get(`/files/imports/${id}`)
  },

  // 删除文件导入记录
  deleteFileImport: (id: number) => {
    return request.delete(`/files/imports/${id}`)
  },

  // 获取支持的文件格式
  getSupportedFormats: () => {
    return request.get('/files/supported-formats')
  }
}
