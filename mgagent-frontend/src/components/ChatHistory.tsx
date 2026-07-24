import { useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { MessageSquare, Search } from 'lucide-react'
import MessageBubble from './MessageBubble'
import TypingIndicator from './TypingIndicator'
import type { Message } from '@/api/client'

interface ChatHistoryProps {
  messages: Message[]
  isTyping: boolean
}

const ChatHistory = ({ messages, isTyping }: ChatHistoryProps) => {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: 'smooth',
    })
  }, [messages, isTyping])

  if (messages.length === 0 && !isTyping) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-400">
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="w-24 h-24 bg-gradient-to-br from-primary-100 to-accent-100 rounded-full flex items-center justify-center mb-6"
        >
          <MessageSquare size={48} className="text-primary-500" />
        </motion.div>
        <h2 className="text-xl font-semibold text-gray-700 mb-2">欢迎使用 MGAgent</h2>
        <p className="text-sm text-center max-w-md">
          您可以提问关于公司政策、产品文档、数据分析等问题。
          支持上传文档进行检索，也可以直接查询数据库。
        </p>
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mt-8 flex items-center gap-2 text-sm text-gray-500"
        >
          <Search size={16} />
          <span>输入问题开始对话</span>
        </motion.div>
      </div>
    )
  }

  return (
    <div ref={scrollRef} className="h-full overflow-y-auto p-6 space-y-4">
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}
      {isTyping && <TypingIndicator />}
    </div>
  )
}

export default ChatHistory