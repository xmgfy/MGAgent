import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Paperclip, PlusCircle } from 'lucide-react'

interface ChatInputProps {
  onSend: (message: string) => void
  onUpload: (message: string, file: File) => void
  isLoading: boolean
}

const ChatInput = ({ onSend, onUpload, isLoading }: ChatInputProps) => {
  const [message, setMessage] = useState('')
  const [showUpload, setShowUpload] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`
    }
  }, [message])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmedMessage = message.trim()
    if (trimmedMessage && !isLoading) {
      onSend(trimmedMessage)
      setMessage('')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      onUpload(message.trim(), file)
      setShowUpload(false)
    }
  }

  const handlePaste = (e: React.ClipboardEvent) => {
    const items = e.clipboardData?.items
    if (items) {
      for (const item of items) {
        if (item.type.indexOf('image') !== -1) {
          const file = item.getAsFile()
          if (file) {
            onUpload(message.trim(), file)
          }
        }
      }
    }
  }

  return (
    <div className="bg-white border-t border-gray-100 p-4">
      <AnimatePresence>
        {showUpload && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-3"
          >
            <label className="flex items-center justify-center gap-2 w-full py-3 border-2 border-dashed border-primary-200 rounded-xl text-primary-500 hover:border-primary-400 hover:bg-primary-50 cursor-pointer transition-colors">
              <PlusCircle size={20} />
              <span className="text-sm font-medium">点击或拖拽上传文件</span>
              <input
                type="file"
                accept=".pdf,.txt,.docx,.md"
                className="hidden"
                onChange={handleFileChange}
              />
            </label>
          </motion.div>
        )}
      </AnimatePresence>
      
      <form onSubmit={handleSubmit} className="flex items-end gap-3">
        <motion.button
          type="button"
          onClick={() => setShowUpload(!showUpload)}
          className="p-2.5 rounded-xl bg-gray-50 text-gray-500 hover:bg-gray-100 transition-colors flex-shrink-0"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Paperclip size={20} />
        </motion.button>
        
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            onPaste={handlePaste}
            placeholder="输入您的问题..."
            disabled={isLoading}
            className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400 resize-none disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            rows={1}
          />
        </div>
        
        <motion.button
          type="submit"
          disabled={!message.trim() || isLoading}
          className="p-3 rounded-xl bg-gradient-to-r from-primary-500 to-primary-600 text-white hover:from-primary-600 hover:to-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-primary-500/25 flex-shrink-0"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Send size={20} />
        </motion.button>
      </form>
    </div>
  )
}

export default ChatInput