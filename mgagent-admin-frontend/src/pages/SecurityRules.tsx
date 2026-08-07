import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Shield, Plus, Trash2, Power, Edit3, RefreshCw, FlaskConical, AlertTriangle, CheckCircle } from 'lucide-react'
import Button from '../components/Button'
import { securityApi } from '../api/client'
import { toast, getErrorMessage } from '../components/Toast'
import type { SecurityRule, SecurityTestResult } from '../api/client'

const SecurityRules = () => {
  const [rules, setRules] = useState<SecurityRule[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingRule, setEditingRule] = useState<SecurityRule | null>(null)
  const [saving, setSaving] = useState(false)
  const [testContent, setTestContent] = useState('')
  const [testResult, setTestResult] = useState<SecurityTestResult | null>(null)
  const [testing, setTesting] = useState(false)

  const [formData, setFormData] = useState({
    rule_type: 'keyword' as 'keyword' | 'regex',
    content: '',
    action: 'mask' as 'block' | 'mask',
    priority: 0,
    description: '',
  })

  useEffect(() => {
    loadRules()
  }, [])

  const loadRules = async () => {
    try {
      setLoading(true)
      const data = await securityApi.getRules()
      setRules(data)
    } catch (error) {
      toast.error(`加载安全规则失败: ${getErrorMessage(error)}`)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setEditingRule(null)
    setFormData({
      rule_type: 'keyword',
      content: '',
      action: 'mask',
      priority: 0,
      description: '',
    })
    setShowModal(true)
  }

  const handleEdit = (rule: SecurityRule) => {
    setEditingRule(rule)
    setFormData({
      rule_type: rule.rule_type,
      content: rule.content,
      action: rule.action,
      priority: rule.priority,
      description: rule.description || '',
    })
    setShowModal(true)
  }

  const handleSave = async () => {
    if (!formData.content.trim()) {
      toast.warning('请输入规则内容')
      return
    }
    try {
      setSaving(true)
      if (editingRule) {
        await securityApi.updateRule(editingRule.id, formData)
        toast.success('安全规则更新成功')
      } else {
        await securityApi.createRule(formData)
        toast.success('安全规则创建成功')
      }
      setShowModal(false)
      loadRules()
    } catch (error) {
      toast.error(`保存失败: ${getErrorMessage(error)}`)
    } finally {
      setSaving(false)
    }
  }

  const handleToggle = async (ruleId: string) => {
    try {
      await securityApi.toggleRule(ruleId)
      toast.success('规则状态已切换')
      loadRules()
    } catch (error) {
      toast.error(`操作失败: ${getErrorMessage(error)}`)
    }
  }

  const handleDelete = async (ruleId: string) => {
    if (!window.confirm('确定要删除这条安全规则吗？')) return
    try {
      await securityApi.deleteRule(ruleId)
      toast.success('安全规则已删除')
      loadRules()
    } catch (error) {
      toast.error(`删除失败: ${getErrorMessage(error)}`)
    }
  }

  const handleTest = async () => {
    if (!testContent.trim()) {
      toast.warning('请输入测试内容')
      return
    }
    try {
      setTesting(true)
      const result = await securityApi.testFilter(testContent)
      setTestResult(result)
    } catch (error) {
      toast.error(`测试失败: ${getErrorMessage(error)}`)
    } finally {
      setTesting(false)
    }
  }

  const activeCount = rules.filter(r => r.is_active).length
  const blockCount = rules.filter(r => r.is_active && r.action === 'block').length
  const maskCount = rules.filter(r => r.is_active && r.action === 'mask').length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-red-100 rounded-xl">
            <Shield size={20} className="text-red-500" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-800">安全规则管理</h2>
            <p className="text-sm text-gray-500">管理 LLM 输出安全过滤规则</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="secondary" onClick={loadRules} disabled={loading}>
            <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
            刷新
          </Button>
          <Button onClick={handleCreate}>
            <Plus size={18} />
            添加规则
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-500">总规则数</span>
            <Shield size={18} className="text-gray-400" />
          </div>
          <p className="text-2xl font-bold text-gray-800">{rules.length}</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-500">已启用</span>
            <div className="w-2 h-2 rounded-full bg-green-500" />
          </div>
          <p className="text-2xl font-bold text-green-600">{activeCount}</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-500">拦截规则</span>
            <AlertTriangle size={18} className="text-red-400" />
          </div>
          <p className="text-2xl font-bold text-red-500">{blockCount}</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-500">脱敏规则</span>
            <CheckCircle size={18} className="text-blue-400" />
          </div>
          <p className="text-2xl font-bold text-blue-500">{maskCount}</p>
        </motion.div>
      </div>

      {/* Rules List */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
        <h3 className="font-semibold text-gray-800 mb-4">规则列表</h3>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-500 rounded-full animate-spin" />
          </div>
        ) : rules.length === 0 ? (
          <div className="text-center py-12">
            <Shield size={40} className="text-gray-300 mx-auto mb-3" />
            <p className="text-gray-400">暂无安全规则</p>
            <button
              onClick={handleCreate}
              className="mt-3 text-primary-500 hover:text-primary-600 text-sm font-medium"
            >
              添加第一条规则
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {rules.map((rule, index) => (
              <motion.div
                key={rule.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.03 }}
                className={`p-4 rounded-xl border transition-all ${
                  rule.is_active
                    ? 'border-gray-200 bg-white'
                    : 'border-gray-100 bg-gray-50 opacity-60'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        rule.rule_type === 'regex'
                          ? 'bg-purple-100 text-purple-600'
                          : 'bg-blue-100 text-blue-600'
                      }`}>
                        {rule.rule_type === 'regex' ? '正则' : '关键词'}
                      </span>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        rule.action === 'block'
                          ? 'bg-red-100 text-red-600'
                          : 'bg-yellow-100 text-yellow-600'
                      }`}>
                        {rule.action === 'block' ? '拦截' : '脱敏'}
                      </span>
                      <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-500 rounded-full">
                        优先级 {rule.priority}
                      </span>
                      <div className={`w-2 h-2 rounded-full ${rule.is_active ? 'bg-green-500' : 'bg-gray-400'}`} />
                      <span className="text-xs text-gray-400">{rule.is_active ? '启用' : '停用'}</span>
                    </div>
                    <p className="text-sm font-mono text-gray-800 bg-gray-50 px-3 py-2 rounded-lg break-all">
                      {rule.content}
                    </p>
                    {rule.description && (
                      <p className="text-xs text-gray-500 mt-2">{rule.description}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-2 ml-4">
                    <button
                      onClick={() => handleToggle(rule.id)}
                      className={`p-2 rounded-lg transition-colors ${
                        rule.is_active
                          ? 'text-green-600 hover:bg-green-50'
                          : 'text-gray-400 hover:bg-gray-100'
                      }`}
                      title={rule.is_active ? '停用' : '启用'}
                    >
                      <Power size={16} />
                    </button>
                    <button
                      onClick={() => handleEdit(rule)}
                      className="p-2 rounded-lg text-gray-500 hover:bg-gray-100"
                      title="编辑"
                    >
                      <Edit3 size={16} />
                    </button>
                    <button
                      onClick={() => handleDelete(rule.id)}
                      className="p-2 rounded-lg text-red-500 hover:bg-red-50"
                      title="删除"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Test Section */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
        <div className="flex items-center gap-2 mb-4">
          <FlaskConical size={18} className="text-primary-500" />
          <h3 className="font-semibold text-gray-800">过滤测试</h3>
        </div>
        <p className="text-sm text-gray-500 mb-4">输入一段文本，测试内置安全规则的过滤效果（不包含自定义规则）</p>
        <div className="space-y-4">
          <textarea
            value={testContent}
            onChange={(e) => setTestContent(e.target.value)}
            className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 resize-none"
            rows={4}
            placeholder="输入需要测试的文本内容，例如：我的手机号是13800138000，邮箱是test@example.com"
          />
          <Button onClick={handleTest} disabled={testing}>
            <FlaskConical size={18} />
            {testing ? '测试中...' : '执行测试'}
          </Button>

          {testResult && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-3"
            >
              <div className={`p-4 rounded-xl ${
                testResult.has_sensitive
                  ? 'bg-yellow-50 border border-yellow-200'
                  : 'bg-green-50 border border-green-200'
              }`}>
                <div className="flex items-center gap-2 mb-2">
                  {testResult.has_sensitive ? (
                    <AlertTriangle size={18} className="text-yellow-600" />
                  ) : (
                    <CheckCircle size={18} className="text-green-600" />
                  )}
                  <span className={`font-medium ${
                    testResult.has_sensitive ? 'text-yellow-800' : 'text-green-800'
                  }`}>
                    {testResult.has_sensitive
                      ? `检测到 ${testResult.matched_rules.length} 条敏感内容`
                      : '未检测到敏感内容'}
                  </span>
                </div>

                {testResult.matched_rules.length > 0 && (
                  <div className="space-y-1 mb-3">
                    {testResult.matched_rules.map((match, i) => (
                      <div key={i} className="text-xs text-yellow-700 flex items-center gap-2">
                        <span className="px-1.5 py-0.5 bg-yellow-200 rounded">{match.type}</span>
                        <span className="font-mono truncate">{match.content}</span>
                      </div>
                    ))}
                  </div>
                )}

                <div className="mt-2">
                  <p className="text-xs text-gray-500 mb-1">过滤结果：</p>
                  <p className="text-sm text-gray-800 bg-white px-3 py-2 rounded-lg border border-gray-100">
                    {testResult.filtered}
                  </p>
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </div>

      {/* Info Panel */}
      <div className="bg-blue-50 rounded-2xl p-5">
        <h4 className="font-medium text-blue-800 mb-3 flex items-center gap-2">
          <Shield size={16} />
          安全规则说明
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-600">
          <div>
            <p className="font-medium mb-1">规则类型</p>
            <ul className="space-y-1 text-xs">
              <li>- <b>关键词</b>：匹配文本中的敏感词，不区分大小写</li>
              <li>- <b>正则</b>：使用正则表达式进行模式匹配，可识别邮箱、手机号等</li>
            </ul>
          </div>
          <div>
            <p className="font-medium mb-1">处理动作</p>
            <ul className="space-y-1 text-xs">
              <li>- <b>拦截(block)</b>：直接阻止内容输出，返回安全提示</li>
              <li>- <b>脱敏(mask)</b>：将敏感内容替换为 [已过滤] 标记</li>
            </ul>
          </div>
          <div>
            <p className="font-medium mb-1">优先级</p>
            <p className="text-xs">数字越大优先级越高，高优先级规则先执行</p>
          </div>
          <div>
            <p className="font-medium mb-1">双层架构</p>
            <p className="text-xs">系统内置硬编码规则 + 数据库可配置规则，确保核心安全</p>
          </div>
        </div>
      </div>

      {/* Create/Edit Modal */}
      <AnimatePresence>
        {showModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => setShowModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="bg-white rounded-2xl p-6 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold text-gray-800 mb-6">
                {editingRule ? '编辑安全规则' : '添加安全规则'}
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">规则类型</label>
                  <div className="flex gap-3">
                    <button
                      onClick={() => setFormData({ ...formData, rule_type: 'keyword' })}
                      className={`flex-1 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
                        formData.rule_type === 'keyword'
                          ? 'bg-primary-500 text-white'
                          : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      关键词匹配
                    </button>
                    <button
                      onClick={() => setFormData({ ...formData, rule_type: 'regex' })}
                      className={`flex-1 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
                        formData.rule_type === 'regex'
                          ? 'bg-primary-500 text-white'
                          : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      正则表达式
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {formData.rule_type === 'keyword' ? '关键词' : '正则表达式'}
                  </label>
                  <input
                    type="text"
                    value={formData.content}
                    onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 font-mono"
                    placeholder={formData.rule_type === 'keyword'
                      ? '例如：系统提示词'
                      : '例如：\\b1[3-9]\\d{9}\\b'
                    }
                  />
                  {formData.rule_type === 'regex' && (
                    <p className="text-xs text-gray-500 mt-1">使用 Python re 语法，不区分大小写</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">处理动作</label>
                  <div className="flex gap-3">
                    <button
                      onClick={() => setFormData({ ...formData, action: 'mask' })}
                      className={`flex-1 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
                        formData.action === 'mask'
                          ? 'bg-yellow-500 text-white'
                          : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      脱敏（替换内容）
                    </button>
                    <button
                      onClick={() => setFormData({ ...formData, action: 'block' })}
                      className={`flex-1 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
                        formData.action === 'block'
                          ? 'bg-red-500 text-white'
                          : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      拦截（阻止输出）
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">优先级</label>
                  <input
                    type="number"
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) || 0 })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                    placeholder="0"
                  />
                  <p className="text-xs text-gray-500 mt-1">数字越大优先级越高，先执行</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">描述（可选）</label>
                  <input
                    type="text"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                    placeholder="规则的用途说明"
                  />
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <Button variant="secondary" onClick={() => setShowModal(false)} disabled={saving}>
                  取消
                </Button>
                <Button onClick={handleSave} disabled={saving}>
                  {saving ? '保存中...' : '保存规则'}
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default SecurityRules
