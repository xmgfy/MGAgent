import { useState, useEffect } from 'react'
import Sidebar from './components/Layout/Sidebar'
import Header from './components/Layout/Header'
import Dashboard from './pages/Dashboard'
import KnowledgeBase from './pages/KnowledgeBase'
import VectorDB from './pages/VectorDB'
import StorageDB from './pages/StorageDB'
import ModelManagement from './pages/ModelManagement'
import SystemManagement from './pages/SystemManagement'
import UserManagement from './pages/UserManagement'
import SecurityRules from './pages/SecurityRules'
import Login from './pages/Login'
import { authApi, type Admin } from './api/client'

const pageConfig: Record<string, { title: string; subtitle?: string }> = {
  'dashboard': { title: '概览', subtitle: '系统总览和关键指标' },
  'knowledge-base': { title: '知识库管理', subtitle: '管理文档和知识内容' },
  'vector-db': { title: '向量数据库', subtitle: '管理向量索引和搜索' },
  'storage-db': { title: '存储数据库', subtitle: '管理 MySQL 数据库' },
  'model': { title: '配置管理', subtitle: '厂商和模型配置' },
  'users': { title: '用户管理', subtitle: '管理系统用户和权限审批' },
  'security': { title: '安全规则', subtitle: '管理 LLM 输出安全过滤规则' },
  'system': { title: '监控管理', subtitle: '系统状态和资源监控' },
}

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [admin, setAdmin] = useState<Admin | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      const currentAdmin = await authApi.getCurrentAdmin()
      setAdmin(currentAdmin)
    } catch (error) {
      console.error('Auth check failed:', error)
      setAdmin(null)
    } finally {
      setLoading(false)
    }
  }

  const handleLoginSuccess = (loggedInAdmin: Admin) => {
    setAdmin(loggedInAdmin)
    localStorage.setItem('admin_info', JSON.stringify(loggedInAdmin))
  }

  const handleLogout = () => {
    authApi.logout()
    setAdmin(null)
    setActiveTab('dashboard')
  }

  const renderPage = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />
      case 'knowledge-base':
        return <KnowledgeBase />
      case 'vector-db':
        return <VectorDB />
      case 'storage-db':
        return <StorageDB />
      case 'model':
        return <ModelManagement />
      case 'users':
        return <UserManagement />
      case 'security':
        return <SecurityRules />
      case 'system':
        return <SystemManagement />
      default:
        return <Dashboard />
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-500 rounded-full animate-spin" />
      </div>
    )
  }

  if (!admin) {
    return <Login onLoginSuccess={handleLoginSuccess} />
  }

  const config = pageConfig[activeTab]

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      <div className="ml-64">
        <Header 
          title={config.title} 
          subtitle={config.subtitle} 
          admin={admin}
          onLogout={handleLogout}
          onAdminUpdate={setAdmin}
          onTabChange={setActiveTab}
        />
        <main className="p-6">
          {renderPage()}
        </main>
      </div>
    </div>
  )
}

export default App
