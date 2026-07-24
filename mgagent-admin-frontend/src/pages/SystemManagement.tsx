import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Server, Cpu, HardDrive, Activity, Clock, Globe, RefreshCw } from 'lucide-react'
import Button from '../components/Button'
import { systemApi } from '../api/client'
import type { SystemStatus, SystemInfo } from '../api/client'

const SystemManagement = () => {
  const [status, setStatus] = useState<SystemStatus>({ status: '', version: '', uptime: '' })
  const [info, setInfo] = useState<SystemInfo>({ platform: '', python_version: '', cpu_count: 0, memory_usage: 0, disk_usage: 0 })
  const [loading, setLoading] = useState(true)
  const [currentTime, setCurrentTime] = useState(new Date())

  useEffect(() => {
    loadData()
    const timer = setInterval(() => setCurrentTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [statusData, infoData] = await Promise.all([
        systemApi.getStatus(),
        systemApi.getInfo(),
      ])
      setStatus(statusData)
      setInfo(infoData)
    } catch (error) {
      console.error('Failed to load system data:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatTime = (date: Date) => {
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  }

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
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gray-100 rounded-xl">
            <Server size={20} className="text-gray-500" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-800">监控管理</h2>
              <p className="text-sm text-gray-500">系统状态和资源监控</p>
          </div>
        </div>
        <Button variant="secondary" onClick={loadData}>
          <RefreshCw size={18} />
          刷新
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-xl p-4 shadow-sm border border-gray-100"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <Activity size={20} className="text-green-500" />
            </div>
            <div>
              <p className="text-sm text-gray-500">系统状态</p>
              <p className="text-lg font-bold text-green-500">{status.status}</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-xl p-4 shadow-sm border border-gray-100"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <Globe size={20} className="text-blue-500" />
            </div>
            <div>
              <p className="text-sm text-gray-500">版本</p>
              <p className="text-lg font-bold text-gray-800">{status.version}</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-xl p-4 shadow-sm border border-gray-100"
        >
          <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                <Clock size={20} className="text-purple-500" />
              </div>
              <div>
                <p className="text-sm text-gray-500">运行时间</p>
                <p className="text-lg font-bold text-gray-800">{status.uptime}</p>
              </div>
            </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white rounded-xl p-4 shadow-sm border border-gray-100"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
              <Cpu size={20} className="text-orange-500" />
            </div>
            <div>
              <p className="text-sm text-gray-500">CPU 核心</p>
              <p className="text-lg font-bold text-gray-800">{info.cpu_count}</p>
            </div>
          </div>
        </motion.div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6"
        >
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Activity size={18} className="text-blue-500" />
            资源监控
          </h3>

          <div className="space-y-6">
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-gray-600">内存使用率</span>
                <span className="text-sm font-medium text-gray-800">{info.memory_usage}%</span>
              </div>
              <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${info.memory_usage}%` }}
                  transition={{ duration: 1 }}
                  className="h-full bg-gradient-to-r from-blue-400 to-blue-600 rounded-full"
                />
              </div>
              <p className="text-xs text-gray-400 mt-1">建议保持在 80% 以下</p>
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-gray-600">磁盘使用率</span>
                <span className="text-sm font-medium text-gray-800">{info.disk_usage}%</span>
              </div>
              <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${info.disk_usage}%` }}
                  transition={{ duration: 1 }}
                  className={`h-full rounded-full ${
                    info.disk_usage > 80 ? 'bg-gradient-to-r from-red-400 to-red-600' : 'bg-gradient-to-r from-green-400 to-green-600'
                  }`}
                />
              </div>
              <p className={`text-xs mt-1 ${info.disk_usage > 80 ? 'text-red-500' : 'text-gray-400'}`}>
                {info.disk_usage > 80 ? '磁盘空间不足，请及时清理' : '磁盘空间充足'}
              </p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6"
        >
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Server size={18} className="text-gray-500" />
            系统信息
          </h3>

          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
              <div className="flex items-center gap-3">
                <Globe size={16} className="text-gray-400" />
                <span className="text-gray-600">操作系统</span>
              </div>
              <span className="font-medium text-gray-800">{info.platform}</span>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
              <div className="flex items-center gap-3">
                <Cpu size={16} className="text-gray-400" />
                <span className="text-gray-600">Python 版本</span>
              </div>
              <span className="font-medium text-gray-800">{info.python_version}</span>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
              <div className="flex items-center gap-3">
                <HardDrive size={16} className="text-gray-400" />
                <span className="text-gray-600">CPU 核心数</span>
              </div>
              <span className="font-medium text-gray-800">{info.cpu_count}</span>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
              <div className="flex items-center gap-3">
                <Clock size={16} className="text-gray-400" />
                <span className="text-gray-600">当前时间</span>
              </div>
              <span className="font-medium text-gray-800">{formatTime(currentTime)}</span>
            </div>
          </div>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-r from-primary-500 to-primary-600 rounded-2xl p-6 text-white"
      >
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">MGAgent 智能体系统</h3>
            <p className="text-primary-100 text-sm mt-1">版本 {status.version}</p>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold">运行正常</p>
            <p className="text-primary-100 text-sm mt-1">所有服务均已启动</p>
          </div>
        </div>
      </motion.div>
    </div>
  )
}

export default SystemManagement