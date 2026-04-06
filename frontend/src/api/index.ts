import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000',
})

api.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const msg = err.response?.data?.message || err.message || '请求失败'
    return Promise.reject(new Error(msg))
  }
)

export default api

// ===== 项目管理 =====
export const projectApi = {
  list: () => api.get('/api/projects'),
  create: (data: any) => api.post('/api/projects', data),
  get: (id: number) => api.get(`/api/projects/${id}`),
  update: (id: number, data: any) => api.put(`/api/projects/${id}`, data),
  delete: (id: number) => api.delete(`/api/projects/${id}`),
}

// ===== 招标文件 =====
export const fileApi = {
  get: (projectId: number) => api.get(`/api/projects/${projectId}/tender-file`),
  upload: (projectId: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/api/projects/${projectId}/tender-file`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  parse: (projectId: number) => api.post(`/api/projects/${projectId}/tender-file/parse`),
}

// ===== 目录树 =====
export const outlineApi = {
  get: (projectId: number) => api.get(`/api/projects/${projectId}/outline`),
  save: (projectId: number, nodes: any[]) =>
    api.put(`/api/projects/${projectId}/outline`, { nodes }),
}

// ===== 章节内容 =====
export const chapterApi = {
  get: (projectId: number, nodeId: number) =>
    api.get(`/api/projects/${projectId}/chapters/${nodeId}`),
  save: (projectId: number, nodeId: number, content: string) =>
    api.put(`/api/projects/${projectId}/chapters/${nodeId}`, { content }),
  generate: (
    projectId: number,
    nodeId: number,
    data?: { useKnowledge?: boolean; knowledgeTopK?: number }
  ) => api.post(`/api/projects/${projectId}/chapters/${nodeId}/generate`, data || {}),
}

// ===== 知识库 =====
export const knowledgeApi = {
  list: (projectId: number) => api.get(`/api/projects/${projectId}/knowledge-files`),
  upload: (projectId: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/api/projects/${projectId}/knowledge-files`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  parse: (projectId: number, fileId: number) =>
    api.post(`/api/projects/${projectId}/knowledge-files/${fileId}/parse`),
  update: (projectId: number, fileId: number, data: { isEnabled?: boolean }) =>
    api.put(`/api/projects/${projectId}/knowledge-files/${fileId}`, data),
  remove: (projectId: number, fileId: number) =>
    api.delete(`/api/projects/${projectId}/knowledge-files/${fileId}`),
  search: (projectId: number, data: { query: string; topK?: number }) =>
    api.post(`/api/projects/${projectId}/knowledge/search`, data),
}

// ===== 废标检查 =====
export const reviewApi = {
  get: (projectId: number) => api.get(`/api/projects/${projectId}/bid-check`),
  run: (projectId: number) => api.post(`/api/projects/${projectId}/bid-check`),
}

// ===== 导出 =====
export const exportApi = {
  list: (projectId: number) => api.get(`/api/projects/${projectId}/exports`),
  create: (projectId: number, data: any) =>
    api.post(`/api/projects/${projectId}/exports`, data),
  downloadUrl: (projectId: number, exportId: number) =>
    `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'}/api/projects/${projectId}/exports/${exportId}/download`,
}
