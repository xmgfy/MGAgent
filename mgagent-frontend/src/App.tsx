import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Loader2, CheckCircle, UserIcon, LogOut } from 'lucide-react'
import Sidebar from './components/Sidebar'
import ChatHeader from './components/ChatHeader'
import ChatHistory from './components/ChatHistory'
import ChatInput from './components/ChatInput'
import AuthModal from './components/AuthModal'
import { useChat } from './hooks/useChat'

function App() {
  const {
    sessions,
    currentSessionId,
    messages,
    isTyping,
    user,
    chatCountWarning,
    sendMessage,
    sendMessageWithFile,
    selectSession,
    createSession,
    deleteSession,
    logout,
    loginSuccess,
  } = useChat()

  const [showAuthModal, setShowAuthModal] = useState(false)
  const [uploadingFile, setUploadingFile] = useState<string | null>(null)
  const [uploadSuccess, setUploadSuccess] = useState(false)

  const handleUpload = async (message: string, file: File) => {
    setUploadingFile(file.name)
    try {
      await sendMessageWithFile(message, file)
      setUploadSuccess(true)
      setTimeout(() => setUploadSuccess(false), 3000)
    } finally {
      setUploadingFile(null)
    }
  }

  const handleClearChat = () => {
    if (!window.confirm('确定要清空当前对话吗？')) return
    createSession()
  }

  const currentSession = sessions.find((s) => s.id === currentSessionId)

  return (
    <div className="h-screen flex bg-gray-50">
      <Sidebar
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSelectSession={selectSession}
        onCreateSession={createSession}
        onDeleteSession={deleteSession}
      />

      <div className="flex-1 flex flex-col h-full">
        <ChatHeader title={currentSession?.title || '新对话'} onClear={handleClearChat} />

        <div className="flex-1 bg-gray-50 overflow-hidden">
          <ChatHistory messages={messages} isTyping={isTyping} />
        </div>

        <ChatInput
          onSend={sendMessage}
          onUpload={handleUpload}
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
            onClick={logout}
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
        onLoginSuccess={loginSuccess}
      />
    </div>
  )
}

export default App
