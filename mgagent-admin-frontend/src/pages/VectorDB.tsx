import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Box, Search, Trash2, AlertCircle, ZoomIn } from 'lucide-react'
import Button from '../components/Button'
import { vectorDbApi } from '../api/client'
import type { VectorDBStats, VectorChunk } from '../api/client'

const VectorDB = () => {
  const [stats, setStats] = useState<VectorDBStats>({ total_chunks: 0, persist_directory: '', embedding_model: '' })
  const [chunks, setChunks] = useState<VectorChunk[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<VectorChunk[]>([])
  const [showSearchResults, setShowSearchResults] = useState(false)
  const [selectedChunk, setSelectedChunk] = useState<VectorChunk | null>(null)
  const [confirmClear, setConfirmClear] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [statsData, chunksData] = await Promise.all([
        vectorDbApi.getStats(),
        vectorDbApi.getChunks(20, 0),
      ])
      setStats(statsData)
      setChunks(chunksData)
    } catch (error) {
      console.error('Failed to load vector DB data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    try {
      const result = await vectorDbApi.search(searchQuery, 5)
      setSearchResults(result.results)
      setShowSearchResults(true)
    } catch (error) {
      console.error('Failed to search:', error)
    }
  }

  const handleClear = async () => {
    try {
      await vectorDbApi.clear()
      setChunks([])
      setStats({ ...stats, total_chunks: 0 })
      setConfirmClear(false)
    } catch (error) {
      console.error('Failed to clear vector DB:', error)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-green-100 rounded-xl">
            <Box size={20} className="text-green-500" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-800">向量数据库</h2>
            <p className="text-sm text-gray-500">管理和查询向量数据库中的数据</p>
          </div>
        </div>
        <Button variant="danger" onClick={() => setConfirmClear(true)}>
          <Trash2 size={18} />
          清空向量库
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-xl p-4 shadow-sm border border-gray-100"
        >
          <p className="text-sm text-gray-500 mb-1">总向量块数</p>
          <p className="text-2xl font-bold text-gray-800">{stats.total_chunks}</p>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-xl p-4 shadow-sm border border-gray-100"
        >
          <p className="text-sm text-gray-500 mb-1">嵌入模型</p>
          <p className="text-lg font-semibold text-gray-800">{stats.embedding_model}</p>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-xl p-4 shadow-sm border border-gray-100"
        >
          <p className="text-sm text-gray-500 mb-1">存储目录</p>
          <p className="text-sm text-gray-800 truncate">{stats.persist_directory}</p>
        </motion.div>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="搜索向量内容..."
              className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400"
            />
          </div>
          <Button onClick={handleSearch}>
            <Search size={18} />
            搜索
          </Button>
        </div>
      </div>

      <AnimatePresence>
        {showSearchResults && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden"
          >
            <div className="p-4 border-b border-gray-100 bg-blue-50">
              <h3 className="font-medium text-blue-800">搜索结果</h3>
            </div>
            <div className="divide-y divide-gray-100">
              {searchResults.map((chunk, index) => (
                <motion.div
                  key={chunk.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="p-4 hover:bg-gray-50 cursor-pointer"
                  onClick={() => setSelectedChunk(chunk)}
                >
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-xs text-gray-400">匹配 #{index + 1}</span>
                    <ZoomIn size={14} className="text-gray-400" />
                  </div>
                  <p className="text-sm text-gray-700 line-clamp-2">{chunk.content}</p>
                </motion.div>
              ))}
              {searchResults.length === 0 && (
                <div className="p-8 text-center text-gray-400">
                  <p>未找到匹配的结果</p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-4 border-b border-gray-100">
          <h3 className="font-medium text-gray-800">向量块列表</h3>
          <p className="text-sm text-gray-500">显示前20个向量块</p>
        </div>
        {loading ? (
          <div className="flex items-center justify-center h-48">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              className="w-8 h-8 border-4 border-primary-200 border-t-primary-500 rounded-full"
            />
          </div>
        ) : chunks.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-400">
            <Box size={48} className="mb-4 opacity-50" />
            <p className="text-lg font-medium">向量库为空</p>
            <p className="text-sm">上传文档后会自动生成向量索引</p>
          </div>
        ) : (
          <div className="max-h-[500px] overflow-y-auto">
            {chunks.map((chunk) => (
              <motion.div
                key={chunk.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="p-4 border-b border-gray-100 hover:bg-gray-50 cursor-pointer"
                onClick={() => setSelectedChunk(chunk)}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-gray-400 font-mono">{chunk.id.slice(0, 8)}...</span>
                  {chunk.metadata.source && (
                    <span className="text-xs text-gray-500">{chunk.metadata.source}</span>
                  )}
                </div>
                <p className="text-sm text-gray-700 line-clamp-2">{chunk.content}</p>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      <AnimatePresence>
        {selectedChunk && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => setSelectedChunk(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-2xl p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto"
              onClick={e => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-800">向量块详情</h3>
                <Button variant="ghost" size="sm" onClick={() => setSelectedChunk(null)}>
                  关闭
                </Button>
              </div>
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-gray-500 mb-1">ID</p>
                  <p className="text-sm font-mono text-gray-800">{selectedChunk.id}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 mb-1">内容</p>
                  <pre className="bg-gray-50 p-4 rounded-xl text-sm text-gray-700 whitespace-pre-wrap max-h-[300px] overflow-y-auto">
                    {selectedChunk.content}
                  </pre>
                </div>
                <div>
                  <p className="text-sm text-gray-500 mb-1">元数据</p>
                  <pre className="bg-gray-50 p-4 rounded-xl text-sm text-gray-700">
                    {JSON.stringify(selectedChunk.metadata, null, 2)}
                  </pre>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {confirmClear && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => setConfirmClear(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-2xl p-6 w-full max-w-md"
              onClick={e => e.stopPropagation()}
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                  <AlertCircle size={24} className="text-red-500" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-800">确认清空</h3>
                  <p className="text-sm text-gray-500">此操作不可撤销</p>
                </div>
              </div>
              <p className="text-gray-600 mb-6">
                确定要清空向量数据库吗？这将删除所有向量索引，但不会删除原始文档。
              </p>
              <div className="flex gap-3">
                <Button variant="secondary" className="flex-1" onClick={() => setConfirmClear(false)}>
                  取消
                </Button>
                <Button variant="danger" className="flex-1" onClick={handleClear}>
                  确认清空
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default VectorDB