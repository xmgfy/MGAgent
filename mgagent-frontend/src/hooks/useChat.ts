import { useState, useEffect, useCallback } from 'react'
import { chatApi, sessionApi, authApi, type Session, type Message, type User } from '../api/client'

interface UseChatReturn {
  sessions: Session[]
  currentSessionId: string | null
  messages: Message[]
  isTyping: boolean
  user: User | null
  chatCountWarning: boolean
  setCurrentSessionId: (id: string | null) => void
  sendMessage: (message: string) => Promise<void>
  sendMessageWithFile: (message: string, file: File) => Promise<void>
  selectSession: (sessionId: string) => void
  createSession: () => void
  deleteSession: (sessionId: string) => Promise<void>
  logout: () => void
  loginSuccess: (loggedInUser: User) => void
}

export function useChat(): UseChatReturn {
  const [sessions, setSessions] = useState<Session[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [isTyping, setIsTyping] = useState(false)
  const [user, setUser] = useState<User | null>(null)
  const [chatCountWarning, setChatCountWarning] = useState(false)

  const loadSessions = useCallback(async () => {
    try {
      const data = await sessionApi.getSessions()
      setSessions(data)
    } catch (error) {
      console.error('Failed to load sessions:', error)
    }
  }, [])

  const loadSessionMessages = useCallback(async (sessionId: string) => {
    try {
      const session = await sessionApi.getSession(sessionId)
      setMessages(session.messages || [])
    } catch (error) {
      console.error('Failed to load session messages:', error)
    }
  }, [])

  const loadCurrentUser = useCallback(async () => {
    try {
      const currentUser = await authApi.getCurrentUser()
      setUser(currentUser)
    } catch (error) {
      console.error('Failed to load current user:', error)
    }
  }, [])

  useEffect(() => {
    loadSessions()
    loadCurrentUser()
  }, [loadSessions, loadCurrentUser])

  useEffect(() => {
    if (currentSessionId) {
      loadSessionMessages(currentSessionId)
    } else {
      setMessages([])
    }
  }, [currentSessionId, loadSessionMessages])

  const handleErrorResponse = (error: unknown, tempMessageId: string) => {
    const err = error as { response?: { status?: number; data?: { detail?: unknown } } }
    const status = err.response?.status
    const errorDetail = err.response?.data?.detail

    const removeTempMessage = () => {
      setMessages(prev => prev.filter(m => m.id !== tempMessageId))
    }

    if (status === 403) {
      setChatCountWarning(true)
      setTimeout(() => setChatCountWarning(false), 5000)
    } else if (status === 503) {
      const sessionId = typeof errorDetail === 'object' && errorDetail && 'session_id' in errorDetail 
        ? (errorDetail as { session_id?: string }).session_id 
        : null

      if (sessionId) {
        setCurrentSessionId(sessionId)
      }

      const errorContent = typeof errorDetail === 'object' && errorDetail && 'message' in errorDetail
        ? (errorDetail as { message: string }).message
        : '系统尚未配置AI模型，请联系管理员在管理端配置并启用模型后重试。'

      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: errorContent,
        created_at: new Date().toISOString(),
      }
      removeTempMessage()
      setMessages(prev => [...prev, errorMessage])
    } else {
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `请求失败: ${errorDetail || '未知错误'}。请稍后重试。`,
        created_at: new Date().toISOString(),
      }
      removeTempMessage()
      setMessages(prev => [...prev, errorMessage])
    }
  }

  const sendMessage = async (message: string) => {
    if (!user && sessions.length >= 3) {
      setChatCountWarning(true)
      setTimeout(() => setChatCountWarning(false), 5000)
      return
    }

    setIsTyping(true)

    const tempMessageId = `temp-${Date.now()}`
    const newUserMessage: Message = {
      id: tempMessageId,
      role: 'user',
      content: message,
      created_at: new Date().toISOString(),
    }

    setMessages(prev => [...prev, newUserMessage])

    try {
      const response = await chatApi.sendMessage({
        message,
        session_id: currentSessionId || undefined,
      })

      setCurrentSessionId(response.session_id)

      await loadSessions()
      await loadSessionMessages(response.session_id)
      await loadCurrentUser()
    } catch (error: unknown) {
      handleErrorResponse(error, tempMessageId)
      console.error('Failed to send message:', error)
    } finally {
      setIsTyping(false)
    }
  }

  const sendMessageWithFile = async (message: string, file: File) => {
    if (!user && sessions.length >= 3) {
      setChatCountWarning(true)
      setTimeout(() => setChatCountWarning(false), 5000)
      return
    }

    setIsTyping(true)

    const tempMessageId = `temp-${Date.now()}`
    const newUserMessage: Message = {
      id: tempMessageId,
      role: 'user',
      content: message || `[上传文件: ${file.name}]`,
      created_at: new Date().toISOString(),
    }

    setMessages(prev => [...prev, newUserMessage])

    try {
      const response = await chatApi.sendMessageWithFile(
        message,
        currentSessionId || undefined,
        file
      )

      setCurrentSessionId(response.session_id)

      await loadSessions()
      await loadSessionMessages(response.session_id)
      await loadCurrentUser()
    } catch (error: unknown) {
      handleErrorResponse(error, tempMessageId)
      console.error('Failed to send message with file:', error)
    } finally {
      setIsTyping(false)
    }
  }

  const selectSession = (sessionId: string) => {
    setCurrentSessionId(sessionId)
  }

  const createSession = () => {
    setCurrentSessionId(null)
    setMessages([])
  }

  const deleteSession = async (sessionId: string) => {
    if (!window.confirm('确定要删除这个对话吗？')) return

    try {
      await sessionApi.deleteSession(sessionId)
      await loadSessions()
      if (currentSessionId === sessionId) {
        setCurrentSessionId(null)
        setMessages([])
      }
    } catch (error) {
      console.error('Failed to delete session:', error)
    }
  }

  const logout = () => {
    authApi.logout()
    setUser(null)
    setCurrentSessionId(null)
    setMessages([])
    loadSessions()
  }

  const loginSuccess = (loggedInUser: User) => {
    setUser(loggedInUser)
    loadSessions()
  }

  return {
    sessions,
    currentSessionId,
    messages,
    isTyping,
    user,
    chatCountWarning,
    setCurrentSessionId,
    sendMessage,
    sendMessageWithFile,
    selectSession,
    createSession,
    deleteSession,
    logout,
    loginSuccess,
  }
}
