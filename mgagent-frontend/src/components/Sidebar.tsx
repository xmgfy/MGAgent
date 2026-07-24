import { motion } from 'framer-motion'
import { MessageSquare, Plus, Trash2 } from 'lucide-react'
import type { Session } from '@/api/client'

interface SidebarProps {
  sessions: Session[]
  currentSessionId: string | null
  onSelectSession: (sessionId: string) => void
  onCreateSession: () => void
  onDeleteSession: (sessionId: string) => Promise<void>
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  
  return date.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const Sidebar = ({
  sessions,
  currentSessionId,
  onSelectSession,
  onCreateSession,
  onDeleteSession,
}: SidebarProps) => {
  return (
    <div className="w-80 bg-white border-r border-gray-100 flex flex-col h-full">
      <div className="p-5 border-b border-gray-100">
        <h1 className="text-xl font-bold bg-gradient-to-r from-primary-600 to-accent-600 bg-clip-text text-transparent">
          MGAgent
        </h1>
        <p className="text-sm text-gray-500 mt-1">智能客服助手</p>
        
        <motion.button
          onClick={onCreateSession}
          className="mt-4 w-full py-3 bg-gradient-to-r from-primary-500 to-primary-600 text-white rounded-xl font-medium hover:from-primary-600 hover:to-primary-700 transition-all shadow-lg shadow-primary-500/25 flex items-center justify-center gap-2"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <Plus size={20} />
          新建对话
        </motion.button>
      </div>

      <div className="p-3 border-b border-gray-100">
        <button className="flex items-center gap-2 text-sm font-medium text-primary-600">
          <MessageSquare size={18} />
          对话
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        {sessions.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <MessageSquare size={32} className="mx-auto mb-3 opacity-50" />
            <p className="text-sm">暂无对话</p>
          </div>
        ) : (
          sessions.map((session) => (
            <motion.div
              key={session.id}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              whileHover={{ x: 4 }}
              className={`group p-3 rounded-xl cursor-pointer transition-all ${
                currentSessionId === session.id
                  ? 'bg-gradient-to-r from-primary-50 to-accent-50 border border-primary-200'
                  : 'bg-gray-50 hover:bg-gray-100 border border-transparent'
              }`}
              onClick={() => onSelectSession(session.id)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <h3 className={`font-medium text-sm truncate ${
                    currentSessionId === session.id ? 'text-primary-700' : 'text-gray-700'
                  }`}>
                    {session.title}
                  </h3>
                  <p className="text-xs text-gray-400 mt-1">
                    {formatDate(session.updated_at)}
                  </p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onDeleteSession(session.id)
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </div>
  )
}

export default Sidebar
