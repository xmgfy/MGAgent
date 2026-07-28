import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Cpu, Save, RefreshCw, CheckCircle, XCircle, ExternalLink, Plus, Trash2, Power, Eye, EyeOff } from 'lucide-react'
import Button from '../components/Button'
import { modelApi } from '../api/client'
import { toast, getErrorMessage } from '../components/Toast'
import type { ModelConfig } from '../api/client'

const ModelManagement = () => {
  const [configs, setConfigs] = useState<ModelConfig[]>([])
  const [activeConfig, setActiveConfig] = useState<ModelConfig | null>(null)
  const [saving, setSaving] = useState(false)
  const [testResult, setTestResult] = useState<{ status: string; response?: string; error?: string } | null>(null)
  const [testing, setTesting] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [editingConfig, setEditingConfig] = useState<ModelConfig | null>(null)
  const [newConfig, setNewConfig] = useState({ name: '', api_key: '', api_base: '', model_name: '' })
  const [showApiKey, setShowApiKey] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const configsData = await modelApi.getConfigs()
      setConfigs(configsData)
      const active = configsData.find(c => c.is_active)
      setActiveConfig(active || null)
    } catch (error) {
      toast.error(`加载模型列表失败: ${getErrorMessage(error)}`)
    }
  }

  const handleSave = async () => {
    if (!editingConfig) return
    try {
      setSaving(true)
      await modelApi.updateConfig(editingConfig.id, {
        api_key: newConfig.api_key || undefined,
        api_base: newConfig.api_base || undefined,
        model_name: newConfig.model_name || undefined
      })
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
    if (!newConfig.name || !newConfig.api_key || !newConfig.api_base || !newConfig.model_name) {
      toast.warning('请填写所有必填字段')
      return
    }
    try {
      setSaving(true)
      await modelApi.createConfig(newConfig)
      setSaving(false)
      setShowCreateModal(false)
      setNewConfig({ name: '', api_key: '', api_base: '', model_name: '' })
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
    setNewConfig({
      name: config.name,
      api_key: '',
      api_base: config.api_base,
      model_name: config.model_name
    })
    setShowEditModal(true)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-orange-100 rounded-xl">
            <Cpu size={20} className="text-orange-500" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-800">模型管理</h2>
            <p className="text-sm text-gray-500">配置和管理 AI 模型</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="secondary" onClick={loadData}>
            <RefreshCw size={18} />
            刷新
          </Button>
          <Button onClick={() => setShowCreateModal(true)}>
            <Plus size={18} />
            添加模型
          </Button>
        </div>
      </div>

      {activeConfig && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-r from-primary-500 to-accent-500 rounded-2xl p-6 text-white"
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Power size={20} className="text-green-300" />
                <span className="text-sm font-medium text-green-100">当前启用模型</span>
              </div>
              <h3 className="text-2xl font-bold">{activeConfig.name}</h3>
              <p className="text-sm text-primary-100 mt-1">{activeConfig.model_name}</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-primary-100">API 地址</p>
              <p className="font-medium">{activeConfig.api_base}</p>
              <div className="flex items-center gap-2 mt-2">
                <button
                  onClick={() => setShowApiKey(!showApiKey)}
                  className="text-primary-100 hover:text-white"
                >
                  {showApiKey ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
                <span className="text-sm font-mono">{showApiKey ? activeConfig.api_key : activeConfig.api_key_masked}</span>
              </div>
            </div>
          </div>
          <div className="mt-4 flex gap-3">
            <Button variant="white" onClick={handleTest} disabled={testing}>
              {testing ? '测试中...' : '测试连接'}
            </Button>
            <Button variant="white-secondary" onClick={() => handleEdit(activeConfig)}>
              编辑配置
            </Button>
            <Button variant="white-secondary" onClick={() => handleDeactivate(activeConfig.id)} className="text-red-600 hover:text-red-700">
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

      {!activeConfig && configs.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-yellow-50 border border-yellow-200 rounded-2xl p-6"
        >
          <p className="text-yellow-800 font-medium">未启用任何模型，请选择一个模型配置并启用。</p>
        </motion.div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6"
        >
          <h3 className="font-semibold text-gray-800 mb-4">已配置模型</h3>
          
          {configs.length === 0 ? (
            <div className="text-center py-8">
              <Cpu size={40} className="text-gray-300 mx-auto mb-3" />
              <p className="text-gray-400">暂无模型配置</p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="mt-3 text-primary-500 hover:text-primary-600 text-sm font-medium"
              >
                添加第一个模型
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {configs.map((config) => (
                <motion.div
                  key={config.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className={`p-4 rounded-xl border transition-all ${
                    config.is_active
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-100 hover:border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full ${config.is_active ? 'bg-green-500' : 'bg-gray-400'}`} />
                      <div>
                        <div className="flex items-center gap-2">
                          <p className={`font-medium ${config.is_active ? 'text-primary-600' : 'text-gray-800'}`}>
                            {config.name}
                          </p>
                          {config.is_active && (
                            <span className="text-xs px-2 py-0.5 bg-green-100 text-green-600 rounded-full">启用中</span>
                          )}
                        </div>
                        <p className="text-sm text-gray-500 truncate">{config.model_name}</p>
                      </div>
                    </div>
                    <ExternalLink size={16} className="text-gray-400" />
                  </div>
                  <div className="mt-2 text-xs text-gray-400 truncate">{config.api_base}</div>
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
          
          {activeConfig ? (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="p-4 bg-gray-50 rounded-xl">
                <p className="text-sm text-gray-500 mb-1">当前模型</p>
                <p className="font-medium text-gray-800">{activeConfig.name}</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-xl">
                <p className="text-sm text-gray-500 mb-1">模型名称</p>
                <p className="font-medium text-gray-800">{activeConfig.model_name}</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-xl">
                <p className="text-sm text-gray-500 mb-1">API 地址</p>
                <p className="font-medium text-gray-800 truncate">{activeConfig.api_base}</p>
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
              <p className="text-gray-400">请配置并启用一个模型</p>
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

      <AnimatePresence>
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
              className="bg-white rounded-2xl p-6 w-full max-w-md mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold text-gray-800 mb-6">添加模型配置</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">配置名称</label>
                  <input
                    type="text"
                    value={newConfig.name}
                    onChange={(e) => setNewConfig({ ...newConfig, name: e.target.value })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                    placeholder="例如：DeepSeek"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">API Key</label>
                  <input
                    type="password"
                    value={newConfig.api_key}
                    onChange={(e) => setNewConfig({ ...newConfig, api_key: e.target.value })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                    placeholder="输入 API Key"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">API Base URL</label>
                  <input
                    type="text"
                    value={newConfig.api_base}
                    onChange={(e) => setNewConfig({ ...newConfig, api_base: e.target.value })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                    placeholder="输入 API 基础地址"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">模型名称</label>
                  <input
                    type="text"
                    value={newConfig.model_name}
                    onChange={(e) => setNewConfig({ ...newConfig, model_name: e.target.value })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                    placeholder="例如：deepseek-chat"
                  />
                </div>
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
              className="bg-white rounded-2xl p-6 w-full max-w-md mx-4"
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
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">API Key</label>
                  <div className="relative">
                    <input
                      type="password"
                      value={newConfig.api_key}
                      onChange={(e) => setNewConfig({ ...newConfig, api_key: e.target.value })}
                      className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                      placeholder="留空则不修改"
                    />
                    <button
                      type="button"
                      onClick={() => setShowApiKey(!showApiKey)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400"
                    >
                      {showApiKey ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">当前: {editingConfig.api_key_masked}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">API Base URL</label>
                  <input
                    type="text"
                    value={newConfig.api_base}
                    onChange={(e) => setNewConfig({ ...newConfig, api_base: e.target.value })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">模型名称</label>
                  <input
                    type="text"
                    value={newConfig.model_name}
                    onChange={(e) => setNewConfig({ ...newConfig, model_name: e.target.value })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                  />
                </div>
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
