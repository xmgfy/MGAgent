import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { FileText, Box, Database, Cpu, Activity, Server, CheckCircle } from 'lucide-react'
import StatsCard from '../components/StatsCard'
import { knowledgeBaseApi, vectorDbApi, storageDbApi, systemApi, dashboardApi } from '../api/client'
import type { KnowledgeBaseStats, VectorDBStats, StorageDBStats, SystemInfo, DashboardStats } from '../api/client'

const Dashboard = () => {
  const [loading, setLoading] = useState(true)
  const [kbStats, setKbStats] = useState<KnowledgeBaseStats>({ total_documents: 0, total_files: 0, total_size: 0, indexed_count: 0, file_types: {} })
  const [vectorStats, setVectorStats] = useState<VectorDBStats>({ total_chunks: 0, persist_directory: '', embedding_model: '' })
  const [storageStats, setStorageStats] = useState<StorageDBStats>({ database_path: '', tables: [], total_records: {} })
  const [systemInfo, setSystemInfo] = useState<SystemInfo>({ platform: '', python_version: '', cpu_count: 0, memory_usage: 0, disk_usage: 0 })
  const [dashboardStats, setDashboardStats] = useState<DashboardStats>({ model_calls: 0, total_sessions: 0, total_users: 0 })

  useEffect(() => {
    const loadData = async () => {
      try {
        const [kb, vector, storage, system, dashboard] = await Promise.all([
          knowledgeBaseApi.getStats(),
          vectorDbApi.getStats(),
          storageDbApi.getStats(),
          systemApi.getInfo(),
          dashboardApi.getStats(),
        ])
        setKbStats(kb)
        setVectorStats(vector)
        setStorageStats(storage)
        setSystemInfo(system)
        setDashboardStats(dashboard)
      } catch (error) {
        console.error('Failed to load dashboard data:', error)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const totalRecords = Object.values(storageStats.total_records).reduce((a: number, b: number) => a + b, 0)

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="w-8 h-8 border-4 border-primary-200 border-t-primary-500 rounded-full"
        />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          icon={FileText}
          title="知识库文档"
          value={kbStats.total_files}
          color="blue"
        />
        <StatsCard
          icon={Box}
          title="向量块数量"
          value={vectorStats.total_chunks}
          color="green"
        />
        <StatsCard
          icon={Database}
          title="数据库记录"
          value={totalRecords}
          color="purple"
        />
        <StatsCard
          icon={Cpu}
          title="模型调用次数"
          value={dashboardStats.model_calls}
          color="orange"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100"
        >
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Activity size={20} className="text-blue-500" />
            系统资源
          </h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">CPU 使用率</span>
                <span className="text-gray-800 font-medium">{systemInfo.cpu_count} 核</span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${systemInfo.cpu_count * 10}%` }}
                  className="h-full bg-gradient-to-r from-blue-400 to-blue-600 rounded-full"
                />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">内存使用率</span>
                <span className="text-gray-800 font-medium">{systemInfo.memory_usage}%</span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${systemInfo.memory_usage}%` }}
                  className="h-full bg-gradient-to-r from-green-400 to-green-600 rounded-full"
                />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">磁盘使用率</span>
                <span className="text-gray-800 font-medium">{systemInfo.disk_usage}%</span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${systemInfo.disk_usage}%` }}
                  className="h-full bg-gradient-to-r from-orange-400 to-orange-600 rounded-full"
                />
              </div>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100"
        >
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Server size={20} className="text-green-500" />
            服务状态
          </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-green-50 rounded-xl">
              <span className="text-gray-700">主服务 (mgagent-backend)</span>
              <CheckCircle size={20} className="text-green-500" />
            </div>
            <div className="flex items-center justify-between p-3 bg-green-50 rounded-xl">
              <span className="text-gray-700">管理服务 (mgagent-admin-backend)</span>
              <CheckCircle size={20} className="text-green-500" />
            </div>
            <div className="flex items-center justify-between p-3 bg-green-50 rounded-xl">
              <span className="text-gray-700">向量数据库 (Milvus)</span>
              <CheckCircle size={20} className="text-green-500" />
            </div>
            <div className="flex items-center justify-between p-3 bg-green-50 rounded-xl">
              <span className="text-gray-700">关系数据库 (MySQL)</span>
              <CheckCircle size={20} className="text-green-500" />
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100"
        >
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <FileText size={20} className="text-purple-500" />
            知识库概览
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">总文件数</span>
              <span className="text-xl font-bold text-gray-800">{kbStats.total_files}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">总大小</span>
              <span className="text-xl font-bold text-gray-800">{formatSize(kbStats.total_size)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">已索引块数</span>
              <span className="text-xl font-bold text-gray-800">{kbStats.indexed_count}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">索引覆盖率</span>
              <span className="text-xl font-bold text-green-500">100%</span>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

export default Dashboard