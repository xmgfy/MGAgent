import axios from 'axios'

const token = localStorage.getItem('admin_token')

const api = axios.create({
  baseURL: '/admin/api',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  },
})

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('admin_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('admin_token')
      localStorage.removeItem('admin_info')
      delete api.defaults.headers.common['Authorization']
    }
    console.error('Admin API Error:', error)
    return Promise.reject(error)
  }
)

export const setAdminToken = (token: string) => {
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`
  localStorage.setItem('admin_token', token)
}

export const clearAdminToken = () => {
  delete api.defaults.headers.common['Authorization']
  localStorage.removeItem('admin_token')
  localStorage.removeItem('admin_info')
}

export interface KnowledgeBaseStats {
  total_documents: number
  total_files: number
  file_types: Record<string, number>
  total_size: number
  indexed_count: number
}

export interface DocumentInfo {
  filename: string
  file_type: string
  file_size: number
  created_at: string
  status: string
}

export interface VectorDBStats {
  total_chunks: number
  persist_directory: string
  embedding_model: string
}

export interface VectorChunk {
  id: string
  content: string
  metadata: Record<string, any>
}

export interface StorageDBStats {
  database_path: string
  tables: string[]
  total_records: Record<string, number>
}

export interface TableInfo {
  name: string
  columns: Array<{ name: string; type: string; is_pk: boolean }>
  record_count: number
}

export interface ModelConfig {
  id: string
  name: string
  api_key: string
  api_key_masked: string
  api_base: string
  model_name: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface SystemStatus {
  status: string
  version: string
  uptime: string
}

export interface SystemInfo {
  platform: string
  python_version: string
  cpu_count: number
  memory_usage: number
  disk_usage: number
}

export interface User {
  id: string
  username: string
  email: string
  role: string
  status: string
  tenant_id: string
  chat_count: number
  max_chats: number
  created_at: string
}

export interface Tenant {
  id: string
  name: string
  description: string
  status: string
  max_users: number
  admin_count: number
  user_count: number
  created_at: string
}

export interface UpdateUserStatusRequest {
  status: string
}

export interface UpdateUserRoleRequest {
  role: string
}

export interface Admin {
  id: string
  username: string
  email: string
  role: string
  tenant_id: string
  tenant_name?: string
  status: string
  created_at: string
  updated_at?: string
}

export interface CreateAdminRequest {
  username: string
  email: string
  password: string
  role?: string
  tenant_id?: string
}

export interface UpdateAdminRequest {
  email?: string
  role?: string
  tenant_id?: string
  status?: string
}

export interface AdminLoginRequest {
  username: string
  password: string
}

export interface AdminRegisterRequest {
  username: string
  email: string
  password: string
  tenant_name?: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  admin: Admin
}

export interface UploadResponse {
  message: string
  filename: string
  file_type: string
  file_size: number
  chunks_count: number
}

export interface PreviewResponse {
  content: string
  type: 'text' | 'error'
  truncated?: boolean
}

export interface Notification {
  id: string
  type: 'error' | 'warning' | 'info' | 'user_registration'
  title: string
  message: string
  is_read: boolean
  created_at: string
}

export const knowledgeBaseApi = {
  getStats: async (): Promise<KnowledgeBaseStats> => {
    const response = await api.get('/knowledge-base/stats')
    return response.data
  },
  
  getDocuments: async (): Promise<DocumentInfo[]> => {
    const response = await api.get('/knowledge-base/documents')
    return response.data
  },
  
  deleteDocument: async (filename: string): Promise<void> => {
    await api.delete(`/knowledge-base/documents/${filename}`)
  },
  
  clear: async (): Promise<void> => {
    await api.post('/knowledge-base/clear')
  },
  
  upload: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post('/knowledge-base/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },
  
  download: async (filename: string): Promise<void> => {
    const response = await api.get(`/knowledge-base/documents/${filename}/download`, {
      responseType: 'blob'
    })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  },
  
  preview: async (filename: string): Promise<PreviewResponse> => {
    const response = await api.get(`/knowledge-base/documents/${filename}/preview`)
    return response.data
  },
}

export const vectorDbApi = {
  getStats: async (): Promise<VectorDBStats> => {
    const response = await api.get('/vector-db/stats')
    return response.data
  },
  
  getChunks: async (limit: number = 10, offset: number = 0): Promise<VectorChunk[]> => {
    const response = await api.get('/vector-db/chunks', { params: { limit, offset } })
    return response.data
  },
  
  search: async (query: string, k: number = 3): Promise<{ results: VectorChunk[] }> => {
    const response = await api.get('/vector-db/search', { params: { query, k } })
    return response.data
  },
  
  deleteChunk: async (chunkId: string): Promise<void> => {
    await api.delete(`/vector-db/chunks/${chunkId}`)
  },
  
  clear: async (): Promise<void> => {
    await api.post('/vector-db/clear')
  },
}

export const storageDbApi = {
  getStats: async (): Promise<StorageDBStats> => {
    const response = await api.get('/storage-db/stats')
    return response.data
  },
  
  getTables: async (): Promise<TableInfo[]> => {
    const response = await api.get('/storage-db/tables')
    return response.data
  },
  
  getTableData: async (tableName: string, limit: number = 50, offset: number = 0): Promise<{ columns: string[]; data: Record<string, any>[] }> => {
    const response = await api.get(`/storage-db/tables/${tableName}/data`, { params: { limit, offset } })
    return response.data
  },
  
  executeQuery: async (query: string): Promise<{ columns?: string[]; data?: Record<string, any>[]; message?: string }> => {
    const response = await api.post('/storage-db/query', { query })
    return response.data
  },
}

export const modelApi = {
  getConfig: async (): Promise<ModelConfig> => {
    try {
      const response = await api.get('/model/config')
      return response.data
    } catch {
      return {
        id: '',
        name: '',
        api_key: '',
        api_key_masked: '',
        api_base: '',
        model_name: '',
        is_active: false,
        created_at: '',
        updated_at: ''
      }
    }
  },
  
  getConfigs: async (): Promise<ModelConfig[]> => {
    const response = await api.get('/model/configs')
    return response.data
  },
  
  createConfig: async (config: { name: string; api_key: string; api_base: string; model_name: string }): Promise<ModelConfig> => {
    const response = await api.post('/model/config', config)
    return response.data
  },
  
  updateConfig: async (configId: string, config: { api_key?: string; api_base?: string; model_name?: string }): Promise<ModelConfig> => {
    const response = await api.put(`/model/config/${configId}`, config)
    return response.data
  },
  
  activateConfig: async (configId: string): Promise<ModelConfig> => {
    const response = await api.post(`/model/config/${configId}/activate`)
    return response.data
  },
  
  deactivateConfig: async (configId: string): Promise<ModelConfig> => {
    const response = await api.post(`/model/config/${configId}/deactivate`)
    return response.data
  },
  
  deleteConfig: async (configId: string): Promise<void> => {
    await api.delete(`/model/config/${configId}`)
  },
  
  testConnection: async (): Promise<{ status: string; response?: string; error?: string }> => {
    const response = await api.get('/model/test')
    return response.data
  },
}

export interface DashboardStats {
  model_calls: number
  total_sessions: number
  total_users: number
}

export const systemApi = {
  getStatus: async (): Promise<SystemStatus> => {
    const response = await api.get('/system/status')
    return response.data
  },
  
  getInfo: async (): Promise<SystemInfo> => {
    const response = await api.get('/system/info')
    return response.data
  },
}

export const notificationApi = {
  getNotifications: async (): Promise<Notification[]> => {
    const response = await api.get('/notifications')
    return response.data
  },
  
  getUnreadCount: async (): Promise<{ count: number }> => {
    const response = await api.get('/notifications/unread-count')
    return response.data
  },
  
  markAsRead: async (notificationId: string): Promise<Notification> => {
    const response = await api.put(`/notifications/${notificationId}/read`)
    return response.data
  },
  
  createNotification: async (type: string, title: string, message: string): Promise<Notification> => {
    const response = await api.post('/notifications', { type, title, message })
    return response.data
  },
}

export const userApi = {
  getUsers: async (status?: string): Promise<User[]> => {
    const response = await api.get('/users', { params: { status } })
    return response.data
  },
  
  getUser: async (userId: string): Promise<User> => {
    const response = await api.get(`/users/${userId}`)
    return response.data
  },
  
  updateUserStatus: async (userId: string, status: string): Promise<User> => {
    const response = await api.put(`/users/${userId}/status`, { status })
    return response.data
  },
  
  updateUserRole: async (userId: string, role: string): Promise<User> => {
    const response = await api.put(`/users/${userId}/role`, { role })
    return response.data
  },
  
  deleteUser: async (userId: string): Promise<{ message: string }> => {
    const response = await api.delete(`/users/${userId}`)
    return response.data
  },
}

export const tenantApi = {
  getTenants: async (): Promise<Tenant[]> => {
    const response = await api.get('/tenants')
    return response.data
  },
  
  getTenant: async (tenantId: string): Promise<Tenant> => {
    const response = await api.get(`/tenants/${tenantId}`)
    return response.data
  },
  
  createTenant: async (tenant: { name: string; description?: string; max_users?: number }): Promise<Tenant> => {
    const response = await api.post('/tenants', tenant)
    return response.data
  },
  
  updateTenant: async (tenantId: string, tenant: { name?: string; description?: string; max_users?: number; status?: string }): Promise<Tenant> => {
    const response = await api.put(`/tenants/${tenantId}`, tenant)
    return response.data
  },
  
  deleteTenant: async (tenantId: string): Promise<{ message: string }> => {
    const response = await api.delete(`/tenants/${tenantId}`)
    return response.data
  },
}

export const adminApi = {
  getAdmins: async (role?: string, tenantId?: string): Promise<Admin[]> => {
    const response = await api.get('/admins', { params: { role, tenant_id: tenantId } })
    return response.data
  },
  
  getAdmin: async (adminId: string): Promise<Admin> => {
    const response = await api.get(`/admins/${adminId}`)
    return response.data
  },
  
  createAdmin: async (admin: CreateAdminRequest): Promise<Admin> => {
    const response = await api.post('/admins', admin)
    return response.data
  },
  
  updateAdmin: async (adminId: string, admin: UpdateAdminRequest): Promise<Admin> => {
    const response = await api.put(`/admins/${adminId}`, admin)
    return response.data
  },
  
  deleteAdmin: async (adminId: string): Promise<{ message: string }> => {
    const response = await api.delete(`/admins/${adminId}`)
    return response.data
  },
}

export interface UpdateAdminProfileRequest {
  email?: string
}

export interface UpdateAdminPasswordRequest {
  old_password: string
  new_password: string
}

export const authApi = {
  login: async (request: AdminLoginRequest): Promise<TokenResponse> => {
    const response = await api.post('/auth/login', request)
    return response.data
  },
  
  register: async (request: AdminRegisterRequest): Promise<{ message: string; admin: Admin }> => {
    const response = await api.post('/auth/register', request)
    return response.data
  },
  
  getCurrentAdmin: async (): Promise<Admin | null> => {
    const token = localStorage.getItem('admin_token')
    if (!token) {
      return null
    }
    // 确保token被设置到axios实例
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`
    try {
      const response = await api.get('/auth/me')
      return response.data
    } catch (error: any) {
      if (error.response?.status === 401) {
        localStorage.removeItem('admin_token')
        localStorage.removeItem('admin_info')
        delete api.defaults.headers.common['Authorization']
      }
      return null
    }
  },
  
  updateProfile: async (request: UpdateAdminProfileRequest): Promise<Admin> => {
    const response = await api.put('/auth/profile', request)
    return response.data
  },
  
  updatePassword: async (request: UpdateAdminPasswordRequest): Promise<{ message: string }> => {
    const response = await api.put('/auth/password', request)
    return response.data
  },
  
  logout: () => {
    clearAdminToken()
  },
}

export const dashboardApi = {
  getStats: async (): Promise<DashboardStats> => {
    const response = await api.get('/dashboard/stats')
    return response.data
  },
}

export default api
