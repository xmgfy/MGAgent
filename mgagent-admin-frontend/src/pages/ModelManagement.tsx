import { useState, useEffect, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Cpu, Save, RefreshCw, CheckCircle, XCircle, ExternalLink, Plus, Trash2, Power, Download, Info, Search, KeyRound } from 'lucide-react'
import Button from '../components/Button'
import { modelApi } from '../api/client'
import { toast, getErrorMessage } from '../components/Toast'
import type { ModelConfig, LocalEmbeddingModel, Provider, DiscoveredModel } from '../api/client'

const ParamHelpIcon: React.FC<{ text: string }> = ({ text }) => (
  <span className="group/help relative inline-block ml-1 align-middle">
    <span
      className="inline-flex items-center justify-center w-4 h-4 rounded-full bg-gray-200 text-gray-500 text-[10px] font-bold cursor-help hover:bg-blue-100 hover:text-blue-600 transition-colors"
      aria-label={text}
    >ⓘ</span>
    <span
      role="tooltip"
      className="absolute left-1/2 -translate-x-1/2 bottom-full mb-1 z-50 w-56 p-2 rounded-lg bg-gray-900 text-white text-[11px] leading-relaxed shadow-xl opacity-0 invisible group-hover/help:opacity-100 group-hover/help:visible transition-all duration-150 pointer-events-none whitespace-normal break-words"
    >
      {text}
      <span className="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900" />
    </span>
  </span>
)

const PROVIDER_EMOJI_FALLBACK: Record<string, string> = {
  openai: '🤖',
  deepseek: '🚀',
  dashscope: '☁️',
  zhipu: '🧠',
  jina: '🔍',
  ollama: '🏠',
  local: '💻',
  minimax: '🎯',
  moonshot: '🌙',
  stepfun: '📐',
  custom: '🔗',
}

const MODEL_TYPE_LABELS: Record<string, string> = {
  chat: '💬 对话模型',
  embedding: '📊 Embedding 模型',
  reranker: '🎯 Reranker 模型',
}

const FAVICON_CDN_LIST = [
  (domain: string) => `https://favicon.im/${domain}`,
  (domain: string) => `https://favicon.cccyun.cc/${domain}`,
  (domain: string) => `https://www.google.com/s2/favicons?domain=${domain}&sz=64`,
]

const getFaviconWithFallback = (
  domain: string,
  providerCode: string,
  cdnIndex: number = 0
): React.ReactNode => {
  if (cdnIndex >= FAVICON_CDN_LIST.length) {
    return (
      <span className="w-6 h-6 rounded bg-gray-100 flex items-center justify-center text-sm flex-shrink-0">
        {PROVIDER_EMOJI_FALLBACK[providerCode] || '📦'}
      </span>
    )
  }
  return (
    <img
      src={FAVICON_CDN_LIST[cdnIndex](domain)}
      alt={providerCode}
      className="w-6 h-6 rounded flex-shrink-0"
      onError={(e) => {
        e.preventDefault()
        const img = e.target as HTMLImageElement
        const nextIndex = cdnIndex + 1
        if (nextIndex < FAVICON_CDN_LIST.length) {
          img.src = FAVICON_CDN_LIST[nextIndex](domain)
        } else {
          const parent = img.parentElement
          if (parent) {
            parent.replaceChild(
              Object.assign(document.createElement('span'), {
                className: 'w-6 h-6 rounded bg-gray-100 flex items-center justify-center text-sm flex-shrink-0',
                textContent: PROVIDER_EMOJI_FALLBACK[providerCode] || '📦',
              }),
              img
            )
          }
        }
      }}
    />
  )
}

const ModelManagement = () => {
  const [chatConfigs, setChatConfigs] = useState<ModelConfig[]>([])
  const [embeddingConfigs, setEmbeddingConfigs] = useState<ModelConfig[]>([])
  const [rerankerConfigs, setRerankerConfigs] = useState<ModelConfig[]>([])
  const [activeConfig, setActiveConfig] = useState<ModelConfig | null>(null)
  const [activeEmbeddingConfig, setActiveEmbeddingConfig] = useState<ModelConfig | null>(null)
  const [activeRerankerConfig, setActiveRerankerConfig] = useState<ModelConfig | null>(null)
  const [activeTab, setActiveTab] = useState<'chat' | 'embedding' | 'reranker'>('chat')
  const [saving, setSaving] = useState(false)
  const [testResult, setTestResult] = useState<{ status: string; response?: string; error?: string } | null>(null)
  const [testing, setTesting] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [editingConfig, setEditingConfig] = useState<ModelConfig | null>(null)
  const [localModels, setLocalModels] = useState<LocalEmbeddingModel[]>([])
  const [downloadingModel, setDownloadingModel] = useState<string | null>(null)
  const [providers, setProviders] = useState<Provider[]>([])
  const [tenants, setTenants] = useState<{ id: string; name: string }[]>([])
  const [discovering, setDiscovering] = useState(false)
  const [discoveredModels, setDiscoveredModels] = useState<DiscoveredModel[]>([])
  const [newConfig, setNewConfig] = useState({
    name: '', api_key: '', api_base: '', model_name: '',
    model_type: 'chat' as 'chat' | 'embedding' | 'reranker',
    provider: 'openai',
    dimension: 1536,
    is_local: false,
    local_model_id: '',
    scenario: '',
    tenant_id: '',
    temperature: 0.7 as number | null,
    top_p: 1 as number | null,
    max_tokens: null as number | null,
    presence_penalty: 0 as number | null,
    frequency_penalty: 0 as number | null,
  })

  const [mainTab, setMainTab] = useState<'provider' | 'model'>('model')
  const [showProviderModal, setShowProviderModal] = useState(false)
  const [editingProvider, setEditingProvider] = useState<Provider | null>(null)
  const [newProvider, setNewProvider] = useState({
    code: '',
    display_name: '',
    favicon_domain: '',
    default_api_base: '',
    supports_api_key: true,
    supports_local: false,
    supports_discover: true,
    supported_model_types: ['chat'] as string[],
    description: '',
    api_key: '',
  })
  const [detectingProviderId, setDetectingProviderId] = useState<string | null>(null)

  useEffect(() => {
    loadData()
    loadLocalModels()
    loadProviders()
  }, [])

  const currentProviders = useMemo(() => {
    return providers.filter(p =>
      p.is_active !== false && currentTabConfig(p.supported_model_types, newConfig.model_type)
    )
  }, [providers, newConfig.model_type])

  const currentProviderInfo = useMemo(() => {
    return providers.find(p => p.code === newConfig.provider)
  }, [providers, newConfig.provider])

  function currentTabConfig(types: string[], modelType: string): boolean {
    return types.includes(modelType)
  }

  const loadData = async () => {
    try {
      const configsData = await modelApi.getConfigs()
      setChatConfigs(configsData.filter(c => c.model_type === 'chat'))
      setEmbeddingConfigs(configsData.filter(c => c.model_type === 'embedding'))
      setRerankerConfigs(configsData.filter(c => c.model_type === 'reranker'))
      const active = configsData.find(c => c.is_active && c.model_type === 'chat')
      setActiveConfig(active || null)
      const activeEmb = configsData.find(c => c.is_active && c.model_type === 'embedding')
      setActiveEmbeddingConfig(activeEmb || null)
      const activeRer = configsData.find(c => c.is_active && c.model_type === 'reranker')
      setActiveRerankerConfig(activeRer || null)
    } catch (error) {
      toast.error(`加载模型列表失败: ${getErrorMessage(error)}`)
    }
  }

  const loadLocalModels = async () => {
    try {
      const models = await modelApi.getLocalModels()
      setLocalModels(models)
    } catch (error) {
      console.error('加载本地模型列表失败:', error)
    }
  }

  const loadProviders = async () => {
    try {
      const data = await modelApi.getProviders()
      setProviders(data)
      const token = localStorage.getItem('admin_token') || ''
      fetch('/admin/api/tenants', { headers: { Authorization: `Bearer ${token}` } })
        .then(r => r.ok ? r.json() : [])
        .then(t => setTenants(Array.isArray(t) ? t : []))
        .catch(() => {})
    } catch (error) {
      console.error('加载 Provider 列表失败:', error)
    }
  }

  const handleProviderChange = (providerCode: string) => {
    const provider = providers.find(p => p.code === providerCode)
    if (!provider) return

    const isLocal = provider.supports_local && !provider.supports_api_key
    const providerKey = provider.api_key || ''
    const providerBase = provider.default_api_base || ''

    setNewConfig(prev => ({
      ...prev,
      provider: providerCode,
      api_base: providerBase || prev.api_base,
      api_key: providerKey || prev.api_key,
      is_local: isLocal,
      local_model_id: isLocal ? prev.local_model_id : '',
      model_name: '',
      dimension: prev.dimension,
    }))
    setDiscoveredModels([])
  }

  const handleDiscoverModels = async () => {
    const provider = currentProviderInfo
    if (!provider) return

    if (provider.supports_api_key && !provider.supports_local && !newConfig.api_key) {
      toast.warning('请先填写 API Key 再检测可用模型')
      return
    }

    if (provider.code === 'ollama' && !newConfig.api_base) {
      toast.warning('请确认 Ollama API Base 地址')
      return
    }

    try {
      setDiscovering(true)
      setDiscoveredModels([])
      const result = await modelApi.discoverModels({
        provider_code: provider.code,
        api_base: newConfig.api_base || provider.default_api_base,
        api_key: newConfig.api_key,
        model_type: newConfig.model_type,
      })
      setDiscoveredModels(result.models)
      const msg = `发现 ${result.total} 个模型（Chat: ${result.chat_count}, Embedding: ${result.embedding_count}, Reranker: ${result.reranker_count}）`
      if (result.total === 0) {
        toast.info(`${msg}，当前模型类型下无可选项`)
      } else {
        toast.success(msg)
      }
    } catch (error) {
      toast.error(`检测失败: ${getErrorMessage(error)}`)
    } finally {
      setDiscovering(false)
    }
  }

  const handleDiscoveredModelSelect = (model: DiscoveredModel) => {
    setNewConfig(prev => ({
      ...prev,
      model_name: model.model_id,
      dimension: model.dimension ?? prev.dimension,
    }))
  }

  const handleDownloadLocalModel = async (modelId: string) => {
    try {
      setDownloadingModel(modelId)
      const result = await modelApi.downloadLocalModel(modelId)
      if (result.status === 'success') {
        toast.success(result.message)
      }
    } catch (error) {
      toast.error(`下载失败: ${getErrorMessage(error)}`)
    } finally {
      setDownloadingModel(null)
    }
  }

  const handleLocalModelSelect = (modelId: string) => {
    const model = localModels.find(m => m.id === modelId)
    if (model) {
      setNewConfig(prev => ({
        ...prev,
        local_model_id: modelId,
        model_name: model.name,
        dimension: model.dimension,
        provider: 'local'
      }))
    }
  }

  const handleSave = async () => {
    if (!editingConfig) return
    try {
      setSaving(true)
      const provider = currentProviderInfo
      const supportsApiKey = provider?.supports_api_key ?? true
      const supportsLocal = provider?.supports_local ?? false
      
      const updateData: any = {
        model_name: newConfig.model_name || undefined,
        model_type: newConfig.model_type,
        provider: newConfig.provider,
        dimension: newConfig.model_type === 'embedding' ? newConfig.dimension : undefined,
        is_local: newConfig.is_local && supportsLocal,
        scenario: newConfig.scenario || undefined,
        tenant_id: newConfig.tenant_id || undefined,
      }
      if (newConfig.model_type === 'chat') {
        updateData.temperature = newConfig.temperature
        updateData.top_p = newConfig.top_p
        updateData.max_tokens = newConfig.max_tokens
        updateData.presence_penalty = newConfig.presence_penalty
        updateData.frequency_penalty = newConfig.frequency_penalty
      }
      if (supportsApiKey && !newConfig.is_local) {
        updateData.api_key = newConfig.api_key || undefined
        updateData.api_base = newConfig.api_base || undefined
      }
      await modelApi.updateConfig(editingConfig.id, updateData)
      setSaving(false)
      setShowEditModal(false)
      toast.success('模型配置更新成功')
      loadData()
    } catch (error) {
      toast.error(`保存失败: ${getErrorMessage(error)}`)
      setSaving(false)
    }
  }

  const handleCreate = async () => {
    const isEmbedding = newConfig.model_type === 'embedding'
    const provider = currentProviderInfo
    const requiresApiKey = provider?.supports_api_key ?? true
    const requiresApiBase = provider?.code !== 'local'

    if (!newConfig.name || !newConfig.model_name) {
      toast.warning('请填写配置名称和模型名称')
      return
    }
    if (requiresApiKey && !newConfig.is_local && !newConfig.api_key) {
      toast.warning(`当前提供商 ${provider?.display_name || ''} 需要 API Key`)
      return
    }
    if (requiresApiBase && !newConfig.api_base) {
      toast.warning('请填写 API Base URL')
      return
    }
    if (isEmbedding && !newConfig.is_local && !newConfig.dimension) {
      toast.warning('Embedding 模型需要指定维度')
      return
    }
    try {
      setSaving(true)
      const createData: any = {
        name: newConfig.name,
        model_name: newConfig.model_name,
        model_type: newConfig.model_type,
        provider: newConfig.provider,
        dimension: isEmbedding && !newConfig.is_local ? newConfig.dimension : undefined,
        is_local: newConfig.is_local,
        scenario: newConfig.scenario || undefined,
        tenant_id: newConfig.tenant_id || undefined,
      }
      if (newConfig.model_type === 'chat') {
        createData.temperature = newConfig.temperature
        createData.top_p = newConfig.top_p
        createData.max_tokens = newConfig.max_tokens
        createData.presence_penalty = newConfig.presence_penalty
        createData.frequency_penalty = newConfig.frequency_penalty
      }
      if (!newConfig.is_local) {
        if (requiresApiKey) {
          createData.api_key = newConfig.api_key
        }
        if (requiresApiBase) {
          createData.api_base = newConfig.api_base
        }
      }
      await modelApi.createConfig(createData)
      setSaving(false)
      setShowCreateModal(false)
      setNewConfig({
        name: '', api_key: '', api_base: '', model_name: '',
        model_type: 'chat', provider: 'openai', dimension: 1536, is_local: false, local_model_id: '',
        scenario: '', tenant_id: '',
        temperature: 0.7, top_p: 1, max_tokens: null, presence_penalty: 0, frequency_penalty: 0,
      })
      toast.success('模型配置创建成功')
      loadData()
    } catch (error) {
      toast.error(`创建失败: ${getErrorMessage(error)}`)
      setSaving(false)
    }
  }

  const handleTest = async () => {
    try {
      setTesting(true)
      const result = await modelApi.testConnection()
      setTestResult(result)
      setTesting(false)
      if (result.status === 'success') {
        toast.success('模型连接测试成功')
      } else {
        toast.error('模型连接测试失败')
      }
    } catch (error) {
      const errorMsg = getErrorMessage(error)
      setTestResult({ status: 'failed', error: errorMsg })
      setTesting(false)
      toast.error(`连接测试失败: ${errorMsg}`)
    }
  }

  const handleActivate = async (configId: string) => {
    try {
      await modelApi.activateConfig(configId)
      toast.success('模型已启用，主后端将立即感知到变更')
      loadData()
    } catch (error) {
      toast.error(`启用失败: ${getErrorMessage(error)}`)
    }
  }

  const handleDeactivate = async (configId: string) => {
    if (!window.confirm('确定要停用这个模型配置吗？停用后将没有启用的模型，用户将无法使用聊天功能。')) return
    try {
      await modelApi.deactivateConfig(configId)
      toast.warning('模型已停用，用户将无法使用聊天功能')
      loadData()
    } catch (error) {
      toast.error(`停用失败: ${getErrorMessage(error)}`)
    }
  }

  const handleDelete = async (configId: string) => {
    if (!window.confirm('确定要删除这个模型配置吗？')) return
    try {
      await modelApi.deleteConfig(configId)
      toast.success('模型配置已删除')
      loadData()
    } catch (error) {
      toast.error(`删除失败: ${getErrorMessage(error)}`)
    }
  }

  const handleEdit = (config: ModelConfig) => {
    setEditingConfig(config)
    const matchedLocalModel = localModels.find(m => m.name === config.model_name)
    setNewConfig({
      name: config.name,
      api_key: '',
      api_base: config.api_base || '',
      model_name: config.model_name,
      model_type: config.model_type as 'chat' | 'embedding' | 'reranker',
      provider: config.provider,
      dimension: config.dimension || 1536,
      is_local: config.is_local,
      local_model_id: matchedLocalModel?.id || '',
      scenario: config.scenario || '',
      tenant_id: config.tenant_id || '',
      temperature: config.temperature ?? 0.7,
      top_p: config.top_p ?? 1,
      max_tokens: config.max_tokens ?? null,
      presence_penalty: config.presence_penalty ?? 0,
      frequency_penalty: config.frequency_penalty ?? 0,
    })
    setDiscoveredModels([])
    setShowEditModal(true)
  }

  const handleEditProvider = (p: Provider) => {
    setEditingProvider(p)
    setNewProvider({
      code: p.code,
      display_name: p.display_name,
      favicon_domain: p.favicon_domain || '',
      default_api_base: p.default_api_base || '',
      supports_api_key: p.supports_api_key,
      supports_local: p.supports_local,
      supports_discover: p.supports_discover,
      supported_model_types: [...p.supported_model_types],
      description: p.description || '',
      api_key: '',
    })
    setShowProviderModal(true)
  }

  const handleToggleProvider = async (p: Provider) => {
    try {
      if (p.id) {
        await modelApi.toggleProvider(p.id)
      }
      toast.success(`Provider 已${p.is_active ? '停用' : '启用'}`)
      await loadProviders()
    } catch (err) {
      toast.error(`操作失败: ${getErrorMessage(err)}`)
    }
  }

  const handleDeleteProvider = async (p: Provider) => {
    if (!p.id) return
    if (!window.confirm(`确定删除 Provider "${p.display_name}"？该操作不可恢复。`)) return
    try {
      await modelApi.deleteProvider(p.id)
      toast.success('Provider 已删除')
      await loadProviders()
    } catch (err) {
      toast.error(`删除失败: ${getErrorMessage(err)}`)
    }
  }

  const handleDetectProviderTypes = async (p: Provider) => {
    if (detectingProviderId) return

    if (p.supports_discover === false) {
      toast.warning('该厂商不支持动态探测')
      return
    }
    const hasKey = p.has_api_key || (p.api_key_masked && p.api_key_masked.length > 0)
    const needsKey = p.supports_api_key
    if (needsKey && !hasKey) {
      toast.warning('请先在编辑中配置 API Key 后再探测')
      return
    }

    setDetectingProviderId(p.id || p.code)
    try {
      const result = await modelApi.discoverModels({
        provider_code: p.code,
        api_base: p.default_api_base,
      })

      const detectedTypes: string[] = []
      if (result.chat_count > 0) detectedTypes.push('chat')
      if (result.embedding_count > 0) detectedTypes.push('embedding')
      if (result.reranker_count > 0) detectedTypes.push('reranker')

      const extraFromModels = new Set<string>()
      for (const m of result.models) {
        if (m.model_type && !detectedTypes.includes(m.model_type)) {
          extraFromModels.add(m.model_type)
        }
      }
      detectedTypes.push(...extraFromModels)

      const sorted = [...detectedTypes].sort()
      const currentSorted = [...(p.supported_model_types || [])].sort()

      const same = sorted.length === currentSorted.length &&
        sorted.every((t, i) => t === currentSorted[i])

      if (same) {
        toast.success(`探测完成，类型配置已是最新（${sorted.map(t => MODEL_TYPE_LABELS[t]?.split(' ')[1] || t).join(' / ')}）`)
        return
      }

      const typeBadge = (t: string) => MODEL_TYPE_LABELS[t]?.split(' ')[1] || t
      const currentStr = currentSorted.length > 0 ? currentSorted.map(typeBadge).join('、') : '（无）'
      const detectedStr = sorted.map(typeBadge).join('、')

      const confirmed = window.confirm(
        `检测到「${p.display_name}」的支持类型与配置不同：\n\n` +
        `当前配置：${currentStr}\n` +
        `实际探测：${detectedStr}\n\n` +
        `是否自动更新？（${result.total} 个模型已分类）`
      )

      if (confirmed && p.id) {
        await modelApi.updateProvider(p.id, { supported_model_types: sorted })
        toast.success(`已更新为：${detectedStr}`)
        await loadProviders()
      }
    } catch (err) {
      toast.error(`探测失败: ${getErrorMessage(err)}`)
    } finally {
      setDetectingProviderId(null)
    }
  }

  const currentActive = activeTab === 'chat' ? activeConfig : activeTab === 'embedding' ? activeEmbeddingConfig : activeRerankerConfig
  const currentConfigs = activeTab === 'chat' ? chatConfigs : activeTab === 'embedding' ? embeddingConfigs : rerankerConfigs

  const getTabGradient = (tab: 'chat' | 'embedding' | 'reranker') =>
    tab === 'chat' ? 'from-primary-500 to-accent-500'
    : tab === 'embedding' ? 'from-purple-500 to-indigo-500'
    : 'from-amber-500 to-orange-500'
  const getTabActiveBorder = (tab: 'chat' | 'embedding' | 'reranker') =>
    tab === 'chat' ? 'border-primary-500 bg-primary-50'
    : tab === 'embedding' ? 'border-purple-500 bg-purple-50'
    : 'border-amber-500 bg-amber-50'
  const getTabActiveText = (tab: 'chat' | 'embedding' | 'reranker') =>
    tab === 'chat' ? 'text-primary-600'
    : tab === 'embedding' ? 'text-purple-600'
    : 'text-amber-600'

  return (
    <div className="space-y-6">
      {/* 主 Tab 切换 */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-2 mb-6 flex gap-1 w-fit">
        <button
          onClick={() => setMainTab('provider')}
          className={`px-6 py-2.5 rounded-xl text-sm font-medium transition-all ${
            mainTab === 'provider'
              ? 'bg-gradient-to-r from-blue-500 to-indigo-500 text-white shadow-md'
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          🏢 厂商管理
        </button>
        <button
          onClick={() => setMainTab('model')}
          className={`px-6 py-2.5 rounded-xl text-sm font-medium transition-all ${
            mainTab === 'model'
              ? 'bg-gradient-to-r from-primary-500 to-accent-500 text-white shadow-md'
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          🤖 模型管理
        </button>
      </div>

      {mainTab === 'provider' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-800">厂商管理</h2>
              <p className="text-sm text-gray-500 mt-1">
                {providers.filter(p => p.is_active !== false).length} 个启用 / {providers.filter(p => p.is_active === false).length} 个停用 · 共 {providers.length} 家
              </p>
            </div>
            <Button onClick={() => {
              setEditingProvider(null)
              setNewProvider({
                code: '', display_name: '', favicon_domain: '', default_api_base: '',
                supports_api_key: true, supports_local: false, supports_discover: true,
                supported_model_types: ['chat'], description: '', api_key: '',
              })
              setShowProviderModal(true)
            }}>
              <Plus size={18} />
              新增自定义厂商
            </Button>
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr className="text-left text-gray-500 text-xs uppercase tracking-wider">
                  <th className="px-5 py-3 font-medium">厂商</th>
                  <th className="px-5 py-3 font-medium">状态</th>
                  <th className="px-5 py-3 font-medium">支持类型</th>
                  <th className="px-5 py-3 font-medium">API Key</th>
                  <th className="px-5 py-3 font-medium">API Base</th>
                  <th className="px-5 py-3 font-medium text-right">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {providers.map(p => (
                  <tr key={p.id || p.code} className={`transition-colors ${
                    p.is_active === false ? 'bg-gray-50/50' : 'hover:bg-gray-50'
                  }`}>
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-3">
                        {getFaviconWithFallback(p.favicon_domain || '', p.code)}
                        <div>
                          <div className="flex items-center gap-2">
                            <span className={`font-medium ${p.is_active === false ? 'text-gray-400 line-through' : 'text-gray-800'}`}>
                              {p.display_name}
                            </span>
                            {p.is_system && (
                              <span className="text-[10px] px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded">内置</span>
                            )}
                          </div>
                          <div className="text-xs text-gray-400 font-mono">{p.code}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-4">
                      {p.is_active === false ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs bg-red-50 text-red-600 rounded">
                          <span className="w-1.5 h-1.5 bg-red-400 rounded-full"></span>已停用
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs bg-green-50 text-green-600 rounded">
                          <span className="w-1.5 h-1.5 bg-green-400 rounded-full"></span>启用中
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex gap-1 flex-wrap">
                        {p.supported_model_types.map(t => (
                          <span key={t} className={`text-[10px] px-1.5 py-0.5 rounded ${
                            t === 'chat' ? 'bg-blue-50 text-blue-600'
                            : t === 'embedding' ? 'bg-purple-50 text-purple-600'
                            : 'bg-amber-50 text-amber-600'
                          }`}>
                            {MODEL_TYPE_LABELS[t]?.split(' ')[1] || t}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-5 py-4">
                      {p.has_api_key || (p.api_key_masked && p.api_key_masked.length > 0) ? (
                        <span className="text-xs text-green-600">🔑 {p.api_key_masked || '已配置'}</span>
                      ) : (
                        <span className="text-xs text-gray-400">未配置</span>
                      )}
                    </td>
                    <td className="px-5 py-4 max-w-[180px] truncate">
                      <span className="text-xs text-gray-500 font-mono" title={p.default_api_base || ''}>
                        {p.default_api_base || '—'}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button onClick={() => handleDetectProviderTypes(p)}
                          disabled={detectingProviderId === (p.id || p.code) || p.supports_discover === false}
                          className={`px-3 py-1.5 text-xs rounded-lg flex items-center gap-1 ${
                            detectingProviderId === (p.id || p.code)
                              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                              : p.supports_discover === false
                              ? 'bg-gray-50 text-gray-300 cursor-not-allowed'
                              : 'bg-blue-50 text-blue-600 hover:bg-blue-100'
                          }`}>
                          <Search size={12} />
                          {detectingProviderId === (p.id || p.code) ? '探测中...' : '探测类型'}
                        </button>
                        <button onClick={() => handleEditProvider(p)}
                          className="px-3 py-1.5 text-xs bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
                          编辑
                        </button>
                        <button onClick={() => handleToggleProvider(p)}
                          className={`px-3 py-1.5 text-xs rounded-lg ${
                            p.is_active === false
                              ? 'bg-green-100 text-green-700 hover:bg-green-200'
                              : 'bg-yellow-50 text-yellow-700 hover:bg-yellow-100'
                          }`}>
                          {p.is_active === false ? '启用' : '停用'}
                        </button>
                        {!p.is_system && (
                          <button onClick={() => handleDeleteProvider(p)}
                            className="px-2 py-1.5 text-xs bg-red-50 text-red-500 rounded-lg hover:bg-red-100">
                            <Trash2 size={14} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {mainTab === 'model' && (
        <>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-100 rounded-xl">
                <Cpu size={20} className="text-orange-500" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-800">模型管理</h2>
                <p className="text-sm text-gray-500">配置和管理 AI 模型（对话 / Embedding / Reranker）</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Button variant="secondary" onClick={loadData}>
                <RefreshCw size={18} />
                刷新
              </Button>
              <Button onClick={() => {
                const defaultProviderCode = providers.find(p => p.is_active !== false && p.supported_model_types.includes(activeTab))?.code
                setNewConfig({
                  name: '', api_key: '', api_base: '', model_name: '',
                  model_type: activeTab, provider: defaultProviderCode || (activeTab === 'embedding' ? 'dashscope' : activeTab === 'reranker' ? 'minimax' : 'openai'),
                  dimension: 1536, is_local: false, local_model_id: '',
                  scenario: '', tenant_id: '',
                  temperature: 0.7, top_p: 1, max_tokens: null, presence_penalty: 0, frequency_penalty: 0,
                })
                setDiscoveredModels([])
                setShowCreateModal(true)
              }}>
                <Plus size={18} />
                添加模型
              </Button>
            </div>
          </div>

          <div className="flex gap-2 bg-gray-100 p-1 rounded-xl w-fit">
            <button
              onClick={() => { setActiveTab('chat'); setDiscoveredModels([]) }}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-all ${
                activeTab === 'chat'
                  ? 'bg-white text-primary-600 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              对话模型 ({chatConfigs.length})
            </button>
            <button
              onClick={() => { setActiveTab('embedding'); setDiscoveredModels([]) }}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-all ${
                activeTab === 'embedding'
                  ? 'bg-white text-primary-600 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Embedding 模型 ({embeddingConfigs.length})
            </button>
            <button
              onClick={() => { setActiveTab('reranker'); setDiscoveredModels([]) }}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-all ${
                activeTab === 'reranker'
                  ? 'bg-white text-amber-600 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Reranker 模型 ({rerankerConfigs.length})
            </button>
          </div>

          {currentActive && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className={`bg-gradient-to-r ${getTabGradient(activeTab)} rounded-2xl p-6 text-white`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Power size={20} className="text-green-300" />
                    <span className="text-sm font-medium text-green-100">
                      当前启用{MODEL_TYPE_LABELS[activeTab].replace(/^[^\s]+\s/, '')}模型
                    </span>
                  </div>
                  <h3 className="text-2xl font-bold">{currentActive.name}</h3>
                  <p className="text-sm text-white/80 mt-1">
                    {currentActive.model_name}
                    {currentActive.model_type === 'embedding' && currentActive.dimension && (
                      <span className="ml-2 px-2 py-0.5 bg-white/20 rounded">
                        {currentActive.dimension}维
                      </span>
                    )}
                    {currentActive.is_local && (
                      <span className="ml-2 px-2 py-0.5 bg-green-500/40 rounded">本地模型</span>
                    )}
                  </p>
                </div>
                <div className="text-right">
                  {currentActive.is_local ? (
                    <div className="text-sm">
                      <p className="text-white/70">运行方式</p>
                      <p className="font-medium">本地部署</p>
                    </div>
                  ) : (
                    <>
                      <p className="text-sm text-white/70">API 地址</p>
                      <p className="font-medium truncate max-w-xs">{currentActive.api_base}</p>
                      {currentActive.api_key_masked && (
                        <p className="text-sm text-white/70 mt-2">
                          API Key: <span className="font-mono">{currentActive.api_key_masked}</span>
                        </p>
                      )}
                    </>
                  )}
                </div>
              </div>
              <div className="mt-4 flex gap-3">
                <Button variant="white" onClick={handleTest} disabled={testing}>
                  {testing ? '测试中...' : '测试连接'}
                </Button>
                <Button variant="white-secondary" onClick={() => handleEdit(currentActive)}>
                  编辑配置
                </Button>
                <Button variant="white-secondary" onClick={() => handleDeactivate(currentActive.id)} className="text-red-600 hover:text-red-700">
                  <Power size={16} className="mr-1" />
                  停用
                </Button>
              </div>

              {testResult && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`mt-4 p-4 rounded-xl flex items-start gap-3 ${
                    testResult.status === 'success' ? 'bg-white/20' : 'bg-red-500/30'
                  }`}
                >
                  {testResult.status === 'success' ? (
                    <CheckCircle size={20} className="text-green-300 flex-shrink-0 mt-0.5" />
                  ) : (
                    <XCircle size={20} className="text-red-300 flex-shrink-0 mt-0.5" />
                  )}
                  <div>
                    <p className={`font-medium ${testResult.status === 'success' ? 'text-green-100' : 'text-red-100'}`}>
                      {testResult.status === 'success' ? '连接成功' : '连接失败'}
                    </p>
                    {testResult.response && (
                      <p className="text-sm text-white/80 mt-1">{testResult.response}</p>
                    )}
                    {testResult.error && (
                      <p className="text-sm text-red-200 mt-1">{testResult.error}</p>
                    )}
                  </div>
                </motion.div>
              )}
            </motion.div>
          )}

          {!currentActive && currentConfigs.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-yellow-50 border border-yellow-200 rounded-2xl p-6"
            >
              <p className="text-yellow-800 font-medium">
                未启用任何{MODEL_TYPE_LABELS[activeTab].replace(/^[^\s]+\s/, '')}模型，请选择一个模型配置并启用。
              </p>
            </motion.div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6"
            >
              <h3 className="font-semibold text-gray-800 mb-4">
                已配置{MODEL_TYPE_LABELS[activeTab].replace(/^[^\s]+\s/, '')}模型
              </h3>
              
              {currentConfigs.length === 0 ? (
                <div className="text-center py-8">
                  <Cpu size={40} className="text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-400">暂无模型配置</p>
                  <button
                    onClick={() => {
                      const defaultProviderCode = providers.find(p => p.is_active !== false && p.supported_model_types.includes(activeTab))?.code
                      setNewConfig({
                        name: '', api_key: '', api_base: '', model_name: '',
                        model_type: activeTab, provider: defaultProviderCode || (activeTab === 'embedding' ? 'dashscope' : activeTab === 'reranker' ? 'minimax' : 'openai'),
                        dimension: 1536, is_local: false, local_model_id: '',
                        scenario: '', tenant_id: '',
                        temperature: 0.7, top_p: 1, max_tokens: null, presence_penalty: 0, frequency_penalty: 0,
                      })
                      setDiscoveredModels([])
                      setShowCreateModal(true)
                    }}
                    className="mt-3 text-primary-500 hover:text-primary-600 text-sm font-medium"
                  >
                    添加第一个模型
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  {currentConfigs.map((config) => (
                    <motion.div
                      key={config.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className={`p-4 rounded-xl border transition-all ${
                        config.is_active
                          ? getTabActiveBorder(activeTab)
                          : 'border-gray-100 hover:border-gray-200 hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`w-2 h-2 rounded-full ${config.is_active ? 'bg-green-500' : 'bg-gray-400'}`} />
                          <div>
                            <div className="flex items-center gap-2 flex-wrap">
                              <p className={`font-medium ${config.is_active ? getTabActiveText(activeTab) : 'text-gray-800'}`}>
                                {config.name}
                              </p>
                              {config.is_active && (
                                <span className="text-xs px-2 py-0.5 bg-green-100 text-green-600 rounded-full">启用中</span>
                              )}
                              {config.model_type === 'embedding' && config.dimension && (
                                <span className="text-xs px-1.5 py-0.5 bg-purple-100 text-purple-600 rounded">
                                  {config.dimension}维
                                </span>
                              )}
                              {config.model_type === 'reranker' && (
                                <span className="text-xs px-1.5 py-0.5 bg-amber-100 text-amber-600 rounded">🎯 Reranker</span>
                              )}
                              {config.is_local && (
                                <span className="text-xs px-1.5 py-0.5 bg-green-100 text-green-600 rounded">本地</span>
                              )}
                            </div>
                            <p className="text-sm text-gray-500 truncate">{config.model_name}</p>
                          </div>
                        </div>
                        <ExternalLink size={16} className="text-gray-400" />
                      </div>
                      {!config.is_local && (
                        <div className="mt-2 text-xs text-gray-400 truncate">{config.api_base}</div>
                      )}
                      <div className="mt-3 flex gap-2">
                        {!config.is_active ? (
                          <button
                            onClick={() => handleActivate(config.id)}
                            className="flex-1 px-3 py-1.5 text-xs bg-green-500 text-white rounded-lg hover:bg-green-600"
                          >
                            启用
                          </button>
                        ) : (
                          <button
                            onClick={() => handleDeactivate(config.id)}
                            className="flex-1 px-3 py-1.5 text-xs bg-red-500 text-white rounded-lg hover:bg-red-600"
                          >
                            停用
                          </button>
                        )}
                        <button
                          onClick={() => handleEdit(config)}
                          className="flex-1 px-3 py-1.5 text-xs bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                        >
                          编辑
                        </button>
                        {!config.is_active && (
                          <button
                            onClick={() => handleDelete(config.id)}
                            className="px-3 py-1.5 text-xs bg-red-50 text-red-600 rounded-lg hover:bg-red-100"
                          >
                            <Trash2 size={12} />
                          </button>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-gray-100 p-6"
            >
              <h3 className="font-semibold text-gray-800 mb-4">模型信息</h3>
              
              {currentActive ? (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="p-4 bg-gray-50 rounded-xl">
                    <p className="text-sm text-gray-500 mb-1">当前模型</p>
                    <p className="font-medium text-gray-800">{currentActive.name}</p>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-xl">
                    <p className="text-sm text-gray-500 mb-1">模型名称</p>
                    <p className="font-medium text-gray-800">{currentActive.model_name}</p>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-xl">
                    <p className="text-sm text-gray-500 mb-1">API 地址</p>
                    <p className="font-medium text-gray-800 truncate">{currentActive.api_base}</p>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-xl">
                    <p className="text-sm text-gray-500 mb-1">状态</p>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-green-500" />
                      <span className="font-medium text-green-600">已启用</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <Cpu size={40} className="text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-400">请配置并启用一个{MODEL_TYPE_LABELS[activeTab].replace(/^[^\s]+\s/, '')}模型</p>
                </div>
              )}

              <div className="mt-6 p-4 bg-blue-50 rounded-xl">
                <h4 className="font-medium text-blue-800 mb-2">配置说明</h4>
                <ul className="text-sm text-blue-600 space-y-1">
                  <li>- DeepSeek: api_base = https://api.deepseek.com/v1</li>
                  <li>- OpenAI: api_base = https://api.openai.com/v1</li>
                  <li>- Anthropic: api_base = https://api.anthropic.com/v1</li>
                  <li>- Qwen (阿里云): api_base = https://dashscope.aliyuncs.com/compatible-mode/v1</li>
                </ul>
              </div>
            </motion.div>
          </div>
        </>
      )}

      <AnimatePresence>
        {showProviderModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => setShowProviderModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="bg-white rounded-2xl p-6 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold text-gray-800 mb-6">
                {editingProvider ? '编辑 Provider' : '新增自定义 Provider'}
              </h3>
              <div className="space-y-4">
                {!editingProvider && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Provider Code（唯一标识）</label>
                    <input
                      type="text"
                      value={newProvider.code}
                      onChange={(e) => setNewProvider({ ...newProvider, code: e.target.value })}
                      className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 font-mono"
                      placeholder="例如：my-gateway 或 anthropic-compat"
                      disabled={!!editingProvider}
                    />
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">显示名称</label>
                  <input
                    type="text"
                    value={newProvider.display_name}
                    onChange={(e) => setNewProvider(prev => ({ ...prev, display_name: e.target.value }))}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                    placeholder="例如：我的专用网关"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Favicon 域名（可选）</label>
                  <input
                    type="text"
                    value={newProvider.favicon_domain}
                    onChange={(e) => setNewProvider(prev => ({ ...prev, favicon_domain: e.target.value }))}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 font-mono"
                    placeholder="例如：my-api.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">默认 API Base URL</label>
                  <input
                    type="text"
                    value={newProvider.default_api_base}
                    onChange={(e) => setNewProvider(prev => ({ ...prev, default_api_base: e.target.value }))}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 font-mono"
                    placeholder="例如：https://api.example.com/v1"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    全局 API Key（可选，会自动填入新建的模型配置）
                  </label>
                  <input
                    type="password"
                    value={newProvider.api_key}
                    onChange={(e) => setNewProvider(prev => ({ ...prev, api_key: e.target.value }))}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 font-mono"
                    placeholder={editingProvider && editingProvider.has_api_key ? '已配置（留空=不改，输入=替换）' : '输入 API Key'}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">支持的模型类型</label>
                  <div className="flex gap-2">
                    {['chat', 'embedding', 'reranker'].map(t => {
                      const types = newProvider.supported_model_types
                      const checked = types.includes(t)
                      return (
                        <label key={t} className={`flex-1 flex items-center justify-center gap-1 px-3 py-2 text-xs rounded-lg border cursor-pointer transition-all ${
                          checked ? 'border-primary-500 bg-primary-50 text-primary-700' : 'border-gray-200 text-gray-500 hover:border-gray-300'
                        }`}>
                          <input
                            type="checkbox"
                            className="hidden"
                            checked={checked}
                            onChange={() => {
                              const next = checked
                                ? types.filter(x => x !== t)
                                : [...types, t]
                              setNewProvider(prev => ({ ...prev, supported_model_types: next }))
                            }}
                          />
                          {MODEL_TYPE_LABELS[t]}
                        </label>
                      )
                    })}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">能力开关</label>
                  <div className="flex gap-3 flex-wrap">
                    <label className="flex items-center gap-2 text-xs text-gray-600">
                      <input type="checkbox" checked={newProvider.supports_api_key}
                        onChange={(e) => setNewProvider(prev => ({ ...prev, supports_api_key: e.target.checked }))}
                        className="rounded border-gray-300" />
                      需要 API Key
                    </label>
                    <label className="flex items-center gap-2 text-xs text-gray-600">
                      <input type="checkbox" checked={newProvider.supports_discover}
                        onChange={(e) => setNewProvider(prev => ({ ...prev, supports_discover: e.target.checked }))}
                        className="rounded border-gray-300" />
                      支持动态发现
                    </label>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">描述</label>
                  <textarea
                    value={newProvider.description}
                    onChange={(e) => setNewProvider(prev => ({ ...prev, description: e.target.value }))}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 resize-none"
                    rows={2}
                    placeholder="简要说明这个 Provider 的用途"
                  />
                </div>
              </div>
              <div className="flex gap-3 mt-6">
                <Button variant="secondary" onClick={() => { setShowProviderModal(false); setEditingProvider(null) }}>取消</Button>
                <Button onClick={async () => {
                  try {
                    const types = newProvider.supported_model_types
                    if (types.length === 0) { toast.warning('至少选择一种支持的模型类型'); return }
                    if (editingProvider && editingProvider.id) {
                      await modelApi.updateProvider(editingProvider.id, {
                        display_name: newProvider.display_name || editingProvider.display_name,
                        favicon_domain: newProvider.favicon_domain || editingProvider.favicon_domain,
                        default_api_base: newProvider.default_api_base,
                        supports_api_key: newProvider.supports_api_key,
                        supports_discover: newProvider.supports_discover,
                        supported_model_types: types,
                        description: newProvider.description,
                        api_key: newProvider.api_key || undefined,
                      })
                      toast.success('Provider 更新成功')
                    } else {
                      if (!newProvider.code || !newProvider.display_name) { toast.warning('请填写 code 和显示名称'); return }
                      await modelApi.createProvider({
                        code: newProvider.code,
                        display_name: newProvider.display_name,
                        favicon_domain: newProvider.favicon_domain,
                        default_api_base: newProvider.default_api_base,
                        supports_api_key: newProvider.supports_api_key,
                        supports_local: false,
                        supports_discover: newProvider.supports_discover,
                        supported_model_types: types,
                        description: newProvider.description,
                        api_key: newProvider.api_key || undefined,
                      })
                      toast.success('Provider 创建成功')
                    }
                    setShowProviderModal(false)
                    setEditingProvider(null)
                    await loadProviders()
                  } catch (err) {
                    toast.error(`操作失败: ${getErrorMessage(err)}`)
                  }
                }}>
                  <Save size={16} />
                  {editingProvider ? '保存修改' : '创建 Provider'}
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}

        {showCreateModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => setShowCreateModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="bg-white rounded-2xl p-6 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold text-gray-800 mb-6">添加模型配置</h3>
              <div className="space-y-4">
                {/* 模型类型 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">模型类型</label>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => {
                        const chatProviders = providers.filter(p => p.supported_model_types.includes('chat'))
                        const defaultProvider = chatProviders[0]
                        setNewConfig({
                          ...newConfig,
                          model_type: 'chat',
                          provider: defaultProvider?.code || 'openai',
                          api_base: defaultProvider?.default_api_base || newConfig.api_base,
                          is_local: defaultProvider?.supports_local && !defaultProvider.supports_api_key,
                          local_model_id: '',
                          model_name: '',
                          dimension: 1536,
                          temperature: 0.7, top_p: 1, max_tokens: null, presence_penalty: 0, frequency_penalty: 0,
                        })
                      }}
                      className={`flex-1 py-2 text-sm rounded-lg border transition-all ${
                        newConfig.model_type === 'chat'
                          ? 'border-primary-500 bg-primary-50 text-primary-700'
                          : 'border-gray-200 text-gray-600 hover:border-gray-300'
                      }`}
                    >
                      💬 对话模型
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        const embProviders = providers.filter(p => p.supported_model_types.includes('embedding'))
                        const defaultProvider = embProviders[0]
                        setNewConfig({
                          ...newConfig,
                          model_type: 'embedding',
                          provider: defaultProvider?.code || 'dashscope',
                          api_base: defaultProvider?.default_api_base || newConfig.api_base,
                          is_local: defaultProvider?.supports_local && !defaultProvider.supports_api_key,
                          local_model_id: '',
                          model_name: '',
                          dimension: 1536,
                          temperature: null, top_p: null, max_tokens: null, presence_penalty: null, frequency_penalty: null,
                        })
                      }}
                      className={`flex-1 py-2 text-sm rounded-lg border transition-all ${
                        newConfig.model_type === 'embedding'
                          ? 'border-purple-500 bg-purple-50 text-purple-700'
                          : 'border-gray-200 text-gray-600 hover:border-gray-300'
                      }`}
                    >
                      📊 Embedding 模型
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        const rerProviders = providers.filter(p => p.supported_model_types.includes('reranker'))
                        const defaultProvider = rerProviders[0]
                        setNewConfig({
                          ...newConfig,
                          model_type: 'reranker',
                          provider: defaultProvider?.code || 'minimax',
                          api_base: defaultProvider?.default_api_base || newConfig.api_base,
                          is_local: false,
                          local_model_id: '',
                          model_name: '',
                          dimension: 1536,
                          temperature: null, top_p: null, max_tokens: null, presence_penalty: null, frequency_penalty: null,
                        })
                      }}
                      className={`flex-1 py-2 text-sm rounded-lg border transition-all ${
                        newConfig.model_type === 'reranker'
                          ? 'border-amber-500 bg-amber-50 text-amber-700'
                          : 'border-gray-200 text-gray-600 hover:border-gray-300'
                      }`}
                    >
                      🎯 Reranker 模型
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">配置名称</label>
                  <input
                    type="text"
                    value={newConfig.name}
                    onChange={(e) => setNewConfig({ ...newConfig, name: e.target.value })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                    placeholder={newConfig.model_type === 'embedding' ? '例如：DashScope Embedding' : newConfig.model_type === 'reranker' ? '例如：Jina Reranker' : '例如：DeepSeek'}
                  />
                </div>

                {/* Provider 选择（chat 和 embedding 都显示） */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">服务提供商</label>
                  <div className="flex items-center gap-2">
                    {currentProviderInfo && getFaviconWithFallback(currentProviderInfo.favicon_domain, currentProviderInfo.code)}
                    <select
                      value={newConfig.provider}
                      onChange={(e) => handleProviderChange(e.target.value)}
                      className="flex-1 px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                    >
                      {currentProviders.map(p => (
                        <option key={p.code} value={p.code}>
                          {p.display_name}
                        </option>
                      ))}
                    </select>
                  </div>
                  {currentProviderInfo && (
                    <p className="text-xs text-gray-500 mt-1 flex items-center gap-1">
                      <Info size={12} />
                      {currentProviderInfo.description}
                      {currentProviderInfo.supports_discover && !currentProviderInfo.supports_local && (
                        <span className="ml-1 px-1.5 py-0.5 bg-green-100 text-green-700 rounded text-[10px]">支持动态检测</span>
                      )}
                    </p>
                  )}
                </div>

                {/* 本地模型选项 */}
                {newConfig.model_type === 'embedding' && currentProviderInfo?.code !== 'ollama' && currentProviderInfo?.supports_local && (
                  <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg">
                    <input
                      type="checkbox"
                      id="is_local"
                      checked={newConfig.is_local}
                      onChange={(e) => {
                        const isLocal = e.target.checked
                        setNewConfig({ ...newConfig, is_local: isLocal })
                        if (!isLocal) {
                          setNewConfig(prev => ({ ...prev, local_model_id: '', model_name: '', dimension: 1536 }))
                        }
                      }}
                      className="w-4 h-4 rounded border-gray-300 text-green-500 focus:ring-green-400"
                    />
                    <label htmlFor="is_local" className="flex-1 text-sm text-green-700 cursor-pointer">
                      使用本地 HuggingFace 模型（免 API Key）
                    </label>
                  </div>
                )}

                {/* 动态检测可用模型 */}
                {currentProviderInfo?.supports_discover && !newConfig.is_local && (
                  <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-sm font-medium text-blue-700 flex items-center gap-1">
                        <Search size={14} />
                        检测 {newConfig.model_type === 'embedding' ? 'Embedding' : newConfig.model_type === 'reranker' ? 'Reranker' : 'Chat'} 模型
                      </label>
                      <button
                        type="button"
                        onClick={handleDiscoverModels}
                        disabled={discovering}
                        className={`px-3 py-1.5 text-xs rounded-lg font-medium transition-all ${
                          discovering
                            ? 'bg-blue-300 text-white cursor-wait'
                            : 'bg-blue-500 text-white hover:bg-blue-600'
                        }`}
                      >
                        {discovering ? '检测中...' : '🔍 检测可用模型'}
                      </button>
                    </div>

                    {discoveredModels.length > 0 && (
                      <>
                        <p className="text-xs text-blue-600 mb-2">
                          发现 {discoveredModels.length} 个可用模型，点击选择（或直接手动输入）
                        </p>
                        <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto">
                          {discoveredModels.map(m => (
                            <button
                              key={m.model_id}
                              type="button"
                              onClick={() => handleDiscoveredModelSelect(m)}
                              className={`px-2.5 py-1 text-xs rounded-md border transition-all text-left ${
                                newConfig.model_name === m.model_id
                                  ? 'border-blue-500 bg-blue-100 text-blue-800'
                                  : 'border-blue-200 bg-white text-gray-700 hover:border-blue-300 hover:bg-blue-50'
                              }`}
                            >
                              <span className="font-medium">{m.model_id}</span>
                              {m.dimension && (
                                <span className="ml-1 text-[10px] text-gray-500">{m.dimension}维</span>
                              )}
                            </button>
                          ))}
                        </div>
                      </>
                    )}

                    {discoveredModels.length === 0 && !discovering && (
                      <p className="text-xs text-blue-500">
                        点击检测按钮，自动查询该 Provider 账号下可用的最新模型
                      </p>
                    )}

                    {discoveredModels.length === 0 && !discovering && currentProviderInfo?.fallback_models?.[newConfig.model_type]?.length && (
                      <div className="mt-2 pt-2 border-t border-blue-100">
                        <p className="text-[11px] text-gray-400 mb-1">
                          💡 未检测时可参考以下常用模型（或直接手动输入）
                        </p>
                        <div className="flex flex-wrap gap-1">
                          {currentProviderInfo.fallback_models[newConfig.model_type].map(m => (
                            <button
                              key={m}
                              type="button"
                              onClick={() => setNewConfig(prev => ({ ...prev, model_name: m }))}
                              className={`px-2 py-0.5 text-[11px] rounded border transition-colors ${
                                newConfig.model_name === m
                                  ? 'border-blue-400 bg-blue-50 text-blue-700'
                                  : 'border-gray-200 text-gray-400 hover:text-gray-600 hover:border-gray-300'
                              }`}
                            >
                              {m}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* 本地模型选择下拉 */}
                {newConfig.model_type === 'embedding' && newConfig.is_local && (
                  <div className="p-3 bg-purple-50 rounded-lg border border-purple-200">
                    <label className="block text-sm font-medium text-purple-700 mb-2">选择本地 Embedding 模型</label>
                    <select
                      value={newConfig.local_model_id}
                      onChange={(e) => handleLocalModelSelect(e.target.value)}
                      className="w-full px-4 py-2.5 bg-white border border-purple-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple-500/20"
                    >
                      <option value="">-- 请选择模型 --</option>
                      {localModels.map(model => (
                        <option key={model.id} value={model.id}>
                          {model.display_name} ({model.dimension}维, ~{model.size_mb}MB)
                        </option>
                      ))}
                    </select>
                    
                    {newConfig.local_model_id && (
                      <div className="mt-3 p-3 bg-white rounded-lg text-xs space-y-1">
                        {(() => {
                          const model = localModels.find(m => m.id === newConfig.local_model_id)
                          if (!model) return null
                          return (
                            <>
                              <div className="flex justify-between">
                                <span className="text-gray-500">模型名称：</span>
                                <span className="font-mono text-gray-800">{model.name}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-500">向量维度：</span>
                                <span className="font-medium text-purple-600">{model.dimension}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-500">模型大小：</span>
                                <span>{model.size_mb} MB</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-500">支持语言：</span>
                                <span>{model.language === 'zh' ? '中文' : model.language === 'zh+en' ? '中英双语' : model.language}</span>
                              </div>
                              <div className="pt-2 border-t">
                                <div className="text-gray-500 mb-1">模型说明：</div>
                                <div className="text-gray-700">{model.description}</div>
                                <div className="text-gray-500 mt-1">推荐场景：{model.recommended_for}</div>
                              </div>
                              <div className="mt-2 pt-2 border-t border-gray-100">
                                <p className="text-gray-500 mb-1">若模型未下载，请先在部署步骤中下载：</p>
                                <button
                                  type="button"
                                  onClick={() => handleDownloadLocalModel(model.id)}
                                  disabled={downloadingModel === model.id}
                                  className="w-full px-3 py-1.5 text-xs bg-purple-500 text-white rounded-lg hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1"
                                >
                                  <Download size={14} />
                                  {downloadingModel === model.id ? '下载中...' : '下载此模型'}
                                </button>
                              </div>
                            </>
                          )
                        })()}
                      </div>
                    )}
                  </div>
                )}

                {/* API 配置（根据 Provider 支持情况和 is_local 动态显示） */}
                {!newConfig.is_local && (
                  <>
                    {currentProviderInfo?.supports_api_key && (
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <label className="block text-sm font-medium text-gray-700">API Key</label>
                          {currentProviderInfo?.has_api_key && newConfig.api_key === currentProviderInfo.api_key && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-50 text-blue-600 text-[10px] font-medium rounded-full">
                              <KeyRound size={10} /> 继承自厂商
                            </span>
                          )}
                        </div>
                        <input
                          type="password"
                          value={newConfig.api_key}
                          onChange={(e) => setNewConfig({ ...newConfig, api_key: e.target.value })}
                          className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                          placeholder={currentProviderInfo?.code === 'ollama' ? 'Ollama 通常不需要 API Key' : 
                            (currentProviderInfo?.has_api_key ? '已自动继承厂商 Key（可手动覆盖）' : '输入 API Key')}
                        />
                        {currentProviderInfo?.has_api_key && (
                          <p className="text-[11px] text-gray-400 mt-1">留空则自动使用厂商管理中配置的 Key</p>
                        )}
                      </div>
                    )}
                    {currentProviderInfo?.code !== 'local' && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">API Base URL</label>
                        <input
                          type="text"
                          value={newConfig.api_base}
                          onChange={(e) => setNewConfig({ ...newConfig, api_base: e.target.value })}
                          className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                          placeholder={currentProviderInfo?.default_api_base || '输入 API 基础地址'}
                        />
                        {currentProviderInfo?.default_api_base && (
                          <p className="text-xs text-gray-400 mt-1">默认值已自动填充，可根据需要修改</p>
                        )}
                      </div>
                    )}
                  </>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    模型名称
                    {newConfig.is_local && (
                      <span className="text-xs text-gray-400 ml-2">（HuggingFace 模型路径）</span>
                    )}
                  </label>
                  <input
                    type="text"
                    value={newConfig.model_name}
                    onChange={(e) => setNewConfig({ ...newConfig, model_name: e.target.value })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                    placeholder={
                      newConfig.is_local
                        ? '例如：BAAI/bge-large-zh-v1.5'
                        : newConfig.model_type === 'embedding'
                        ? '例如：text-embedding-v3'
                        : newConfig.model_type === 'reranker'
                        ? '例如：jina-reranker-v2-base-multilingual'
                        : '例如：deepseek-chat'
                    }
                  />
                </div>

                {/* 维度（仅 Embedding 类型显示） */}
                {newConfig.model_type === 'embedding' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">向量维度</label>
                    <input
                      type="number"
                      value={newConfig.dimension}
                      onChange={(e) => setNewConfig({ ...newConfig, dimension: parseInt(e.target.value) || 0 })}
                      className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                      placeholder="例如：1536"
                      min={1}
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      {newConfig.is_local
                        ? '本地模型维度通常在 768~1024 之间，请根据实际模型填写'
                        : '不同模型维度不同，如 text-embedding-v3 支持 1024/768，text-embedding-3-small 为 1536'}
                    </p>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">适用场景（可选）</label>
                  <select
                    value={newConfig.scenario || ''}
                    onChange={(e) => setNewConfig({...newConfig, scenario: e.target.value})}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                  >
                    <option value="">默认（所有场景通用）</option>
                    <option value="chat">对话场景</option>
                    <option value="rag">检索增强(RAG)</option>
                    <option value="code">代码生成</option>
                    <option value="extraction">信息抽取</option>
                    <option value="creative">创意写作</option>
                  </select>
                  <p className="text-xs text-gray-400 mt-1">留空=该类型的全局默认模型</p>
                </div>

                {tenants.length > 0 && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">适用租户（可选）</label>
                    <select
                      value={newConfig.tenant_id || ''}
                      onChange={(e) => setNewConfig({...newConfig, tenant_id: e.target.value})}
                      className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                    >
                      <option value="">所有租户（全局默认）</option>
                      {tenants.map(t => (
                        <option key={t.id} value={t.id}>{t.name}</option>
                      ))}
                    </select>
                    <p className="text-xs text-gray-400 mt-1">留空=该模型类型的全局默认，选中后仅该租户使用</p>
                  </div>
                )}

                {newConfig.model_type === 'chat' && (
                  <details className="group bg-gray-50 rounded-xl border border-gray-200">
                    <summary className="px-4 py-2.5 text-sm font-medium text-gray-700 cursor-pointer select-none flex items-center gap-2">
                      <span>⚙️ 高级参数</span>
                      <span className="text-xs text-gray-400 group-open:hidden">点我展开</span>
                      <span className="text-xs text-gray-400 hidden group-open:inline">点我收起</span>
                    </summary>
                    <div className="px-4 pb-4 grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">
                          Temperature
                          <ParamHelpIcon text="控制生成随机性。0=确定（每次相同），2=高度随机。创意写作用 0.7-0.9，RAG/抽取用 0.1-0.3" />
                        </label>
                        <input type="number" step="0.1" min="0" max="2"
                          value={newConfig.temperature ?? ''}
                          onChange={(e) => setNewConfig({...newConfig, temperature: e.target.value === '' ? null : Number(e.target.value)})}
                          className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm font-mono"
                          placeholder="0.7" />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">
                          Top P
                          <ParamHelpIcon text="核采样阈值。0.9=考虑前 90% 的候选。和 Temperature 二选一，通常保持 1 只调 Temperature" />
                        </label>
                        <input type="number" step="0.01" min="0" max="1"
                          value={newConfig.top_p ?? ''}
                          onChange={(e) => setNewConfig({...newConfig, top_p: e.target.value === '' ? null : Number(e.target.value)})}
                          className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm font-mono"
                          placeholder="1" />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">
                          Max Tokens
                          <ParamHelpIcon text="单次回复最大 token 数。不填则由模型/系统限制。4096 约等于 3000 汉字" />
                        </label>
                        <input type="number" step="1" min="1"
                          value={newConfig.max_tokens ?? ''}
                          onChange={(e) => setNewConfig({...newConfig, max_tokens: e.target.value === '' ? null : Number(e.target.value)})}
                          className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm font-mono"
                          placeholder="不限制" />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">
                          Presence Penalty
                          <ParamHelpIcon text="惩罚已出现过的话题，鼓励谈论新内容。-2 到 2 之间。0.5=轻微鼓励新颖" />
                        </label>
                        <input type="number" step="0.1" min="-2" max="2"
                          value={newConfig.presence_penalty ?? ''}
                          onChange={(e) => setNewConfig({...newConfig, presence_penalty: e.target.value === '' ? null : Number(e.target.value)})}
                          className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm font-mono"
                          placeholder="0" />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">
                          Frequency Penalty
                          <ParamHelpIcon text="惩罚高频词，降低重复。-2 到 2 之间。0.5=轻微去重" />
                        </label>
                        <input type="number" step="0.1" min="-2" max="2"
                          value={newConfig.frequency_penalty ?? ''}
                          onChange={(e) => setNewConfig({...newConfig, frequency_penalty: e.target.value === '' ? null : Number(e.target.value)})}
                          className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm font-mono"
                          placeholder="0" />
                      </div>
                    </div>
                  </details>
                )}
              </div>
              <div className="flex gap-3 mt-6">
                <Button variant="secondary" onClick={() => setShowCreateModal(false)} disabled={saving}>
                  取消
                </Button>
                <Button onClick={handleCreate} disabled={saving}>
                  <Save size={18} />
                  {saving ? '保存中...' : '保存配置'}
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showEditModal && editingConfig && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => setShowEditModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="bg-white rounded-2xl p-6 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold text-gray-800 mb-6">编辑模型配置</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">配置名称</label>
                  <input
                    type="text"
                    value={newConfig.name}
                    onChange={(e) => setNewConfig({ ...newConfig, name: e.target.value })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                  />
                </div>

                {/* 模型类型（只读） */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">模型类型</label>
                  <div className="px-4 py-2.5 bg-gray-100 rounded-xl text-sm text-gray-600">
                    {MODEL_TYPE_LABELS[editingConfig.model_type] || editingConfig.model_type}
                  </div>
                </div>

                {/* Provider 选择（chat 和 embedding 都显示） */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">服务提供商</label>
                  <select
                    value={newConfig.provider}
                    onChange={(e) => {
                      const provider = providers.find(p => p.code === e.target.value)
                      setNewConfig(prev => ({
                        ...prev,
                        provider: e.target.value,
                        api_base: provider?.default_api_base || prev.api_base
                      }))
                    }}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                  >
                    {providers
                      .filter(p => p.is_active !== false && p.supported_model_types.includes(editingConfig.model_type))
                      .map(p => (
                        <option key={p.code} value={p.code}>
                          {p.display_name}
                        </option>
                      ))
                    }
                  </select>
                  {providers.find(p => p.code === newConfig.provider) && (
                    <p className="text-xs text-gray-500 mt-1 flex items-center gap-1">
                      <Info size={12} />
                      {providers.find(p => p.code === newConfig.provider)?.description}
                    </p>
                  )}
                </div>

                {/* 本地模型选项 */}
                {editingConfig.model_type === 'embedding' && newConfig.provider !== 'ollama' && providers.find(p => p.code === newConfig.provider)?.supports_local && (
                  <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg">
                    <input
                      type="checkbox"
                      id="edit_is_local"
                      checked={newConfig.is_local}
                      onChange={(e) => {
                        const isLocal = e.target.checked
                        setNewConfig({ ...newConfig, is_local: isLocal })
                        if (!isLocal) {
                          setNewConfig(prev => ({ ...prev, local_model_id: '', model_name: '', dimension: 1536 }))
                        }
                      }}
                      className="w-4 h-4 rounded border-gray-300 text-green-500 focus:ring-green-400"
                    />
                    <label htmlFor="edit_is_local" className="flex-1 text-sm text-green-700 cursor-pointer">
                      使用本地 HuggingFace 模型（免 API Key）
                    </label>
                  </div>
                )}

                {/* 本地模型选择下拉（编辑模式） */}
                {editingConfig.model_type === 'embedding' && newConfig.is_local && (
                  <div className="p-3 bg-purple-50 rounded-lg border border-purple-200">
                    <label className="block text-sm font-medium text-purple-700 mb-2">选择本地 Embedding 模型</label>
                    <select
                      value={newConfig.local_model_id}
                      onChange={(e) => handleLocalModelSelect(e.target.value)}
                      className="w-full px-4 py-2.5 bg-white border border-purple-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple-500/20"
                    >
                      <option value="">-- 请选择模型 --</option>
                      {localModels.map(model => (
                        <option key={model.id} value={model.id}>
                          {model.display_name} ({model.dimension}维, ~{model.size_mb}MB)
                        </option>
                      ))}
                    </select>
                    
                    {newConfig.local_model_id && (
                      <div className="mt-3 p-3 bg-white rounded-lg text-xs space-y-1">
                        {(() => {
                          const model = localModels.find(m => m.id === newConfig.local_model_id)
                          if (!model) return null
                          return (
                            <>
                              <div className="flex justify-between">
                                <span className="text-gray-500">模型名称：</span>
                                <span className="font-mono text-gray-800">{model.name}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-500">向量维度：</span>
                                <span className="font-medium text-purple-600">{model.dimension}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-500">模型大小：</span>
                                <span>{model.size_mb} MB</span>
                              </div>
                              <div className="pt-2 border-t">
                                <div className="text-gray-500 mb-1">模型说明：</div>
                                <div className="text-gray-700">{model.description}</div>
                              </div>
                            </>
                          )
                        })()}
                      </div>
                    )}
                  </div>
                )}

                {/* API 配置（根据 Provider 支持情况和 is_local 动态显示） */}
                {!newConfig.is_local && (
                  <>
                    {providers.find(p => p.code === newConfig.provider)?.supports_api_key && (
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <label className="block text-sm font-medium text-gray-700">API Key</label>
                          {currentProviderInfo?.has_api_key && newConfig.api_key === currentProviderInfo.api_key && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-50 text-blue-600 text-[10px] font-medium rounded-full">
                              <KeyRound size={10} /> 继承自厂商
                            </span>
                          )}
                        </div>
                        <input
                          type="password"
                          value={newConfig.api_key}
                          onChange={(e) => setNewConfig({ ...newConfig, api_key: e.target.value })}
                          className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                          placeholder={currentProviderInfo?.code === 'ollama' ? 'Ollama 通常不需要 API Key' : 
                            (currentProviderInfo?.has_api_key ? '已自动继承厂商 Key（可手动覆盖）或输入新 Key' : '输入新 API Key')}
                        />
                        <p className="text-xs text-gray-500 mt-1">当前密钥: {editingConfig.api_key_masked || '(未配置)'}</p>
                        {currentProviderInfo?.has_api_key && (
                          <p className="text-[11px] text-gray-400 mt-1">留空则保持原值，清空厂商 Key 后可手动输入</p>
                        )}
                      </div>
                    )}
                    {newConfig.provider !== 'local' && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">API Base URL</label>
                        <input
                          type="text"
                          value={newConfig.api_base}
                          onChange={(e) => setNewConfig({ ...newConfig, api_base: e.target.value })}
                          className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                        />
                      </div>
                    )}
                  </>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">模型名称</label>
                  <input
                    type="text"
                    value={newConfig.model_name}
                    onChange={(e) => setNewConfig({ ...newConfig, model_name: e.target.value })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                  />
                </div>

                {/* 维度（仅 Embedding 类型显示） */}
                {editingConfig.model_type === 'embedding' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">向量维度</label>
                    <input
                      type="number"
                      value={newConfig.dimension}
                      onChange={(e) => setNewConfig({ ...newConfig, dimension: parseInt(e.target.value) || 0 })}
                      className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                      min={1}
                    />
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">适用场景（可选）</label>
                  <select
                    value={newConfig.scenario || ''}
                    onChange={(e) => setNewConfig({...newConfig, scenario: e.target.value})}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                  >
                    <option value="">默认（所有场景通用）</option>
                    <option value="chat">对话场景</option>
                    <option value="rag">检索增强(RAG)</option>
                    <option value="code">代码生成</option>
                    <option value="extraction">信息抽取</option>
                    <option value="creative">创意写作</option>
                  </select>
                  <p className="text-xs text-gray-400 mt-1">留空=该类型的全局默认模型</p>
                </div>

                {tenants.length > 0 && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">适用租户（可选）</label>
                    <select
                      value={newConfig.tenant_id || ''}
                      onChange={(e) => setNewConfig({...newConfig, tenant_id: e.target.value})}
                      className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                    >
                      <option value="">所有租户（全局默认）</option>
                      {tenants.map(t => (
                        <option key={t.id} value={t.id}>{t.name}</option>
                      ))}
                    </select>
                    <p className="text-xs text-gray-400 mt-1">留空=该模型类型的全局默认，选中后仅该租户使用</p>
                  </div>
                )}

                {editingConfig.model_type === 'chat' && (
                  <details className="group bg-gray-50 rounded-xl border border-gray-200">
                    <summary className="px-4 py-2.5 text-sm font-medium text-gray-700 cursor-pointer select-none flex items-center gap-2">
                      <span>⚙️ 高级参数</span>
                      <span className="text-xs text-gray-400 group-open:hidden">点我展开</span>
                      <span className="text-xs text-gray-400 hidden group-open:inline">点我收起</span>
                    </summary>
                    <div className="px-4 pb-4 grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">
                          Temperature
                          <ParamHelpIcon text="控制生成随机性。0=确定（每次相同），2=高度随机。创意写作用 0.7-0.9，RAG/抽取用 0.1-0.3" />
                        </label>
                        <input type="number" step="0.1" min="0" max="2"
                          value={newConfig.temperature ?? ''}
                          onChange={(e) => setNewConfig({...newConfig, temperature: e.target.value === '' ? null : Number(e.target.value)})}
                          className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm font-mono"
                          placeholder="0.7" />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">
                          Top P
                          <ParamHelpIcon text="核采样阈值。0.9=考虑前 90% 的候选。和 Temperature 二选一，通常保持 1 只调 Temperature" />
                        </label>
                        <input type="number" step="0.01" min="0" max="1"
                          value={newConfig.top_p ?? ''}
                          onChange={(e) => setNewConfig({...newConfig, top_p: e.target.value === '' ? null : Number(e.target.value)})}
                          className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm font-mono"
                          placeholder="1" />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">
                          Max Tokens
                          <ParamHelpIcon text="单次回复最大 token 数。不填则由模型/系统限制。4096 约等于 3000 汉字" />
                        </label>
                        <input type="number" step="1" min="1"
                          value={newConfig.max_tokens ?? ''}
                          onChange={(e) => setNewConfig({...newConfig, max_tokens: e.target.value === '' ? null : Number(e.target.value)})}
                          className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm font-mono"
                          placeholder="不限制" />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">
                          Presence Penalty
                          <ParamHelpIcon text="惩罚已出现过的话题，鼓励谈论新内容。-2 到 2 之间。0.5=轻微鼓励新颖" />
                        </label>
                        <input type="number" step="0.1" min="-2" max="2"
                          value={newConfig.presence_penalty ?? ''}
                          onChange={(e) => setNewConfig({...newConfig, presence_penalty: e.target.value === '' ? null : Number(e.target.value)})}
                          className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm font-mono"
                          placeholder="0" />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">
                          Frequency Penalty
                          <ParamHelpIcon text="惩罚高频词，降低重复。-2 到 2 之间。0.5=轻微去重" />
                        </label>
                        <input type="number" step="0.1" min="-2" max="2"
                          value={newConfig.frequency_penalty ?? ''}
                          onChange={(e) => setNewConfig({...newConfig, frequency_penalty: e.target.value === '' ? null : Number(e.target.value)})}
                          className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm font-mono"
                          placeholder="0" />
                      </div>
                    </div>
                  </details>
                )}
              </div>
              <div className="flex gap-3 mt-6">
                <Button variant="secondary" onClick={() => setShowEditModal(false)} disabled={saving}>
                  取消
                </Button>
                <Button onClick={handleSave} disabled={saving}>
                  <Save size={18} />
                  {saving ? '保存中...' : '保存配置'}
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default ModelManagement
