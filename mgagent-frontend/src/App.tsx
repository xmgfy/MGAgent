import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Loader2, CheckCircle, UserIcon, LogOut } from 'lucide-react'
import Sidebar from './components/Sidebar'
import ChatHeader from './components/ChatHeader'
import ChatHistory from './components/ChatHistory'
import ChatInput from './components/ChatInput'
import AuthModal from './components/AuthModal'
import {
  chatApi,
  sessionApi,
  authApi,
  clearAuthToken,
  type Session,
  type Message,
  type User,
} from './api/client'

function App() {
  const [sessions, setSessions] = useState<Session[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [isTyping, setIsTyping] = useState(false)
  const [uploadingFile, setUploadingFile] = useState<string | null>(null)
  const [uploadSuccess, setUploadSuccess] = useState(false)
  const [user, setUser] = useState<User | null>(null)
  const [showAuthModal, setShowAuthModal] = useState(false)
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

  const handleSendMessage = async (message: string) => {
    if (!user && sessions.length >= 3) {
      setChatCountWarning(true)
      setTimeout(() => setChatCountWarning(false), 5000)
      return
    }

    setIsTyping(true)
    
    const tempUserId = `temp-${Date.now()}`
    const newUserMessage: Message = {
      id: tempUserId,
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
    } catch (error: any) {
      if (error.response?.status === 403) {
        setChatCountWarning(true)
        setTimeout(() => setChatCountWarning(false), 5000)
      } else if (error.response?.status === 503) {
        const errorDetail = error.response.data.detail
        const sessionId = typeof errorDetail === 'object' && errorDetail.session_id ? errorDetail.session_id : null
        
        if (sessionId) {
          setCurrentSessionId(sessionId)
        }
        
        const errorContent = typeof errorDetail === 'object' 
          ? errorDetail.message 
          : '系统尚未配置AI模型，请联系管理员在管理端配置并启用模型后重试。'
        
        const errorMessage: Message = {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: errorContent,
          created_at: new Date().toISOString(),
        }
        setMessages(prev => prev.filter(m => m.id !== tempUserId))
        setMessages(prev => [...prev, errorMessage])
      } else {
        const errorMessage: Message = {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: `请求失败: ${error.response?.data?.detail || '未知错误'}。请稍后重试。`,
          created_at: new Date().toISOString(),
        }
        setMessages(prev => prev.filter(m => m.id !== tempUserId))
        setMessages(prev => [...prev, errorMessage])
      }
      console.error('Failed to send message:', error)
    } finally {
      setIsTyping(false)
    }
  }

  const handleSendMessageWithFile = async (message: string, file: File) => {
    if (!user && sessions.length >= 3) {
      setChatCountWarning(true)
      setTimeout(() => setChatCountWarning(false), 5000)
      return
    }

    setIsTyping(true)
    setUploadingFile(file.name)
    
    const tempUserId = `temp-${Date.now()}`
    const newUserMessage: Message = {
      id: tempUserId,
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
      setUploadSuccess(true)
      setTimeout(() => setUploadSuccess(false), 3000)
      
      await loadSessions()
      await loadSessionMessages(response.session_id)
      await loadCurrentUser()
    } catch (error: any) {
      if (error.response?.status === 403) {
        setChatCountWarning(true)
        setTimeout(() => setChatCountWarning(false), 5000)
      } else if (error.response?.status === 503) {
        const errorDetail = error.response.data.detail
        const sessionId = typeof errorDetail === 'object' && errorDetail.session_id ? errorDetail.session_id : null
        
        if (sessionId) {
          setCurrentSessionId(sessionId)
        }
        
        const errorContent = typeof errorDetail === 'object' 
          ? errorDetail.message 
          : '系统尚未配置AI模型，请联系管理员在管理端配置并启用模型后重试。'
        
        const errorMessage: Message = {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: errorContent,
          created_at: new Date().toISOString(),
        }
        setMessages(prev => prev.filter(m => m.id !== tempUserId))
        setMessages(prev => [...prev, errorMessage])
      } else {
        const errorMessage: Message = {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: `请求失败: ${error.response?.data?.detail || '未知错误'}。请稍后重试。`,
          created_at: new Date().toISOString(),
        }
        setMessages(prev => prev.filter(m => m.id !== tempUserId))
        setMessages(prev => [...prev, errorMessage])
      }
      console.error('Failed to send message with file:', error)
    } finally {
      setIsTyping(false)
      setUploadingFile(null)
    }
  }

  const handleSelectSession = (sessionId: string) => {
    setCurrentSessionId(sessionId)
  }

  const handleCreateSession = () => {
    setCurrentSessionId(null)
    setMessages([])
  }

  const handleDeleteSession = async (sessionId: string) => {
    if (!confirm('确定要删除这个对话吗？')) return
    
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

  const handleClearChat = () => {
    if (!confirm('确定要清空当前对话吗？')) return
    handleCreateSession()
  }

  const handleLoginSuccess = (loggedInUser: User) => {
    setUser(loggedInUser)
    loadSessions()
  }

  const handleLogout = () => {
    clearAuthToken()
    setUser(null)
    setCurrentSessionId(null)
    setMessages([])
    loadSessions()
  }

  const currentSession = sessions.find((s) => s.id === currentSessionId)

  return (
    <div className="h-screen flex bg-gray-50">
      <Sidebar
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSelectSession={handleSelectSession}
        onCreateSession={handleCreateSession}
        onDeleteSession={handleDeleteSession}
      />

      <div className="flex-1 flex flex-col h-full">
        <ChatHeader title={currentSession?.title || '新对话'} onClear={handleClearChat} />
        
        <div className="flex-1 bg-gray-50 overflow-hidden">
          <ChatHistory messages={messages} isTyping={isTyping} />
        </div>
        
        <ChatInput
          onSend={handleSendMessage}
          onUpload={handleSendMessageWithFile}
          isLoading={isTyping || !!uploadingFile}
        />
      </div>

      <AnimatePresence>
        {(uploadingFile || uploadSuccess) && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            className="fixed bottom-24 right-6 flex items-center gap-3 px-4 py-3 bg-white rounded-xl shadow-lg border border-gray-100"
          >
            {uploadingFile ? (
              <>
                <Loader2 size={20} className="text-primary-500 animate-spin" />
                <span className="text-sm text-gray-700">上传中: {uploadingFile}</span>
              </>
            ) : (
              <>
                <CheckCircle size={20} className="text-green-500" />
                <span className="text-sm text-green-600">上传成功!</span>
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {chatCountWarning && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="fixed top-20 right-6 px-6 py-4 bg-red-500 text-white rounded-xl shadow-lg"
          >
            <p className="font-medium">已达到免费问答次数限制</p>
            <p className="text-sm opacity-90">请登录账号继续使用</p>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        className="fixed bottom-6 left-6 flex flex-col gap-2"
      >
        {user ? (
          <motion.button
            onClick={handleLogout}
            className="flex items-center gap-2 px-4 py-2.5 bg-white rounded-xl shadow-lg border border-gray-100 hover:bg-gray-50 transition-colors"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
              <UserIcon size={16} className="text-primary-500" />
            </div>
            <div className="text-left">
              <p className="text-sm font-medium text-gray-800">{user.username}</p>
              <p className="text-xs text-gray-500">
                {user.chat_count}/{user.max_chats} 次
              </p>
            </div>
            <LogOut size={16} className="text-gray-400 ml-2" />
          </motion.button>
        ) : (
          <motion.button
            onClick={() => setShowAuthModal(true)}
            className="flex items-center gap-2 px-4 py-2.5 bg-white rounded-xl shadow-lg border border-gray-100 hover:bg-gray-50 transition-colors"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
              <UserIcon size={16} className="text-primary-500" />
            </div>
            <div className="text-left">
              <p className="text-sm font-medium text-gray-800">登录 / 注册</p>
              <p className="text-xs text-gray-500">免费使用 3 次</p>
            </div>
          </motion.button>
        )}
      </motion.div>

      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        onLoginSuccess={handleLoginSuccess}
      />
    </div>
  )
}

export default App
