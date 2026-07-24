import { motion } from 'framer-motion'
import { User, Bot } from 'lucide-react'
import type { Message } from '@/api/client'

interface MessageBubbleProps {
  message: Message
}

const MessageBubble = ({ message }: MessageBubbleProps) => {
  const isUser = message.role === 'user'

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
    >
      <div
        className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
          isUser
            ? 'bg-gradient-to-br from-primary-500 to-accent-500 text-white'
            : 'bg-gray-100 text-gray-500'
        }`}
      >
        {isUser ? <User size={20} /> : <Bot size={20} />}
      </div>
      
      <div
        className={`max-w-[70%] ${
          isUser ? 'items-end' : 'items-start'
        }`}
      >
        <div
          className={`px-4 py-3 rounded-2xl ${
            isUser
              ? 'bg-gradient-to-r from-primary-500 to-primary-600 text-white rounded-br-md'
              : 'bg-white text-gray-800 rounded-bl-md shadow-card'
          }`}
        >
          <p className="text-sm leading-relaxed whitespace-pre-wrap">
            {message.content}
          </p>
        </div>
        <p className="text-xs text-gray-400 mt-1 px-1">
          {(() => {
            const date = new Date(message.created_at)
            return date.toLocaleString('zh-CN', {
              month: '2-digit',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit',
            })
          })()}
        </p>
      </div>
    </motion.div>
  )
}

export default MessageBubble