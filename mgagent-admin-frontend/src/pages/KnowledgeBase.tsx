import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { FileText, Trash2, Download, Upload, AlertCircle, Info, CheckCircle, Eye, X, Zap, Loader2, Plus, Save, Trash2 as Trash2Icon, Search, Target } from 'lucide-react'
import Button from '../components/Button'
import { knowledgeBaseApi } from '../api/client'
import type { DocumentInfo, PreviewResponse, KnowledgeBase, RetrieveTestResponse, RetrievalLogEntry, EvalRunResponse, EvalResultEntry } from '../api/client'

type KbFormMode = 'create' | 'edit'

interface KbFormState {
  id?: string
  name: string
  description: string
  chunk_size: number
  chunk_overlap: number
  chunk_separator: string
  retrieve_limit: number
  similarity_threshold: string
  enable_rerank: boolean
  rerank_top_n: number
  rerank_score_threshold: string
  enable_hybrid: boolean
  hybrid_alpha: number
  is_active: boolean
}

const defaultKbForm: KbFormState = {
  name: '',
  description: '',
  chunk_size: 512,
  chunk_overlap: 50,
  chunk_separator: '',
  retrieve_limit: 5,
  similarity_threshold: '',
  enable_rerank: false,
  rerank_top_n: 3,
  rerank_score_threshold: '',
  enable_hybrid: false,
  hybrid_alpha: 0.7,
  is_active: true,
}

const KnowledgeBasePage = () => {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([])
  const [activeKbId, setActiveKbId] = useState<string | null>(null)
  const [loadingKbs, setLoadingKbs] = useState(true)

  const [documents, setDocuments] = useState<DocumentInfo[]>([])
  const [loadingDocs, setLoadingDocs] = useState(true)
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadSuccess, setUploadSuccess] = useState(false)
  const [indexingIds, setIndexingIds] = useState<Set<string>>(new Set())
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [batchDeleting, setBatchDeleting] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [previewContent, setPreviewContent] = useState<PreviewResponse | null>(null)
  const [previewFilename, setPreviewFilename] = useState<string>('')
  const [previewLoading, setPreviewLoading] = useState(false)

  const [kbFormOpen, setKbFormOpen] = useState(false)
  const [kbFormMode, setKbFormMode] = useState<KbFormMode>('create')
  const [kbForm, setKbForm] = useState<KbFormState>(defaultKbForm)
  const [kbSaving, setKbSaving] = useState(false)
  const [confirmKbDelete, setConfirmKbDelete] = useState(false)

  const [configSaving, setConfigSaving] = useState(false)
  const [configForm, setConfigForm] = useState<KbFormState>(defaultKbForm)
  const [configDirty, setConfigDirty] = useState(false)

  const [testModalOpen, setTestModalOpen] = useState(false)
  const [testQuery, setTestQuery] = useState('')
  const [testTopK, setTestTopK] = useState(5)
  const [testThreshold, setTestThreshold] = useState('')
  const [testLoading, setTestLoading] = useState(false)
  const [testResult, setTestResult] = useState<RetrieveTestResponse | null>(null)
  const [testError, setTestError] = useState<string | null>(null)

  const [logModalOpen, setLogModalOpen] = useState(false)
  const [logLoading, setLogLoading] = useState(false)
  const [retrievalLogs, setRetrievalLogs] = useState<RetrievalLogEntry[]>([])

  const [evalModalOpen, setEvalModalOpen] = useState(false)
  const [evalLoading, setEvalLoading] = useState(false)
  const [evalResult, setEvalResult] = useState<EvalRunResponse | null>(null)
  const [evalHistory, setEvalHistory] = useState<EvalResultEntry[]>([])
  const [evalError, setEvalError] = useState<string | null>(null)
  const [evalDataset, setEvalDataset] = useState<any[]>([])
  const [newEvalQuery, setNewEvalQuery] = useState('')
  const [newEvalDocIds, setNewEvalDocIds] = useState('')
  const [datasetLoading, setDatasetLoading] = useState(false)

  useEffect(() => {
    loadKnowledgeBases()
  }, [])

  useEffect(() => {
    if (activeKbId === null && knowledgeBases.length > 0) {
      setActiveKbId(knowledgeBases[0].id)
    }
  }, [knowledgeBases, activeKbId])

  useEffect(() => {
    loadDocuments()
  }, [])

  useEffect(() => {
    const kb = knowledgeBases.find(k => k.id === activeKbId)
    if (kb) {
      setConfigForm({
        id: kb.id,
        name: kb.name,
        description: kb.description || '',
        chunk_size: kb.chunk_size,
        chunk_overlap: kb.chunk_overlap,
        chunk_separator: kb.chunk_separator || '',
        retrieve_limit: kb.retrieve_limit,
        similarity_threshold: kb.similarity_threshold != null ? String(kb.similarity_threshold) : '',
        enable_rerank: kb.enable_rerank,
        rerank_top_n: kb.rerank_top_n,
        rerank_score_threshold: kb.rerank_score_threshold != null ? String(kb.rerank_score_threshold) : '',
        enable_hybrid: kb.enable_hybrid,
        hybrid_alpha: kb.hybrid_alpha,
        is_active: kb.is_active,
      })
      setConfigDirty(false)
    }
  }, [activeKbId, knowledgeBases])

  const loadKnowledgeBases = async () => {
    try {
      setLoadingKbs(true)
      const data = await knowledgeBaseApi.listKnowledgeBases()
      setKnowledgeBases(data)
      if (data.length > 0 && !activeKbId) {
        setActiveKbId(data[0].id)
      }
    } catch (error) {
      console.error('Failed to load knowledge bases:', error)
    } finally {
      setLoadingKbs(false)
    }
  }

  const loadDocuments = async () => {
    try {
      setLoadingDocs(true)
      const data = await knowledgeBaseApi.getDocuments()
      setDocuments(data)
    } catch (error) {
      console.error('Failed to load documents:', error)
    } finally {
      setLoadingDocs(false)
    }
  }

  const activeKb = knowledgeBases.find(k => k.id === activeKbId) || null

  // ---------- KB create / edit / delete ----------

  const openCreateKbModal = () => {
    setKbFormMode('create')
    setKbForm(defaultKbForm)
    setKbFormOpen(true)
  }

  const openEditKbModal = () => {
    if (!activeKb) return
    setKbFormMode('edit')
    setKbForm({
      id: activeKb.id,
      name: activeKb.name,
      description: activeKb.description || '',
      chunk_size: activeKb.chunk_size,
      chunk_overlap: activeKb.chunk_overlap,
      chunk_separator: activeKb.chunk_separator || '',
      retrieve_limit: activeKb.retrieve_limit,
      similarity_threshold: activeKb.similarity_threshold != null ? String(activeKb.similarity_threshold) : '',
      enable_rerank: activeKb.enable_rerank,
      rerank_top_n: activeKb.rerank_top_n,
      rerank_score_threshold: activeKb.rerank_score_threshold != null ? String(activeKb.rerank_score_threshold) : '',
      enable_hybrid: activeKb.enable_hybrid,
      hybrid_alpha: activeKb.hybrid_alpha,
      is_active: activeKb.is_active,
    })
    setKbFormOpen(true)
  }

  const handleKbSubmit = async () => {
    if (!kbForm.name.trim()) {
      alert('请输入知识库名称')
      return
    }
    try {
      setKbSaving(true)
      const payload = {
        name: kbForm.name,
        description: kbForm.description || undefined,
        chunk_size: kbForm.chunk_size,
        chunk_overlap: kbForm.chunk_overlap,
        chunk_separator: kbForm.chunk_separator || undefined,
        retrieve_limit: kbForm.retrieve_limit,
        similarity_threshold: kbForm.similarity_threshold === '' ? undefined : Number(kbForm.similarity_threshold),
        enable_rerank: kbForm.enable_rerank,
        rerank_top_n: kbForm.rerank_top_n,
        rerank_score_threshold: kbForm.rerank_score_threshold === '' ? undefined : Number(kbForm.rerank_score_threshold),
        enable_hybrid: kbForm.enable_hybrid,
        hybrid_alpha: kbForm.hybrid_alpha,
        is_active: kbForm.is_active,
      }

      if (kbFormMode === 'create') {
        const created = await knowledgeBaseApi.createKnowledgeBase(payload)
        setKnowledgeBases(prev => [...prev, created])
        setActiveKbId(created.id)
      } else if (kbForm.id) {
        const updated = await knowledgeBaseApi.updateKnowledgeBase(kbForm.id, payload)
        setKnowledgeBases(prev => prev.map(k => k.id === updated.id ? updated : k))
      }
      setKbFormOpen(false)
    } catch (error: any) {
      const msg = error.response?.data?.detail || error.message || '操作失败'
      alert(`保存知识库失败: ${msg}`)
    } finally {
      setKbSaving(false)
    }
  }

  const handleDeleteKb = async () => {
    if (!activeKb || activeKb.name.toLowerCase() === 'default') {
      alert('Default 知识库不可删除')
      return
    }
    try {
      await knowledgeBaseApi.deleteKnowledgeBase(activeKb.id)
      setKnowledgeBases(prev => prev.filter(k => k.id !== activeKb.id))
      setActiveKbId(null)
      setConfirmKbDelete(false)
    } catch (error: any) {
      const msg = error.response?.data?.detail || error.message || '删除失败'
      alert(`删除知识库失败: ${msg}`)
    }
  }

  // ---------- Inline config save ----------

  const handleConfigChange = (field: keyof KbFormState, value: any) => {
    setConfigForm(prev => ({ ...prev, [field]: value }))
    setConfigDirty(true)
  }

  const handleSaveConfig = async () => {
    if (!activeKb || !configForm.id) return
    try {
      setConfigSaving(true)
      const payload = {
        name: configForm.name,
        description: configForm.description || undefined,
        chunk_size: configForm.chunk_size,
        chunk_overlap: configForm.chunk_overlap,
        chunk_separator: configForm.chunk_separator || undefined,
        retrieve_limit: configForm.retrieve_limit,
        similarity_threshold: configForm.similarity_threshold === '' ? undefined : Number(configForm.similarity_threshold),
        enable_rerank: configForm.enable_rerank,
        rerank_top_n: configForm.rerank_top_n,
        rerank_score_threshold: configForm.rerank_score_threshold === '' ? undefined : Number(configForm.rerank_score_threshold),
        enable_hybrid: configForm.enable_hybrid,
        hybrid_alpha: configForm.hybrid_alpha,
        is_active: configForm.is_active,
      }
      const updated = await knowledgeBaseApi.updateKnowledgeBase(configForm.id, payload)
      setKnowledgeBases(prev => prev.map(k => k.id === updated.id ? updated : k))
      setConfigDirty(false)
    } catch (error: any) {
      const msg = error.response?.data?.detail || error.message || '保存失败'
      alert(`保存配置失败: ${msg}`)
    } finally {
      setConfigSaving(false)
    }
  }

  // ---------- Document operations ----------

  const handleDelete = async (documentId: string) => {
    try {
      await knowledgeBaseApi.deleteDocument(documentId)
      setDocuments(docs => docs.filter(d => d.document_id !== documentId))
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
      setDocuments(docs => docs.filter(d => !selectedIds.has(d.document_id!)))
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
      await knowledgeBaseApi.upload(file, activeKbId ?? undefined, (percent) => {
        setUploadProgress(percent)
      })
      setUploadSuccess(true)
      await loadDocuments()
      await loadKnowledgeBases()
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

  const handleRetrieveTest = async () => {
    if (!activeKbId || !testQuery.trim()) return
    setTestLoading(true)
    setTestError(null)
    setTestResult(null)
    try {
      const threshold = testThreshold.trim() ? parseFloat(testThreshold) : undefined
      const result = await knowledgeBaseApi.retrieveTest(
        activeKbId,
        testQuery.trim(),
        testTopK,
        isNaN(threshold as number) ? undefined : threshold
      )
      setTestResult(result)
    } catch (error: any) {
      const msg = error.response?.data?.detail || error.message || '召回测试失败'
      setTestError(msg)
    } finally {
      setTestLoading(false)
    }
  }

  const handleOpenLogs = async () => {
    setLogModalOpen(true)
    setLogLoading(true)
    try {
      const logs = await knowledgeBaseApi.fetchRetrievalLogs(activeKbId ?? undefined, 50)
      setRetrievalLogs(logs)
    } catch {
      setRetrievalLogs([])
    } finally {
      setLogLoading(false)
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
  const isDefaultKb = activeKb?.name.toLowerCase() === 'default'

  // ---------- Helpers ----------

  const renderField = (
    label: string,
    children: React.ReactNode,
    help?: string
  ) => (
    <div className="space-y-1.5">
      <label className="block text-xs font-medium text-gray-600">{label}</label>
      {children}
      {help && <p className="text-xs text-gray-400">{help}</p>}
    </div>
  )

  const inputCls = "w-full px-3 py-2 rounded-lg border border-gray-200 bg-white text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-primary-300 focus:border-primary-400 transition"

  return (
    <div className="h-full flex flex-col">
      {/* Page title */}
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 bg-gradient-to-br from-primary-100 to-purple-100 rounded-xl">
          <FileText size={20} className="text-primary-600" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-gray-800">知识库管理</h2>
          <p className="text-sm text-gray-500">管理多个知识库及其文档文件</p>
        </div>
      </div>

      <div className="flex gap-4 flex-1 min-h-0">
        {/* ============ LEFT SIDEBAR ============ */}
        <aside className="w-60 flex-shrink-0 bg-white rounded-2xl shadow-sm border border-gray-100 flex flex-col overflow-hidden">
          <div className="p-3 border-b border-gray-100 flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">知识库</span>
            <Button size="sm" variant="primary" onClick={openCreateKbModal} className="px-2 py-1">
              <Plus size={14} /> 新建
            </Button>
          </div>

          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {loadingKbs ? (
              <div className="flex items-center justify-center py-8">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  className="w-6 h-6 border-4 border-primary-200 border-t-primary-500 rounded-full"
                />
              </div>
            ) : knowledgeBases.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-gray-400">
                <FileText size={32} className="mb-2 opacity-40" />
                <p className="text-xs">暂无知识库</p>
              </div>
            ) : (
              knowledgeBases.map(kb => {
                const isActive = kb.id === activeKbId
                return (
                  <motion.button
                    key={kb.id}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setActiveKbId(kb.id)}
                    className={`w-full text-left px-3 py-2.5 rounded-xl flex items-center justify-between transition-all ${
                      isActive
                        ? 'bg-gradient-to-r from-primary-500 to-purple-500 text-white shadow-md shadow-primary-500/25'
                        : 'hover:bg-gray-50 text-gray-700'
                    }`}
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <div className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 ${
                        isActive ? 'bg-white/20' : 'bg-gray-100'
                      }`}>
                        <FileText size={14} className={isActive ? 'text-white' : 'text-gray-500'} />
                      </div>
                      <span className="text-sm font-medium truncate">{kb.name}</span>
                    </div>
                    {(kb.document_count ?? 0) > 0 && (
                      <span className={`text-xs px-2 py-0.5 rounded-full flex-shrink-0 ${
                        isActive ? 'bg-white/25 text-white' : 'bg-gray-100 text-gray-500'
                      }`}>
                        {kb.document_count}
                      </span>
                    )}
                  </motion.button>
                )
              })
            )}
          </div>
        </aside>

        {/* ============ RIGHT MAIN AREA ============ */}
        <main className="flex-1 min-w-0 overflow-y-auto space-y-4 pr-1">
          {activeKb ? (
            <>
              {/* ---- KB Config Card ---- */}
              <section className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-1.5 bg-primary-100 rounded-lg">
                      <FileText size={16} className="text-primary-500" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-800">知识库配置</h3>
                      <p className="text-xs text-gray-500">分块、召回与重排序参数</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {configDirty && (
                      <span className="text-xs text-amber-500 flex items-center gap-1">
                        <Info size={12} /> 未保存
                      </span>
                    )}
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={openEditKbModal}
                    >
                      弹窗编辑
                    </Button>
                    <Button
                      size="sm"
                      onClick={handleSaveConfig}
                      disabled={!configDirty || configSaving}
                    >
                      {configSaving ? (
                        <Loader2 size={14} className="animate-spin" />
                      ) : (
                        <Save size={14} />
                      )}
                      {configSaving ? '保存中' : '保存'}
                    </Button>
                    {!isDefaultKb && (
                      <Button
                        size="sm"
                        variant="danger"
                        onClick={() => setConfirmKbDelete(true)}
                      >
                        <Trash2Icon size={14} /> 删除
                      </Button>
                    )}
                  </div>
                </div>

                <div className="p-5 grid grid-cols-2 lg:grid-cols-4 gap-4">
                  {renderField('名称',
                    <input
                      className={inputCls}
                      value={configForm.name}
                      onChange={e => handleConfigChange('name', e.target.value)}
                    />
                  )}
                  {renderField('描述',
                    <input
                      className={inputCls}
                      value={configForm.description}
                      onChange={e => handleConfigChange('description', e.target.value)}
                      placeholder="可选"
                    />
                  )}
                  {renderField('分块大小 (chunk_size)',
                    <input
                      type="number"
                      className={inputCls}
                      value={configForm.chunk_size}
                      onChange={e => handleConfigChange('chunk_size', Number(e.target.value))}
                    />,
                    '每个文本块的 token 数'
                  )}
                  {renderField('分块重叠 (chunk_overlap)',
                    <input
                      type="number"
                      className={inputCls}
                      value={configForm.chunk_overlap}
                      onChange={e => handleConfigChange('chunk_overlap', Number(e.target.value))}
                    />,
                    '相邻分块重叠 token 数'
                  )}
                  {renderField('召回数量 (retrieve_limit)',
                    <input
                      type="number"
                      className={inputCls}
                      value={configForm.retrieve_limit}
                      onChange={e => handleConfigChange('retrieve_limit', Number(e.target.value))}
                    />
                  )}
                  {renderField('相似度阈值',
                    <input
                      type="number"
                      step="0.01"
                      className={inputCls}
                      value={configForm.similarity_threshold}
                      onChange={e => handleConfigChange('similarity_threshold', e.target.value)}
                      placeholder="留空则默认"
                    />,
                    '0 - 1 之间'
                  )}
                  {renderField('分块分隔符',
                    <input
                      className={inputCls}
                      value={configForm.chunk_separator}
                      onChange={e => handleConfigChange('chunk_separator', e.target.value)}
                      placeholder="可选"
                    />
                  )}

                  <div className="col-span-2 lg:col-span-4 grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-gray-50 mt-1">
                    {/* Rerank */}
                    <div className="bg-gray-50/60 rounded-xl p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-gray-700">启用 Rerank 重排序</span>
                        <Toggle
                          checked={configForm.enable_rerank}
                          onChange={v => handleConfigChange('enable_rerank', v)}
                        />
                      </div>
                      {configForm.enable_rerank && (
                        <div className="grid grid-cols-2 gap-3">
                          {renderField('Top N',
                            <input
                              type="number"
                              className={inputCls}
                              value={configForm.rerank_top_n}
                              onChange={e => handleConfigChange('rerank_top_n', Number(e.target.value))}
                            />
                          )}
                          {renderField('分数阈值',
                            <input
                              type="number"
                              step="0.01"
                              className={inputCls}
                              value={configForm.rerank_score_threshold}
                              onChange={e => handleConfigChange('rerank_score_threshold', e.target.value)}
                              placeholder="可选"
                            />
                          )}
                        </div>
                      )}
                    </div>

                    {/* Hybrid */}
                    <div className="bg-gray-50/60 rounded-xl p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-gray-700">启用混合检索 (Hybrid)</span>
                        <Toggle
                          checked={configForm.enable_hybrid}
                          onChange={v => handleConfigChange('enable_hybrid', v)}
                        />
                      </div>
                      {configForm.enable_hybrid && (
                        <div>
                          {renderField('Hybrid Alpha',
                            <input
                              type="number"
                              step="0.05"
                              min="0"
                              max="1"
                              className={inputCls}
                              value={configForm.hybrid_alpha}
                              onChange={e => handleConfigChange('hybrid_alpha', Number(e.target.value))}
                            />,
                            '1.0 纯向量，0.0 纯关键词'
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </section>

              {/* ---- Documents of this KB ---- */}
              <section className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-1.5 bg-green-100 rounded-lg">
                      <FileText size={16} className="text-green-500" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-800">文档列表</h3>
                      <p className="text-xs text-gray-500">
                        {activeKb.name} · 共 {documents.length} 个文档
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="secondary"
                      onClick={() => {
                        setTestModalOpen(true)
                        setTestQuery('')
                        setTestResult(null)
                        setTestError(null)
                      }}
                      disabled={!activeKbId || documents.length === 0}
                    >
                      <Search size={16} />
                      测试召回
                    </Button>
                    <Button variant="secondary" onClick={handleOpenLogs} disabled={!activeKbId}>
                      <Target size={16} />
                      检索日志
                    </Button>
                    <Button
                      variant="secondary"
                      onClick={async () => {
                        if (!activeKbId) return
                        setEvalModalOpen(true)
                        setEvalLoading(false)
                        setEvalError(null)
                        setEvalResult(null)
                        // 加载 dataset
                        setDatasetLoading(true)
                        try {
                          const ds = await knowledgeBaseApi.fetchEvalDataset(activeKbId)
                          setEvalDataset(ds)
                        } catch { /* ignore */ }
                        try {
                          const hist = await knowledgeBaseApi.fetchEvalResults(activeKbId, 10)
                          setEvalHistory(hist)
                        } catch { /* ignore */ }
                        setDatasetLoading(false)
                      }}
                      disabled={!activeKbId}
                    >
                      <Zap size={16} />
                      运行评估
                    </Button>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".pdf,.txt,.docx,.md,.xlsx,.xls,.csv,.json,.py,.js,.ts,.java,.go"
                      onChange={handleUpload}
                      className="hidden"
                    />
                    <Button variant="secondary" onClick={handleUploadClick} disabled={uploading}>
                      {uploading ? (
                        <Loader2 size={16} className="animate-spin" />
                      ) : uploadSuccess ? (
                        <CheckCircle size={16} />
                      ) : (
                        <Upload size={16} />
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
                          <Loader2 size={16} className="animate-spin" />
                        ) : (
                          <Trash2 size={16} />
                        )}
                        {batchDeleting ? '删除中...' : `删除选中 (${selectedIds.size})`}
                      </Button>
                    )}
                  </div>
                </div>

                <AnimatePresence>
                  {uploading && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="border-b border-gray-100 overflow-hidden"
                    >
                      <div className="p-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-gray-700">上传中...</span>
                          <span className="text-sm text-gray-500">{uploadProgress}%</span>
                        </div>
                        <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                          <motion.div
                            className="h-full bg-gradient-to-r from-primary-500 to-purple-500 rounded-full"
                            animate={{ width: `${uploadProgress}%` }}
                            transition={{ ease: 'easeOut' }}
                          />
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {loadingDocs ? (
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
                    <p className="text-sm">点击上传按钮添加文档</p>
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
                              className="w-4 h-4 rounded border-gray-300 text-primary-500 focus:ring-primary-400"
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
                                className="w-4 h-4 rounded border-gray-300 text-primary-500 focus:ring-primary-400"
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
              </section>

              <div className="bg-blue-50 rounded-2xl p-4 flex items-start gap-3">
                <Info size={20} className="text-blue-500 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-medium text-blue-800">使用说明</h4>
                  <p className="text-sm text-blue-600 mt-1">
                    文档上传后默认归入 Default 知识库，点击闪电图标索引到向量数据库后可用于检索。
                    支持勾选多个文档批量删除。支持的格式：PDF、TXT、DOCX、MD。
                  </p>
                </div>
              </div>
            </>
          ) : (
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 h-full flex flex-col items-center justify-center text-gray-400 py-24">
              <FileText size={56} className="mb-4 opacity-40" />
              <p className="text-base font-medium text-gray-500">选择或创建一个知识库开始</p>
              <Button className="mt-4" onClick={openCreateKbModal}>
                <Plus size={16} /> 新建知识库
              </Button>
            </div>
          )}
        </main>
      </div>

      {/* ============ PREVIEW MODAL (exactly as before) ============ */}
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

      {/* ============ KB CREATE / EDIT MODAL ============ */}
      <AnimatePresence>
        {kbFormOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => !kbSaving && setKbFormOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-2xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col"
              onClick={e => e.stopPropagation()}
            >
              <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-gradient-to-br from-primary-100 to-purple-100 rounded-lg flex items-center justify-center">
                    <FileText size={16} className="text-primary-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-800">
                    {kbFormMode === 'create' ? '新建知识库' : '编辑知识库'}
                  </h3>
                </div>
                <motion.button
                  onClick={() => !kbSaving && setKbFormOpen(false)}
                  className="p-2 rounded-lg hover:bg-gray-100 text-gray-400 transition-colors"
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  disabled={kbSaving}
                >
                  <X size={20} />
                </motion.button>
              </div>

              <div className="flex-1 overflow-y-auto p-6 space-y-5">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {renderField('知识库名称 *',
                    <input
                      className={inputCls}
                      value={kbForm.name}
                      onChange={e => setKbForm(p => ({ ...p, name: e.target.value }))}
                      placeholder="例如：产品文档库"
                    />
                  )}
                  {renderField('描述',
                    <input
                      className={inputCls}
                      value={kbForm.description}
                      onChange={e => setKbForm(p => ({ ...p, description: e.target.value }))}
                      placeholder="可选"
                    />
                  )}
                  {renderField('分块大小 (chunk_size)',
                    <input
                      type="number"
                      className={inputCls}
                      value={kbForm.chunk_size}
                      onChange={e => setKbForm(p => ({ ...p, chunk_size: Number(e.target.value) }))}
                    />
                  )}
                  {renderField('分块重叠 (chunk_overlap)',
                    <input
                      type="number"
                      className={inputCls}
                      value={kbForm.chunk_overlap}
                      onChange={e => setKbForm(p => ({ ...p, chunk_overlap: Number(e.target.value) }))}
                    />
                  )}
                  {renderField('召回数量 (retrieve_limit)',
                    <input
                      type="number"
                      className={inputCls}
                      value={kbForm.retrieve_limit}
                      onChange={e => setKbForm(p => ({ ...p, retrieve_limit: Number(e.target.value) }))}
                    />
                  )}
                  {renderField('相似度阈值',
                    <input
                      type="number"
                      step="0.01"
                      className={inputCls}
                      value={kbForm.similarity_threshold}
                      onChange={e => setKbForm(p => ({ ...p, similarity_threshold: e.target.value }))}
                      placeholder="留空则默认"
                    />
                  )}
                </div>

                <div className="bg-gray-50/60 rounded-xl p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">启用 Rerank 重排序</span>
                    <Toggle
                      checked={kbForm.enable_rerank}
                      onChange={v => setKbForm(p => ({ ...p, enable_rerank: v }))}
                    />
                  </div>
                  {kbForm.enable_rerank && (
                    <div className="grid grid-cols-2 gap-3">
                      {renderField('Top N',
                        <input
                          type="number"
                          className={inputCls}
                          value={kbForm.rerank_top_n}
                          onChange={e => setKbForm(p => ({ ...p, rerank_top_n: Number(e.target.value) }))}
                        />
                      )}
                      {renderField('分数阈值',
                        <input
                          type="number"
                          step="0.01"
                          className={inputCls}
                          value={kbForm.rerank_score_threshold}
                          onChange={e => setKbForm(p => ({ ...p, rerank_score_threshold: e.target.value }))}
                          placeholder="可选"
                        />
                      )}
                    </div>
                  )}
                </div>

                <div className="bg-gray-50/60 rounded-xl p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">启用混合检索 (Hybrid)</span>
                    <Toggle
                      checked={kbForm.enable_hybrid}
                      onChange={v => setKbForm(p => ({ ...p, enable_hybrid: v }))}
                    />
                  </div>
                  {kbForm.enable_hybrid && (
                    <div>
                      {renderField('Hybrid Alpha',
                        <input
                          type="number"
                          step="0.05"
                          min="0"
                          max="1"
                          className={inputCls}
                          value={kbForm.hybrid_alpha}
                          onChange={e => setKbForm(p => ({ ...p, hybrid_alpha: Number(e.target.value) }))}
                        />,
                        '1.0 纯向量，0.0 纯关键词'
                      )}
                    </div>
                  )}
                </div>
              </div>

              <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-end gap-2">
                <Button
                  variant="secondary"
                  onClick={() => setKbFormOpen(false)}
                  disabled={kbSaving}
                >
                  取消
                </Button>
                <Button onClick={handleKbSubmit} disabled={kbSaving}>
                  {kbSaving && <Loader2 size={16} className="animate-spin" />}
                  {kbSaving ? '保存中...' : (kbFormMode === 'create' ? '创建' : '保存')}
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ============ KB DELETE CONFIRM MODAL ============ */}
      <AnimatePresence>
        {confirmKbDelete && activeKb && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => !kbSaving && setConfirmKbDelete(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-2xl w-full max-w-sm overflow-hidden"
              onClick={e => e.stopPropagation()}
            >
              <div className="p-6">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 bg-red-100 rounded-xl flex items-center justify-center">
                    <AlertCircle size={20} className="text-red-500" />
                  </div>
                  <h3 className="text-base font-semibold text-gray-800">确认删除知识库？</h3>
                </div>
                <p className="text-sm text-gray-500">
                  知识库 <span className="font-medium text-gray-700">「{activeKb.name}」</span> 及其配置将被永久删除，此操作不可恢复。
                </p>
              </div>
              <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-end gap-2 bg-gray-50">
                <Button variant="secondary" onClick={() => setConfirmKbDelete(false)}>
                  取消
                </Button>
                <Button variant="danger" onClick={handleDeleteKb}>
                  <Trash2 size={16} /> 确认删除
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}

        {/* ---------- Retrieve Test Modal ---------- */}
        {testModalOpen && activeKb && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
            onClick={() => setTestModalOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.95, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.95, y: 20 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-2xl shadow-xl w-full max-w-3xl max-h-[85vh] flex flex-col"
            >
              <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-1.5 bg-primary-100 rounded-lg">
                    <Search size={16} className="text-primary-500" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-800">知识问答测试</h3>
                    <p className="text-xs text-gray-500">
                      在「{activeKb.name}」中执行向量检索，验证召回效果
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setTestModalOpen(false)}
                  className="p-1 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600"
                >
                  <X size={20} />
                </button>
              </div>

              {/* Query form */}
              <div className="px-6 py-4 border-b border-gray-100 bg-gray-50 space-y-3">
                <textarea
                  value={testQuery}
                  onChange={(e) => setTestQuery(e.target.value)}
                  placeholder="输入你的问题，例如：如何配置 Embedding 模型？"
                  className="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-200 resize-none"
                  rows={2}
                />
                <div className="flex items-center gap-3 flex-wrap">
                  <label className="flex items-center gap-2 text-xs text-gray-600">
                    Top K
                    <input
                      type="number"
                      min={1}
                      max={30}
                      value={testTopK}
                      onChange={(e) => setTestTopK(parseInt(e.target.value) || 5)}
                      className="w-16 px-2 py-1 rounded border border-gray-200 text-center"
                    />
                  </label>
                  <label className="flex items-center gap-2 text-xs text-gray-600">
                    阈值 (distance)
                    <input
                      type="text"
                      value={testThreshold}
                      onChange={(e) => setTestThreshold(e.target.value)}
                      placeholder={activeKb.similarity_threshold?.toString() || '自动'}
                      className="w-20 px-2 py-1 rounded border border-gray-200 text-center"
                    />
                  </label>
                  <Button
                    size="sm"
                    onClick={handleRetrieveTest}
                    disabled={testLoading || !testQuery.trim()}
                  >
                    {testLoading ? (
                      <Loader2 size={14} className="animate-spin" />
                    ) : (
                      <Target size={14} />
                    )}
                    {testLoading ? '检索中...' : '执行检索'}
                  </Button>
                </div>
              </div>

              {/* Result area */}
              <div className="flex-1 overflow-y-auto p-6">
                {testError && (
                  <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 flex items-center gap-2">
                    <AlertCircle size={16} /> {testError}
                  </div>
                )}

                {testLoading && (
                  <div className="flex items-center justify-center py-12 text-gray-400">
                    <Loader2 size={20} className="animate-spin mr-2" /> 正在检索...
                  </div>
                )}

                {!testLoading && !testResult && !testError && (
                  <div className="text-center py-12 text-gray-400">
                    <Search size={40} className="mx-auto mb-3 opacity-30" />
                    <p className="text-sm">输入问题后点击「执行检索」查看召回归因</p>
                  </div>
                )}

                {testResult && (
                  <div className="space-y-4">
                    {/* Summary */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      <StatCard label="Embedding 模型" value={testResult.embedding_model} />
                      <StatCard
                        label="召回数量"
                        value={`${testResult.results_after_threshold} / ${testResult.results_before_threshold}`}
                      />
                      <StatCard
                        label="阈值"
                        value={testResult.threshold_applied ? testResult.threshold_value?.toFixed(3) || '—' : '未应用'}
                      />
                      <StatCard
                        label="总耗时"
                        value={`${testResult.timings_ms.total_ms?.toFixed(0) || '—'} ms`}
                      />
                    </div>
                    <div className="text-xs text-gray-500 flex gap-4">
                      {testResult.timings_ms.embedding_load_ms != null && (
                        <span>加载 {testResult.timings_ms.embedding_load_ms.toFixed(0)}ms</span>
                      )}
                      {testResult.timings_ms.query_embed_ms != null && (
                        <span>Embedding {testResult.timings_ms.query_embed_ms.toFixed(0)}ms</span>
                      )}
                      {testResult.timings_ms.vector_search_ms != null && (
                        <span>向量检索 {testResult.timings_ms.vector_search_ms.toFixed(0)}ms</span>
                      )}
                      {testResult.knowledge_base.enable_hybrid && <span>🔀 混合检索</span>}
                      {testResult.knowledge_base.enable_rerank && <span>🔁 Rerank 已启用</span>}
                    </div>

                    {/* Chunks */}
                    {testResult.results.length === 0 ? (
                      <div className="text-center py-8 text-gray-400 text-sm">
                        <Info size={20} className="mx-auto mb-2 opacity-40" />
                        没有命中任何 chunk，尝试换个问题或调低阈值
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {testResult.results.map((chunk, idx) => (
                          <div
                            key={chunk.id}
                            className="border border-gray-200 rounded-lg p-4 hover:border-primary-200 transition-colors"
                          >
                            <div className="flex items-start justify-between gap-3 mb-2">
                              <div className="flex items-center gap-2">
                                <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-primary-100 text-primary-600 text-xs font-semibold">
                                  {idx + 1}
                                </span>
                                <span className="text-xs font-mono text-gray-500">
                                  {chunk.id.slice(0, 12)}...
                                </span>
                              </div>
                              <div className="flex items-center gap-2 text-xs">
                                <span
                                  className={`px-2 py-0.5 rounded font-mono ${
                                    chunk.distance < 0.3
                                      ? 'bg-green-100 text-green-700'
                                      : chunk.distance < 0.6
                                      ? 'bg-amber-100 text-amber-700'
                                      : 'bg-gray-100 text-gray-600'
                                  }`}
                                >
                                  dist: {chunk.distance.toFixed(4)}
                                </span>
                              </div>
                            </div>
                            <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                              {chunk.content_preview}
                            </p>
                            {chunk.metadata && Object.keys(chunk.metadata).length > 0 && (
                              <details className="mt-2 text-xs text-gray-500">
                                <summary className="cursor-pointer hover:text-gray-700">
                                  metadata
                                </summary>
                                <pre className="mt-1 p-2 bg-gray-50 rounded overflow-auto max-h-32">
                                  {JSON.stringify(chunk.metadata, null, 2)}
                                </pre>
                              </details>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}

        {/* ---------- Retrieval Logs Modal ---------- */}
        {logModalOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
            onClick={() => setLogModalOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.95, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.95, y: 20 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-2xl shadow-xl w-full max-w-4xl max-h-[85vh] flex flex-col"
            >
              <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-1.5 bg-primary-100 rounded-lg">
                    <Target size={16} className="text-primary-500" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-800">检索日志</h3>
                    <p className="text-xs text-gray-500">
                      {activeKb ? `「${activeKb.name}」最近 50 条检索记录` : '全部知识库最近 50 条检索记录'}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleOpenLogs}
                    className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600"
                    title="刷新"
                  >
                    <Loader2 size={16} />
                  </button>
                  <button
                    onClick={() => setLogModalOpen(false)}
                    className="p-1 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600"
                  >
                    <X size={20} />
                  </button>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto">
                {logLoading && (
                  <div className="flex items-center justify-center py-12 text-gray-400">
                    <Loader2 size={20} className="animate-spin mr-2" /> 加载中...
                  </div>
                )}

                {!logLoading && retrievalLogs.length === 0 && (
                  <div className="text-center py-12 text-gray-400">
                    <Target size={40} className="mx-auto mb-3 opacity-30" />
                    <p className="text-sm">暂无检索记录，先执行一次召回测试</p>
                  </div>
                )}

                {!logLoading && retrievalLogs.length > 0 && (
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 sticky top-0">
                      <tr className="text-left text-xs text-gray-500 uppercase">
                        <th className="px-4 py-2 font-medium">#</th>
                        <th className="px-4 py-2 font-medium">Query</th>
                        <th className="px-4 py-2 font-medium">结果</th>
                        <th className="px-4 py-2 font-medium">耗时</th>
                        <th className="px-4 py-2 font-medium">配置</th>
                        <th className="px-4 py-2 font-medium">时间</th>
                      </tr>
                    </thead>
                    <tbody>
                      {retrievalLogs.map((log) => (
                        <tr key={log.id} className="border-t border-gray-100 hover:bg-gray-50">
                          <td className="px-4 py-2 text-gray-400 font-mono text-xs">{log.id}</td>
                          <td className="px-4 py-2 max-w-xs">
                            <p className="truncate text-gray-800" title={log.query}>{log.query}</p>
                            <p className="text-xs text-gray-400">{log.kb_name || log.knowledge_base_id?.slice(0, 10)}</p>
                          </td>
                          <td className="px-4 py-2">
                            <span className="font-medium text-gray-700">{log.results_count}</span>
                            <span className="text-xs text-gray-400">/{log.top_k}</span>
                            {log.threshold_applied && (
                              <span className="ml-1 text-xs text-amber-600">阈值过滤</span>
                            )}
                          </td>
                          <td className="px-4 py-2 font-mono text-gray-700">
                            {log.latency_ms?.toFixed(1) || '—'} ms
                          </td>
                          <td className="px-4 py-2">
                            <div className="flex gap-1 flex-wrap">
                              {log.hybrid_applied && <span className="px-1.5 py-0.5 text-[10px] bg-purple-100 text-purple-700 rounded">hybrid</span>}
                              {log.rerank_applied && <span className="px-1.5 py-0.5 text-[10px] bg-blue-100 text-blue-700 rounded">rerank</span>}
                            </div>
                          </td>
                          <td className="px-4 py-2 text-xs text-gray-500 whitespace-nowrap">
                            {log.created_at ? new Date(log.created_at).toLocaleString('zh-CN') : '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}

        {evalModalOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
            onClick={() => setEvalModalOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.95, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.95, y: 20 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-2xl shadow-xl w-full max-w-5xl max-h-[90vh] flex flex-col"
            >
              <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-1.5 bg-amber-100 rounded-lg">
                    <Zap size={16} className="text-amber-500" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-800">检索质量评估</h3>
                    <p className="text-xs text-gray-500">
                      {activeKb ? `「${activeKb.name}」离线评估` : '选择知识库后运行评估'}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setEvalModalOpen(false)}
                  className="p-1 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600"
                >
                  <X size={20} />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {/* Eval Dataset 管理面板 */}
                <div className="bg-gray-50 rounded-xl p-4 border border-gray-100">
                  <div className="flex items-center justify-between mb-3">
                    <div className="text-sm font-semibold text-gray-700">
                      评估数据集 <span className="text-xs text-gray-400">({evalDataset.length} 条)</span>
                    </div>
                    {activeKbId && evalDataset.length > 0 && (
                      <Button
                        onClick={async () => {
                          if (!activeKbId) return
                          setEvalLoading(true)
                          setEvalError(null)
                          setEvalResult(null)
                          try {
                            const res = await knowledgeBaseApi.runEval(activeKbId)
                            setEvalResult(res)
                            const hist = await knowledgeBaseApi.fetchEvalResults(activeKbId, 10)
                            setEvalHistory(hist)
                          } catch (err: any) {
                            setEvalError(err.response?.data?.detail || err.message || '评估失败')
                          } finally {
                            setEvalLoading(false)
                          }
                        }}
                        disabled={evalLoading}
                        size="sm"
                      >
                        {evalLoading ? <Loader2 size={14} className="animate-spin mr-1" /> : <Zap size={14} className="mr-1" />}
                        运行评估
                      </Button>
                    )}
                  </div>

                  {/* 添加新条目表单 */}
                  <div className="flex gap-2 mb-3">
                    <input
                      type="text"
                      value={newEvalQuery}
                      onChange={e => setNewEvalQuery(e.target.value)}
                      placeholder="Query（例如：系统如何处理数据权限？）"
                      className="flex-1 px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-200"
                    />
                    <input
                      type="text"
                      value={newEvalDocIds}
                      onChange={e => setNewEvalDocIds(e.target.value)}
                      placeholder="expected_document_ids (逗号分隔)"
                      className="flex-1 px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-200"
                    />
                    <Button
                      onClick={async () => {
                        if (!activeKbId || !newEvalQuery.trim()) return
                        const ids = newEvalDocIds.split(',').map(s => s.trim()).filter(Boolean)
                        try {
                          await knowledgeBaseApi.addEvalDatasetItem(activeKbId, {
                            query: newEvalQuery.trim(),
                            expected_document_ids: ids.length ? ids : undefined,
                          })
                          const ds = await knowledgeBaseApi.fetchEvalDataset(activeKbId)
                          setEvalDataset(ds)
                          setNewEvalQuery('')
                          setNewEvalDocIds('')
                        } catch { /* ignore */ }
                      }}
                      disabled={!newEvalQuery.trim() || !activeKbId}
                      size="sm"
                    >
                      <Plus size={14} className="mr-1" />
                      添加
                    </Button>
                  </div>

                  {/* 数据集条目列表 */}
                  {datasetLoading ? (
                    <div className="flex items-center justify-center py-6 text-gray-400">
                      <Loader2 size={16} className="animate-spin mr-2" /> 加载中...
                    </div>
                  ) : evalDataset.length === 0 ? (
                    <div className="text-center py-6 text-xs text-gray-400">
                      暂无评估数据，在上方表单添加 →
                    </div>
                  ) : (
                    <div className="max-h-40 overflow-y-auto space-y-1">
                      {evalDataset.map((item: any) => (
                        <div key={item.id} className="flex items-center gap-2 py-1.5 px-2 rounded hover:bg-white group">
                          <span className="text-xs text-gray-400 font-mono w-6">#{item.id}</span>
                          <span className="flex-1 text-sm text-gray-700 truncate" title={item.query}>{item.query}</span>
                          {item.expected_document_ids?.length > 0 && (
                            <span className="text-[10px] px-1.5 py-0.5 bg-green-100 text-green-700 rounded">
                              {item.expected_document_ids.length} doc
                            </span>
                          )}
                          <button
                            onClick={async () => {
                              try {
                                await knowledgeBaseApi.deleteEvalDatasetItem(item.id)
                                if (activeKbId) {
                                  const ds = await knowledgeBaseApi.fetchEvalDataset(activeKbId)
                                  setEvalDataset(ds)
                                }
                              } catch { /* ignore */ }
                            }}
                            className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {evalLoading && (
                  <div className="flex items-center justify-center py-4 text-gray-400">
                    <Loader2 size={20} className="animate-spin mr-2" /> 正在运行评估...
                  </div>
                )}

                {evalError && (
                  <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-700">
                    {evalError}
                    <div className="mt-2 text-xs text-red-500">
                      提示：请先通过 API 向知识库添加 eval-dataset（query + expected_document_ids）
                    </div>
                  </div>
                )}

                {!evalLoading && evalResult && (
                  <>
                    <div className="grid grid-cols-3 gap-4">
                      <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-4 border border-green-100">
                        <div className="text-xs text-green-600 font-medium mb-2">HitRate@5</div>
                        <div className="text-2xl font-bold text-green-700">
                          {(evalResult.hit_rate.at_5 * 100).toFixed(1)}%
                        </div>
                        <div className="text-xs text-green-500 mt-1">
                          {evalResult.hit_rate.at_5 * evalResult.total_queries} / {evalResult.total_queries} queries
                        </div>
                      </div>
                      <div className="bg-gradient-to-br from-blue-50 to-sky-50 rounded-xl p-4 border border-blue-100">
                        <div className="text-xs text-blue-600 font-medium mb-2">HitRate@10</div>
                        <div className="text-2xl font-bold text-blue-700">
                          {(evalResult.hit_rate.at_10 * 100).toFixed(1)}%
                        </div>
                        <div className="text-xs text-blue-500 mt-1">
                          {(evalResult.hit_rate.at_10 * evalResult.total_queries).toFixed(0)} / {evalResult.total_queries} queries
                        </div>
                      </div>
                      <div className="bg-gradient-to-br from-purple-50 to-violet-50 rounded-xl p-4 border border-purple-100">
                        <div className="text-xs text-purple-600 font-medium mb-2">MRR@5 / MRR@10</div>
                        <div className="text-2xl font-bold text-purple-700">
                          {evalResult.mrr.at_5.toFixed(3)}
                          <span className="text-purple-400 text-base mx-1">/</span>
                          {evalResult.mrr.at_10.toFixed(3)}
                        </div>
                        <div className="text-xs text-purple-500 mt-1">Mean Reciprocal Rank</div>
                      </div>
                    </div>

                    <div className="grid grid-cols-4 gap-3 bg-gray-50 rounded-xl p-4">
                      <div className="text-center">
                        <div className="text-xs text-gray-500">HitRate@1</div>
                        <div className="text-lg font-semibold text-gray-800">{(evalResult.hit_rate.at_1 * 100).toFixed(0)}%</div>
                      </div>
                      <div className="text-center">
                        <div className="text-xs text-gray-500">HitRate@3</div>
                        <div className="text-lg font-semibold text-gray-800">{(evalResult.hit_rate.at_3 * 100).toFixed(0)}%</div>
                      </div>
                      <div className="text-center">
                        <div className="text-xs text-gray-500">HitRate@5</div>
                        <div className="text-lg font-semibold text-gray-800">{(evalResult.hit_rate.at_5 * 100).toFixed(0)}%</div>
                      </div>
                      <div className="text-center">
                        <div className="text-xs text-gray-500">耗时</div>
                        <div className="text-lg font-semibold text-gray-800">{evalResult.latency_ms} ms</div>
                      </div>
                    </div>

                    <details className="bg-gray-50 rounded-xl p-4">
                      <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900">
                        配置快照 & 详情
                      </summary>
                      <div className="mt-3 space-y-2 text-xs font-mono text-gray-600">
                        <pre className="bg-white p-2 rounded border border-gray-200">
{JSON.stringify(evalResult.config, null, 2)}
                        </pre>
                        {evalResult.details.slice(0, 10).map((d, i) => (
                          <div key={i} className="flex gap-2 py-1 border-b border-gray-100">
                            <span className={d.hit_at_5 ? 'text-green-600' : 'text-red-500'}>
                              {d.hit_at_5 ? '✓' : '✗'}
                            </span>
                            <span className="flex-1 truncate">{d.query}</span>
                          </div>
                        ))}
                      </div>
                    </details>
                  </>
                )}

                {!evalLoading && !evalResult && evalHistory.length === 0 && (
                  <div className="text-center py-12 text-gray-400">
                    <Zap size={40} className="mx-auto mb-3 opacity-30" />
                    <p className="text-sm">
                      点击"运行评估"开始（需先通过 API 添加 eval-dataset）
                    </p>
                  </div>
                )}

                {!evalLoading && evalHistory.length > 0 && (
                  <div>
                    <div className="text-xs text-gray-500 font-medium mb-2">历史评估记录</div>
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50">
                        <tr className="text-left text-xs text-gray-500 uppercase">
                          <th className="px-3 py-2 font-medium">#</th>
                          <th className="px-3 py-2 font-medium">Queries</th>
                          <th className="px-3 py-2 font-medium">Hit@5</th>
                          <th className="px-3 py-2 font-medium">Hit@10</th>
                          <th className="px-3 py-2 font-medium">MRR@5</th>
                          <th className="px-3 py-2 font-medium">耗时</th>
                          <th className="px-3 py-2 font-medium">时间</th>
                        </tr>
                      </thead>
                      <tbody>
                        {evalHistory.map((h) => (
                          <tr key={h.id} className="border-t border-gray-100 hover:bg-gray-50">
                            <td className="px-3 py-2 text-gray-400 font-mono text-xs">{h.id}</td>
                            <td className="px-3 py-2 text-gray-700">{h.total_queries}</td>
                            <td className="px-3 py-2 text-green-700 font-medium">
                              {(h.hit_rate_at_5 * 100).toFixed(0)}%
                            </td>
                            <td className="px-3 py-2 text-blue-700 font-medium">
                              {(h.hit_rate_at_10 * 100).toFixed(0)}%
                            </td>
                            <td className="px-3 py-2 text-purple-700">
                              {h.mrr_at_5.toFixed(3)}
                            </td>
                            <td className="px-3 py-2 font-mono text-gray-500">{h.latency_ms} ms</td>
                            <td className="px-3 py-2 text-xs text-gray-500 whitespace-nowrap">
                              {h.created_at ? new Date(h.created_at).toLocaleString('zh-CN') : '—'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// ============ StatCard Component ============

interface StatCardProps {
  label: string
  value: string | number
}

const StatCard = ({ label, value }: StatCardProps) => {
  return (
    <div className="bg-gray-50 rounded-lg p-3 border border-gray-100">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className="text-sm font-semibold text-gray-800 truncate" title={value.toString()}>
        {value}
      </div>
    </div>
  )
}

// ============ Toggle Component ============

interface ToggleProps {
  checked: boolean
  onChange: (checked: boolean) => void
}

const Toggle = ({ checked, onChange }: ToggleProps) => {
  return (
    <motion.button
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
        checked ? 'bg-gradient-to-r from-primary-500 to-purple-500' : 'bg-gray-300'
      }`}
      whileTap={{ scale: 0.95 }}
    >
      <motion.span
        className="inline-block h-5 w-5 rounded-full bg-white shadow"
        animate={{ x: checked ? 22 : 2 }}
        transition={{ type: 'spring', stiffness: 500, damping: 30 }}
      />
    </motion.button>
  )
}

export default KnowledgeBasePage
