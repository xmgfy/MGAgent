import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { FileText, Trash2, Download, Upload, AlertCircle, Info, CheckCircle, Eye, X } from 'lucide-react'
import Button from '../components/Button'
import { knowledgeBaseApi } from '../api/client'
import type { DocumentInfo, PreviewResponse } from '../api/client'

const KnowledgeBase = () => {
  const [documents, setDocuments] = useState<DocumentInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)
  const [showClearConfirm, setShowClearConfirm] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadSuccess, setUploadSuccess] = useState(false)
  const [previewContent, setPreviewContent] = useState<PreviewResponse | null>(null)
  const [previewFilename, setPreviewFilename] = useState<string>('')
  const [previewLoading, setPreviewLoading] = useState(false)
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

  const handleDelete = async (filename: string) => {
    try {
      await knowledgeBaseApi.deleteDocument(filename)
      setDocuments(documents.filter(d => d.filename !== filename))
      setConfirmDelete(null)
    } catch (error) {
      console.error('Failed to delete document:', error)
    }
  }

  const handleClearAll = async () => {
    try {
      await knowledgeBaseApi.clear()
      setDocuments([])
      setShowClearConfirm(false)
    } catch (error) {
      console.error('Failed to clear knowledge base:', error)
    }
  }

  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    
    setUploading(true)
    setUploadSuccess(false)
    
    try {
      await knowledgeBaseApi.upload(file)
      setUploadSuccess(true)
      loadDocuments()
    } catch (error) {
      console.error('Failed to upload document:', error)
    } finally {
      setUploading(false)
      event.target.value = ''
      setTimeout(() => setUploadSuccess(false), 3000)
    }
  }

  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  const handleDownload = async (filename: string) => {
    try {
      await knowledgeBaseApi.download(filename)
    } catch (error) {
      console.error('Failed to download document:', error)
    }
  }

  const handlePreview = async (filename: string) => {
    setPreviewLoading(true)
    setPreviewFilename(filename)
    try {
      const content = await knowledgeBaseApi.preview(filename)
      setPreviewContent(content)
    } catch (error) {
      console.error('Failed to preview document:', error)
      setPreviewContent({ content: '预览失败，请稍后重试', type: 'error' })
    } finally {
      setPreviewLoading(false)
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
      case 'error':
        return '出错'
      default:
        return status
    }
  }

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
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                className="w-4 h-4 border-2 border-white border-t-transparent rounded-full mr-2"
              />
            ) : uploadSuccess ? (
              <CheckCircle size={18} className="mr-2" />
            ) : (
              <Upload size={18} className="mr-2" />
            )}
            {uploading ? '上传中...' : uploadSuccess ? '上传成功' : '上传文档'}
          </Button>
          <Button variant="danger" onClick={() => setShowClearConfirm(true)}>
            <Trash2 size={18} className="mr-2" />
            清空知识库
          </Button>
        </div>
      </div>

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
                  <th className="w-12">#</th>
                  <th>文件名</th>
                  <th className="w-24">类型</th>
                  <th className="w-20">大小</th>
                  <th className="w-20">状态</th>
                  <th className="w-24">操作</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc, index) => (
                  <motion.tr
                    key={doc.filename}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                  >
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
                        <motion.button
                          className="p-2 text-gray-400 hover:text-green-500 hover:bg-green-50 rounded-lg transition-colors"
                          whileHover={{ scale: 1.1 }}
                          whileTap={{ scale: 0.9 }}
                          onClick={() => handlePreview(doc.filename)}
                          title="预览"
                        >
                          <Eye size={16} />
                        </motion.button>
                        <motion.button
                          className="p-2 text-gray-400 hover:text-blue-500 hover:bg-blue-50 rounded-lg transition-colors"
                          whileHover={{ scale: 1.1 }}
                          whileTap={{ scale: 0.9 }}
                          onClick={() => handleDownload(doc.filename)}
                          title="下载"
                        >
                          <Download size={16} />
                        </motion.button>
                        <AnimatePresence>
                          {confirmDelete === doc.filename ? (
                            <motion.div
                              initial={{ opacity: 0, scale: 0.8 }}
                              animate={{ opacity: 1, scale: 1 }}
                              className="flex gap-1"
                            >
                              <Button
                                size="sm"
                                onClick={() => handleDelete(doc.filename)}
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
                              onClick={() => setConfirmDelete(doc.filename)}
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

      <AnimatePresence>
        {showClearConfirm && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => setShowClearConfirm(false)}
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
                确定要清空知识库中的所有文档吗？这将删除所有已上传的文件和对应的向量索引。
              </p>
              <div className="flex gap-3">
                <Button variant="secondary" className="flex-1" onClick={() => setShowClearConfirm(false)}>
                  取消
                </Button>
                <Button variant="danger" className="flex-1" onClick={handleClearAll}>
                  确认清空
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

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
          <h4 className="font-medium text-blue-800">提示</h4>
          <p className="text-sm text-blue-600 mt-1">
            文档上传后会自动进行向量化处理并存储到向量数据库中。支持的格式：PDF、TXT、DOCX、MD。
          </p>
        </div>
      </div>
    </div>
  )
}

export default KnowledgeBase