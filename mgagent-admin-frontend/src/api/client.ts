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
    const errorMsg = error.response?.data?.detail || error.message || '请求失败'
    console.error('Admin API Error:', errorMsg)
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
  document_id?: string
  storage_path?: string
}

export interface RetrieveTestChunk {
  id: string
  content_preview: string
  content: string
  distance: number
  metadata: Record<string, any>
}

export interface RetrieveTestResponse {
  query: string
  knowledge_base: {
    id: string
    name: string
    retrieve_limit: number
    similarity_threshold: number | null
    enable_hybrid: boolean
    enable_rerank: boolean
  }
  embedding_model: string
  threshold_applied: boolean
  threshold_value: number | null
  results_before_threshold: number
  results_after_threshold: number
  results: RetrieveTestChunk[]
  timings_ms: {
    embedding_load_ms?: number
    query_embed_ms?: number
    vector_search_ms?: number
    total_ms?: number
  }
  hybrid_executed?: boolean
  rerank_executed?: boolean
  note?: string
}

export interface RetrievalLogEntry {
  id: number
  query: string
  knowledge_base_id: string | null
  kb_name: string | null
  top_k: number
  threshold_applied: boolean
  threshold_value: number | null
  results_count: number
  rerank_applied: boolean
  hybrid_applied: boolean
  latency_ms: number | null
  results_preview: string | null
  created_at: string | null
}

export interface EvalDatasetItem {
  id: number
  query: string
  name: string | null
  note: string | null
  expected_chunk_ids: string[]
  expected_document_ids: string[]
  created_at: string | null
}

export interface EvalRunResponse {
  eval_result_id: number
  knowledge_base: string
  total_queries: number
  hit_rate: { at_1: number; at_3: number; at_5: number; at_10: number }
  mrr: { at_5: number; at_10: number }
  latency_ms: number
  config: Record<string, any>
  details: Array<{ query: string; hit_at_5: boolean; hit_at_10: boolean; top3: string[] }>
}

export interface EvalResultEntry {
  id: number
  total_queries: number
  hit_at_1: number
  hit_at_5: number
  hit_at_10: number
  hit_rate_at_5: number
  hit_rate_at_10: number
  mrr_at_5: number
  mrr_at_10: number
  latency_ms: number
  config: Record<string, any> | null
  created_at: string | null
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
  model_type: string  // 'chat' or 'embedding'
  provider: string    // openai, zhipu, dashscope, jina, local
  api_key: string
  api_key_masked: string
  api_base: string
  model_name: string
  dimension?: number  // 仅 embedding 类型使用
  is_local: boolean
  is_active: boolean
  scenario?: string
  tenant_id?: string
  temperature?: number
  top_p?: number
  max_tokens?: number
  presence_penalty?: number
  frequency_penalty?: number
  created_at: string
  updated_at: string
}

export interface Provider {
  id?: string
  code: string
  display_name: string
  favicon_domain: string
  default_api_base: string
  supports_api_key: boolean
  supports_local: boolean
  supports_discover: boolean
  supported_model_types: string[]
  discover_endpoint?: string
  fallback_models?: Record<string, string[]>
  description?: string
  api_key?: string
  api_key_masked?: string
  has_api_key?: boolean
  is_system?: boolean
  is_active?: boolean
  created_at?: string
  updated_at?: string
}

export interface ProviderCreateInput {
  code: string
  display_name: string
  favicon_domain?: string
  default_api_base?: string
  supports_api_key: boolean
  supports_local: boolean
  supports_discover: boolean
  supported_model_types: string[]
  fallback_models?: Record<string, string[]>
  description?: string
  api_key?: string
}

export interface ProviderUpdateInput {
  display_name?: string
  favicon_domain?: string
  default_api_base?: string
  supports_api_key?: boolean
  supports_local?: boolean
  supports_discover?: boolean
  supported_model_types?: string[]
  fallback_models?: Record<string, string[]>
  description?: string
  api_key?: string
  is_active?: boolean
}

export interface DiscoveredModel {
  model_id: string
  model_type: 'chat' | 'embedding' | 'reranker'
  dimension?: number
  owned_by?: string
  size_mb?: number
  modified_at?: string
}

export interface DiscoverModelsResponse {
  provider: string
  provider_name: string
  total: number
  chat_count: number
  embedding_count: number
  reranker_count: number
  models: DiscoveredModel[]
}

export interface UserModelItem {
  id: string
  name: string
  model_type: string
  provider: string
  model_name: string
  dimension?: number
  is_local: boolean
  is_active: boolean
}

export interface LocalEmbeddingModel {
  id: string
  name: string
  display_name: string
  dimension: number
  size_mb: number
  language: string
  description: string
  recommended_for: string
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
  chunks_count?: number
  document_id?: string
  status?: string
}

export interface EmbeddingPreset {
  provider: string
  name: string
  model: string
  api_base: string
  dimension: number
  description: string
  requires_api_key: boolean
}

export interface PreviewResponse {
  content: string
  type: 'text' | 'error'
  truncated?: boolean
}

export interface KnowledgeBase {
  id: string
  name: string
  description: string | null
  tenant_id: string | null
  vector_db_type: string
  embedding_model_id: string | null
  chunk_size: number
  chunk_overlap: number
  chunk_separator: string | null
  retrieve_limit: number
  similarity_threshold: number | null
  enable_rerank: boolean
  rerank_model_id: string | null
  rerank_top_n: number
  rerank_score_threshold: number | null
  enable_hybrid: boolean
  hybrid_alpha: number
  is_active: boolean
  document_count?: number
  created_at?: string
  updated_at?: string
}

export interface KnowledgeBaseCreateInput {
  name: string
  description?: string
  vector_db_type?: string
  embedding_model_id?: string | null
  chunk_size?: number
  chunk_overlap?: number
  chunk_separator?: string | null
  retrieve_limit?: number
  similarity_threshold?: number | null
  enable_rerank?: boolean
  rerank_model_id?: string | null
  rerank_top_n?: number
  rerank_score_threshold?: number | null
  enable_hybrid?: boolean
  hybrid_alpha?: number
  is_active?: boolean
}

export interface KnowledgeBaseUpdateInput {
  name?: string
  description?: string
  vector_db_type?: string
  embedding_model_id?: string | null
  chunk_size?: number
  chunk_overlap?: number
  chunk_separator?: string | null
  retrieve_limit?: number
  similarity_threshold?: number | null
  enable_rerank?: boolean
  rerank_model_id?: string | null
  rerank_top_n?: number
  rerank_score_threshold?: number | null
  enable_hybrid?: boolean
  hybrid_alpha?: number
  is_active?: boolean
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
  // ---------- KnowledgeBase CRUD ----------
  listKnowledgeBases: async (): Promise<KnowledgeBase[]> => {
    const response = await api.get('/knowledge-base/list')
    return response.data.items || []
  },

  getKnowledgeBase: async (kbId: string): Promise<KnowledgeBase> => {
    const response = await api.get(`/knowledge-base/${kbId}`)
    return response.data
  },

  createKnowledgeBase: async (data: KnowledgeBaseCreateInput): Promise<KnowledgeBase> => {
    const response = await api.post('/knowledge-base', data)
    return response.data
  },

  updateKnowledgeBase: async (kbId: string, data: KnowledgeBaseUpdateInput): Promise<KnowledgeBase> => {
    const response = await api.put(`/knowledge-base/${kbId}`, data)
    return response.data
  },

  deleteKnowledgeBase: async (kbId: string): Promise<{ message: string }> => {
    const response = await api.delete(`/knowledge-base/${kbId}`)
    return response.data
  },

  // ---------- Documents (scope optional) ----------
  getStats: async (): Promise<KnowledgeBaseStats> => {
    const response = await api.get('/knowledge-base/stats')
    return response.data
  },

  getDocuments: async (): Promise<DocumentInfo[]> => {
    const response = await api.get('/knowledge-base/documents')
    return response.data
  },

  deleteDocument: async (documentId: string): Promise<void> => {
    await api.delete(`/knowledge-base/documents/${documentId}`)
  },

  batchDelete: async (documentIds: string[]): Promise<{ deleted: string[]; failed: { id: string; reason: string }[] }> => {
    const response = await api.post('/knowledge-base/documents/batch-delete', { document_ids: documentIds })
    return response.data
  },

  upload: async (
    file: File,
    knowledgeBaseId?: string,
    onProgress?: (percent: number) => void
  ): Promise<UploadResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    if (knowledgeBaseId) {
      formData.append('knowledge_base_id', knowledgeBaseId)
    }
    const response = await api.post('/knowledge-base/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percent)
        }
      }
    })
    return response.data
  },

  indexDocument: async (documentId: string): Promise<{ message: string; chunks_count: number; status: string; embedding_model?: string }> => {
    const response = await api.post(`/knowledge-base/documents/${documentId}/index`, {})
    return response.data
  },

  getEmbeddingPresets: async (): Promise<{ presets: EmbeddingPreset[] }> => {
    const response = await api.get('/knowledge-base/embedding-presets')
    return response.data
  },

  download: async (documentId: string, filename: string): Promise<void> => {
    const response = await api.get(`/knowledge-base/documents/${documentId}/download`, {
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

  preview: async (documentId: string): Promise<PreviewResponse> => {
    const response = await api.get(`/knowledge-base/documents/${documentId}/preview`)
    return response.data
  },

  retrieveTest: async (
    kbId: string,
    query: string,
    topK: number = 5,
    similarityThreshold?: number
  ): Promise<RetrieveTestResponse> => {
    const response = await api.post(`/knowledge-base/${kbId}/retrieve-test`, {
      query,
      top_k: topK,
      similarity_threshold: similarityThreshold ?? null
    })
    return response.data
  },

  fetchRetrievalLogs: async (
    kbId?: string,
    limit: number = 50
  ): Promise<RetrievalLogEntry[]> => {
    const params: Record<string, any> = { limit }
    if (kbId) params.knowledge_base_id = kbId
    const response = await api.get('/knowledge-base/retrieve-logs', { params })
    return response.data
  },

  fetchEvalDataset: async (kbId: string): Promise<EvalDatasetItem[]> => {
    const response = await api.get(`/knowledge-base/${kbId}/eval-dataset`)
    return response.data
  },

  addEvalDatasetItem: async (
    kbId: string,
    item: { query: string; expected_chunk_ids?: string[]; expected_document_ids?: string[]; name?: string; note?: string }
  ): Promise<{ id: number; message: string }> => {
    const response = await api.post(`/knowledge-base/${kbId}/eval-dataset`, item)
    return response.data
  },

  deleteEvalDatasetItem: async (itemId: number): Promise<{ message: string }> => {
    const response = await api.delete(`/knowledge-base/eval-dataset/${itemId}`)
    return response.data
  },

  runEval: async (kbId: string): Promise<EvalRunResponse> => {
    const response = await api.post(`/knowledge-base/${kbId}/eval`)
    return response.data
  },

  fetchEvalResults: async (kbId: string, limit: number = 20): Promise<EvalResultEntry[]> => {
    const response = await api.get(`/knowledge-base/${kbId}/eval-results`, { params: { limit } })
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
    const response = await api.get('/model/config')
    return response.data
  },
  
  getConfigs: async (): Promise<ModelConfig[]> => {
    const response = await api.get('/model/configs')
    return response.data
  },
  
  getProviders: async (modelType?: string): Promise<Provider[]> => {
    const response = await api.get('/model/providers', { params: { model_type: modelType } })
    return response.data
  },
  
  getModelList: async (modelType?: string, onlyActive: boolean = true): Promise<UserModelItem[]> => {
    const response = await api.get('/model/list', { params: { model_type: modelType, only_active: onlyActive } })
    return response.data
  },

  discoverModels: async (params: {
    provider_code: string
    api_base?: string
    api_key?: string
    model_type?: string
  }): Promise<DiscoverModelsResponse> => {
    const response = await api.post('/model/providers/discover-models', params)
    return response.data
  },

  createProvider: async (data: ProviderCreateInput): Promise<Provider> => {
    const response = await api.post('/model/providers', data)
    return response.data
  },

  updateProvider: async (providerId: string, data: ProviderUpdateInput): Promise<Provider> => {
    const response = await api.put(`/model/providers/${providerId}`, data)
    return response.data
  },

  deleteProvider: async (providerId: string): Promise<{ message: string }> => {
    const response = await api.delete(`/model/providers/${providerId}`)
    return response.data
  },

  toggleProvider: async (providerId: string): Promise<Provider> => {
    const response = await api.post(`/model/providers/${providerId}/toggle`)
    return response.data
  },
  
  getLocalModels: async (): Promise<LocalEmbeddingModel[]> => {
    const response = await api.get('/model/local-models')
    return response.data
  },
  
  downloadLocalModel: async (modelId: string): Promise<{ status: string; message: string }> => {
    const response = await api.post('/model/local-models/download', { model_id: modelId })
    return response.data
  },
  
  createConfig: async (config: {
    name: string;
    model_name: string;
    model_type?: string;
    provider?: string;
    api_key?: string;
    api_base?: string;
    dimension?: number;
    is_local?: boolean;
    scenario?: string;
    tenant_id?: string;
    temperature?: number;
    top_p?: number;
    max_tokens?: number;
    presence_penalty?: number;
    frequency_penalty?: number;
  }): Promise<ModelConfig> => {
    const response = await api.post('/model/config', config)
    return response.data
  },
  
  updateConfig: async (configId: string, config: {
    name?: string;
    model_name?: string;
    model_type?: string;
    provider?: string;
    api_key?: string;
    api_base?: string;
    dimension?: number;
    is_local?: boolean;
    scenario?: string;
    tenant_id?: string;
    temperature?: number;
    top_p?: number;
    max_tokens?: number;
    presence_penalty?: number;
    frequency_penalty?: number;
  }): Promise<ModelConfig> => {
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

export interface SecurityRule {
  id: string
  tenant_id: string | null
  rule_type: 'keyword' | 'regex'
  content: string
  action: 'block' | 'mask'
  priority: number
  is_active: boolean
  description: string | null
  created_at: string
  updated_at: string
}

export interface SecurityRuleRequest {
  rule_type: 'keyword' | 'regex'
  content: string
  action: 'block' | 'mask'
  priority?: number
  description?: string
}

export interface SecurityRuleUpdateRequest {
  rule_type?: 'keyword' | 'regex'
  content?: string
  action?: 'block' | 'mask'
  priority?: number
  description?: string
}

export interface SecurityTestResult {
  original: string
  filtered: string
  has_sensitive: boolean
  matched_rules: Array<{ type: string; content: string; action: string }>
}

export const securityApi = {
  getRules: async (): Promise<SecurityRule[]> => {
    const response = await api.get('/security/rules')
    return response.data
  },

  createRule: async (request: SecurityRuleRequest): Promise<SecurityRule> => {
    const response = await api.post('/security/rules', request)
    return response.data
  },

  updateRule: async (ruleId: string, request: SecurityRuleUpdateRequest): Promise<SecurityRule> => {
    const response = await api.put(`/security/rules/${ruleId}`, request)
    return response.data
  },

  toggleRule: async (ruleId: string): Promise<SecurityRule> => {
    const response = await api.post(`/security/rules/${ruleId}/toggle`)
    return response.data
  },

  deleteRule: async (ruleId: string): Promise<{ message: string }> => {
    const response = await api.delete(`/security/rules/${ruleId}`)
    return response.data
  },

  testFilter: async (content: string): Promise<SecurityTestResult> => {
    const response = await api.post('/security/test', { content })
    return response.data
  },
}

export default api
