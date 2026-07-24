import axios from 'axios'

const token = localStorage.getItem('token')

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  },
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export const setAuthToken = (token: string) => {
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`
  localStorage.setItem('token', token)
}

export const clearAuthToken = () => {
  delete api.defaults.headers.common['Authorization']
  localStorage.removeItem('token')
}

export interface ChatRequest {
  message: string
  session_id?: string
}

export interface ChatResponse {
  session_id: string
  response: string
}

export interface Message {
  id: string | number
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export interface Session {
  id: string
  title: string
  created_at: string
  updated_at: string
  messages?: Message[]
}

export interface Document {
  id: string
  filename: string
  file_type: string
  file_size: number
  status: 'uploaded' | 'indexed' | 'error'
  created_at: string
}

export interface Tool {
  name: string
  description: string
}

export interface User {
  id: string
  username: string
  email: string
  role: string
  status: string
  chat_count: number
  max_chats: number
  created_at: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

export const chatApi = {
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await api.post('/chat', request)
    return response.data
  },
  
  sendMessageStream: async (request: ChatRequest): Promise<Response> => {
    const token = localStorage.getItem('token')
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (token) headers['Authorization'] = `Bearer ${token}`
    
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
    })
    return response
  },
  
  sendMessageWithFile: async (message: string, session_id: string | undefined, file: File): Promise<ChatResponse> => {
    const formData = new FormData()
    formData.append('message', message)
    if (session_id) formData.append('session_id', session_id)
    formData.append('file', file)
    
    const response = await api.post('/chat/with-file', formData, {
      headers: { 'Content-Type': undefined },
    })
    return response.data
  },
}

export const sessionApi = {
  getSessions: async (): Promise<Session[]> => {
    const response = await api.get('/sessions')
    return response.data
  },
  
  getSession: async (sessionId: string): Promise<Session> => {
    const response = await api.get(`/sessions/${sessionId}`)
    return response.data
  },
  
  updateSession: async (sessionId: string, title: string): Promise<Session> => {
    const response = await api.put(`/sessions/${sessionId}`, { title })
    return response.data
  },
  
  deleteSession: async (sessionId: string): Promise<void> => {
    await api.delete(`/sessions/${sessionId}`)
  },
}

export const documentApi = {
  uploadDocument: async (file: File): Promise<Document> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post('/documents', formData, {
      headers: { 'Content-Type': undefined },
    })
    return response.data
  },
  
  getDocuments: async (): Promise<Document[]> => {
    const response = await api.get('/documents')
    return response.data
  },
  
  getDocument: async (documentId: string): Promise<Document> => {
    const response = await api.get(`/documents/${documentId}`)
    return response.data
  },
  
  deleteDocument: async (documentId: string): Promise<void> => {
    await api.delete(`/documents/${documentId}`)
  },
}

export const toolApi = {
  getTools: async (): Promise<{ tools: Tool[] }> => {
    const response = await api.get('/tools')
    return response.data
  },
}

export const healthApi = {
  check: async (): Promise<{ status: string }> => {
    const response = await api.get('/health')
    return response.data
  },
}

export const authApi = {
  login: async (request: LoginRequest): Promise<TokenResponse> => {
    const response = await api.post('/auth/login', request)
    return response.data
  },
  
  register: async (request: RegisterRequest): Promise<{ message: string; user: User }> => {
    const response = await api.post('/auth/register', request)
    return response.data
  },
  
  getCurrentUser: async (): Promise<User | null> => {
    try {
      const response = await api.get('/auth/me')
      return response.data
    } catch {
      return null
    }
  },
  
  logout: () => {
    clearAuthToken()
  },
}

export default api