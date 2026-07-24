import { motion } from 'framer-motion'
import { Settings, Trash2, Bot } from 'lucide-react'

interface ChatHeaderProps {
  title: string
  onClear: () => void
}

const ChatHeader = ({ title, onClear }: ChatHeaderProps) => {
  return (
    <div className="flex items-center justify-between px-6 py-4 bg-white border-b border-gray-100">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-gradient-to-br from-primary-100 to-accent-100 rounded-xl flex items-center justify-center">
          <Bot size={20} className="text-primary-600" />
        </div>
        <div>
          <h2 className="font-semibold text-gray-800">{title}</h2>
          <p className="text-xs text-gray-400">MGAgent 智能客服助手</p>
        </div>
      </div>
      
      <div className="flex items-center gap-2">
        <motion.button
          className="p-2 rounded-xl text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Settings size={20} />
        </motion.button>
        <motion.button
          onClick={onClear}
          className="p-2 rounded-xl text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Trash2 size={20} />
        </motion.button>
      </div>
    </div>
  )
}

export default ChatHeader