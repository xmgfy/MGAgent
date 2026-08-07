import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { FileText, Trash2, Download, Upload, AlertCircle, Info, CheckCircle, Eye, X, Zap, Loader2 } from 'lucide-react'
import Button from '../components/Button'
import { knowledgeBaseApi } from '../api/client'
import type { DocumentInfo, PreviewResponse } from '../api/client'

const KnowledgeBase = () => {
  const [documents, setDocuments] = useState<DocumentInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadSuccess, setUploadSuccess] = useState(false)
  const [previewContent, setPreviewContent] = useState<PreviewResponse | null>(null)
  const [previewFilename, setPreviewFilename] = useState<string>('')
  const [previewLoading, setPreviewLoading] = useState(false)
  const [indexingIds, setIndexingIds] = useState<Set<string>>(new Set())
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [batchDeleting, setBatchDeleting] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      setLoading(true)
      const data = await knowledgeBaseApi.getDocuments()
      setDocuments(data)
    } catch (error) {
      console.error('Failed to load documents:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (documentId: string) => {
    try {
      await knowledgeBaseApi.deleteDocument(documentId)
      setDocuments(documents.filter(d => d.document_id !== documentId))
      setSelectedIds(prev => {
        const next = new Set(prev)
        next.delete(documentId)
        return next
      })
      setConfirmDelete(null)
    } catch (error) {
      console.error('Failed to delete document:', error)
    }
  }

  const handleBatchDelete = async () => {
    if (selectedIds.size === 0) return
    setBatchDeleting(true)
    try {
      const ids = Array.from(selectedIds)
      await knowledgeBaseApi.batchDelete(ids)
      setDocuments(documents.filter(d => !selectedIds.has(d.document_id!)))
      setSelectedIds(new Set())
    } catch (error) {
      console.error('Failed to batch delete documents:', error)
    } finally {
      setBatchDeleting(false)
    }
  }

  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setUploading(true)
    setUploadProgress(0)
    setUploadSuccess(false)

    try {
      await knowledgeBaseApi.upload(file, (percent) => {
        setUploadProgress(percent)
      })
      setUploadSuccess(true)
      await loadDocuments()
    } catch (error) {
      console.error('Failed to upload document:', error)
    } finally {
      setUploading(false)
      event.target.value = ''
      setTimeout(() => {
        setUploadSuccess(false)
        setUploadProgress(0)
      }, 2000)
    }
  }

  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  // 点击闪电图标，使用全局默认 Embedding 模型进行索引
  const handleIndexClick = async (doc: DocumentInfo) => {
    const docId = doc.document_id!
    setIndexingIds(prev => new Set(prev).add(docId))

    try {
      await knowledgeBaseApi.indexDocument(docId)
      setDocuments(docs =>
        docs.map(d =>
          d.document_id === docId ? { ...d, status: 'indexed' } : d
        )
      )
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || error.message || '索引失败'
      alert(`索引失败: ${errorMsg}`)
    } finally {
      setIndexingIds(prev => {
        const next = new Set(prev)
        next.delete(docId)
        return next
      })
    }
  }

  const handleDownload = async (documentId: string, filename: string) => {
    try {
      await knowledgeBaseApi.download(documentId, filename)
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || error.message || '下载失败'
      alert(`下载失败: ${errorMsg}`)
    }
  }

  const handlePreview = async (documentId: string, filename: string) => {
    setPreviewLoading(true)
    setPreviewFilename(filename)
    try {
      const content = await knowledgeBaseApi.preview(documentId)
      setPreviewContent(content)
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || error.message || '预览失败'
      setPreviewContent({ content: `预览失败: ${errorMsg}`, type: 'error' })
    } finally {
      setPreviewLoading(false)
    }
  }

  const toggleSelect = (documentId: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(documentId)) {
        next.delete(documentId)
      } else {
        next.add(documentId)
      }
      return next
    })
  }

  const toggleSelectAll = () => {
    if (selectedIds.size === documents.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(documents.map(d => d.document_id!).filter(Boolean)))
    }
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const getFileIcon = (fileType: string) => {
    switch (fileType) {
      case '.pdf':
        return <FileText size={16} className="text-red-500" />
      case '.docx':
        return <FileText size={16} className="text-blue-500" />
      case '.md':
        return <FileText size={16} className="text-gray-500" />
      default:
        return <FileText size={16} className="text-gray-400" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'indexed':
        return 'bg-green-100 text-green-600'
      case 'uploaded':
        return 'bg-yellow-100 text-yellow-600'
      case 'indexing':
        return 'bg-blue-100 text-blue-600'
      case 'error':
        return 'bg-red-100 text-red-600'
      default:
        return 'bg-gray-100 text-gray-600'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'indexed':
        return '已索引'
      case 'uploaded':
        return '已上传'
      case 'indexing':
        return '索引中'
      case 'error':
        return '出错'
      default:
        return status
    }
  }

  const allSelected = documents.length > 0 && selectedIds.size === documents.length

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 rounded-xl">
            <FileText size={20} className="text-blue-500" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-800">文档列表</h2>
            <p className="text-sm text-gray-500">管理知识库中的文档文件</p>
          </div>
        </div>
        <div className="flex gap-3">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.txt,.docx,.md"
            onChange={handleUpload}
            className="hidden"
          />
          <Button variant="secondary" onClick={handleUploadClick} disabled={uploading}>
            {uploading ? (
              <Loader2 size={18} className="mr-2 animate-spin" />
            ) : uploadSuccess ? (
              <CheckCircle size={18} className="mr-2" />
            ) : (
              <Upload size={18} className="mr-2" />
            )}
            {uploading ? '上传中...' : uploadSuccess ? '上传成功' : '上传文档'}
          </Button>
          {selectedIds.size > 0 && (
            <Button
              variant="danger"
              onClick={handleBatchDelete}
              disabled={batchDeleting}
            >
              {batchDeleting ? (
                <Loader2 size={18} className="mr-2 animate-spin" />
              ) : (
                <Trash2 size={18} className="mr-2" />
              )}
              {batchDeleting ? '删除中...' : `删除选中 (${selectedIds.size})`}
            </Button>
          )}
        </div>
      </div>

      {/* 上传进度条 */}
      <AnimatePresence>
        {uploading && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-white rounded-xl border border-gray-100 overflow-hidden"
          >
            <div className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">上传中...</span>
                <span className="text-sm text-gray-500">{uploadProgress}%</span>
              </div>
              <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-blue-500 rounded-full"
                  animate={{ width: `${uploadProgress}%` }}
                  transition={{ ease: 'easeOut' }}
                />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-48">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              className="w-8 h-8 border-4 border-primary-200 border-t-primary-500 rounded-full"
            />
          </div>
        ) : documents.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-400">
            <FileText size={48} className="mb-4 opacity-50" />
            <p className="text-lg font-medium">暂无文档</p>
            <p className="text-sm">点击上传按钮添加文档到知识库</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table>
              <thead>
                <tr>
                  <th className="w-12">
                    <input
                      type="checkbox"
                      checked={allSelected}
                      onChange={toggleSelectAll}
                      className="w-4 h-4 rounded border-gray-300 text-blue-500 focus:ring-blue-400"
                    />
                  </th>
                  <th className="w-12">#</th>
                  <th>文件名</th>
                  <th className="w-24">类型</th>
                  <th className="w-20">大小</th>
                  <th className="w-20">状态</th>
                  <th className="w-32">操作</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc, index) => (
                  <motion.tr
                    key={doc.document_id || doc.filename}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                  >
                    <td>
                      <input
                        type="checkbox"
                        checked={selectedIds.has(doc.document_id!)}
                        onChange={() => toggleSelect(doc.document_id!)}
                        className="w-4 h-4 rounded border-gray-300 text-blue-500 focus:ring-blue-400"
                      />
                    </td>
                    <td className="text-gray-400">{index + 1}</td>
                    <td className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                        {getFileIcon(doc.file_type)}
                      </div>
                      <span className="font-medium text-gray-800">{doc.filename}</span>
                    </td>
                    <td className="text-gray-500">{doc.file_type}</td>
                    <td className="text-gray-500">{formatSize(doc.file_size)}</td>
                    <td>
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(doc.status)}`}>
                        {getStatusText(doc.status)}
                      </span>
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                        {/* 已上传状态显示索引按钮 */}
                        {(doc.status === 'uploaded' || doc.status === 'error') && (
                          <motion.button
                            className="p-2 text-gray-400 hover:text-purple-500 hover:bg-purple-50 rounded-lg transition-colors"
                            whileHover={{ scale: 1.1 }}
                            whileTap={{ scale: 0.9 }}
                            onClick={() => handleIndexClick(doc)}
                            disabled={indexingIds.has(doc.document_id!)}
                            title="加载到向量数据库"
                          >
                            {indexingIds.has(doc.document_id!) ? (
                              <Loader2 size={16} className="animate-spin" />
                            ) : (
                              <Zap size={16} />
                            )}
                          </motion.button>
                        )}
                        <motion.button
                          className="p-2 text-gray-400 hover:text-green-500 hover:bg-green-50 rounded-lg transition-colors"
                          whileHover={{ scale: 1.1 }}
                          whileTap={{ scale: 0.9 }}
                          onClick={() => handlePreview(doc.document_id!, doc.filename)}
                          title="预览"
                        >
                          <Eye size={16} />
                        </motion.button>
                        <motion.button
                          className="p-2 text-gray-400 hover:text-blue-500 hover:bg-blue-50 rounded-lg transition-colors"
                          whileHover={{ scale: 1.1 }}
                          whileTap={{ scale: 0.9 }}
                          onClick={() => handleDownload(doc.document_id!, doc.filename)}
                          title="下载"
                        >
                          <Download size={16} />
                        </motion.button>
                        <AnimatePresence>
                          {confirmDelete === doc.document_id ? (
                            <motion.div
                              initial={{ opacity: 0, scale: 0.8 }}
                              animate={{ opacity: 1, scale: 1 }}
                              className="flex gap-1"
                            >
                              <Button
                                size="sm"
                                onClick={() => handleDelete(doc.document_id!)}
                              >
                                确认
                              </Button>
                              <Button
                                size="sm"
                                variant="secondary"
                                onClick={() => setConfirmDelete(null)}
                              >
                                取消
                              </Button>
                            </motion.div>
                          ) : (
                            <motion.button
                              className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                              whileHover={{ scale: 1.1 }}
                              whileTap={{ scale: 0.9 }}
                              onClick={() => setConfirmDelete(doc.document_id!)}
                              title="删除"
                            >
                              <Trash2 size={16} />
                            </motion.button>
                          )}
                        </AnimatePresence>
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 预览弹窗 */}
      <AnimatePresence>
        {previewContent && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => { setPreviewContent(null); setPreviewFilename(''); }}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden"
              onClick={e => e.stopPropagation()}
            >
              <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                    <Eye size={16} className="text-gray-500" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-800">文档预览</h3>
                    <p className="text-sm text-gray-500">{previewFilename}</p>
                  </div>
                </div>
                <motion.button
                  onClick={() => { setPreviewContent(null); setPreviewFilename(''); }}
                  className="p-2 rounded-lg hover:bg-gray-100 text-gray-400 transition-colors"
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                >
                  <X size={20} />
                </motion.button>
              </div>
              <div className="p-6 overflow-y-auto max-h-[60vh]">
                {previewLoading ? (
                  <div className="flex items-center justify-center h-48">
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                      className="w-8 h-8 border-4 border-primary-200 border-t-primary-500 rounded-full"
                    />
                  </div>
                ) : previewContent.type === 'error' ? (
                  <div className="flex items-center justify-center h-48 text-red-500">
                    <AlertCircle size={24} className="mr-2" />
                    <span>{previewContent.content}</span>
                  </div>
                ) : (
                  <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono leading-relaxed">
                    {previewContent.content}
                  </pre>
                )}
                {previewContent.type === 'text' && previewContent.truncated && (
                  <p className="text-xs text-gray-400 mt-4 text-center">内容过长，仅显示前5000字符</p>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="bg-blue-50 rounded-2xl p-4 flex items-start gap-3">
        <Info size={20} className="text-blue-500 flex-shrink-0 mt-0.5" />
        <div>
          <h4 className="font-medium text-blue-800">使用说明</h4>
          <p className="text-sm text-blue-600 mt-1">
            文档上传后状态为「已上传」，点击闪电图标选择 Embedding 模型并加载到向量数据库后变为「已索引」。
            支持勾选多个文档批量删除。支持的格式：PDF、TXT、DOCX、MD。
          </p>
        </div>
      </div>
    </div>
  )
}

export default KnowledgeBase
