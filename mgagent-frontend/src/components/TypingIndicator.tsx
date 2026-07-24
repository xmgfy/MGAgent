import { motion } from 'framer-motion'
import { Bot } from 'lucide-react'

const TypingIndicator = () => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex gap-3"
    >
      <div className="w-10 h-10 rounded-full bg-gray-100 text-gray-500 flex items-center justify-center flex-shrink-0">
        <Bot size={20} />
      </div>
      <div className="bg-white rounded-2xl rounded-bl-md shadow-card px-4 py-3">
        <div className="flex gap-1.5">
          <motion.div
            className="w-2 h-2 bg-gray-400 rounded-full typing-dot"
            animate={{ scale: [0.8, 1.2, 0.8] }}
            transition={{ duration: 1.4, repeat: Infinity }}
          />
          <motion.div
            className="w-2 h-2 bg-gray-400 rounded-full typing-dot"
            animate={{ scale: [0.8, 1.2, 0.8] }}
            transition={{ duration: 1.4, repeat: Infinity, delay: 0.2 }}
          />
          <motion.div
            className="w-2 h-2 bg-gray-400 rounded-full typing-dot"
            animate={{ scale: [0.8, 1.2, 0.8] }}
            transition={{ duration: 1.4, repeat: Infinity, delay: 0.4 }}
          />
        </div>
      </div>
    </motion.div>
  )
}

export default TypingIndicator