import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Bell, Search, User, LogOut, Settings, ChevronDown, X, AlertTriangle, UserCircle, Shield, Mail, Calendar, Check } from 'lucide-react'
import type { Admin } from '../../api/client'
import { notificationApi, authApi } from '../../api/client'
import type { Notification } from '../../api/client'

interface HeaderProps {
  title: string
  subtitle?: string
  admin?: Admin | null
  onLogout?: () => void
  onAdminUpdate?: (updatedAdmin: Admin) => void
  onTabChange?: (tab: string) => void
}

const Header = ({ title, subtitle, admin, onLogout, onAdminUpdate, onTabChange }: HeaderProps) => {
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [showNotifications, setShowNotifications] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [showSearch, setShowSearch] = useState(false)
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [showProfile, setShowProfile] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [showNotificationDetail, setShowNotificationDetail] = useState(false)
  const [selectedNotification, setSelectedNotification] = useState<Notification | null>(null)
  const [email, setEmail] = useState(admin?.email || '')
  const [oldPassword, setOldPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [saveSuccess, setSaveSuccess] = useState(false)

  useEffect(() => {
    loadNotifications()
  }, [])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement
      if (!target.closest('.search-dropdown') && !target.closest('.notification-dropdown') && !target.closest('.user-menu')) {
        setShowSearch(false)
        setShowNotifications(false)
        setShowUserMenu(false)
      }
    }
    
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const loadNotifications = async () => {
    try {
      const [notifs, count] = await Promise.all([
        notificationApi.getNotifications(),
        notificationApi.getUnreadCount()
      ])
      setNotifications(notifs)
      setUnreadCount(count.count)
    } catch (error) {
      console.error('Failed to load notifications:', error)
    }
  }

  const handleMarkAsRead = async (notificationId: string) => {
    try {
      await notificationApi.markAsRead(notificationId)
      setNotifications(notifications.map(n => n.id === notificationId ? { ...n, is_read: true } : n))
      setUnreadCount(unreadCount - 1)
    } catch (error) {
      console.error('Failed to mark notification as read:', error)
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    
    const query = searchQuery.trim()
    
    if (query.includes('用户') || query.includes('审批')) {
      onTabChange?.('users')
    } else if (query.includes('文档') || query.includes('知识')) {
      onTabChange?.('knowledge-base')
    } else if (query.includes('向量')) {
      onTabChange?.('vector-db')
    } else if (query.includes('模型')) {
      onTabChange?.('model')
    } else if (query.includes('监控') || query.includes('系统')) {
      onTabChange?.('system')
    } else if (query.includes('存储') || query.includes('数据库')) {
      onTabChange?.('storage-db')
    } else {
      onTabChange?.('dashboard')
    }
    
    setShowSearch(false)
    setSearchQuery('')
  }

  const handleSaveSettings = async () => {
    try {
      if (email !== admin?.email) {
        const updatedAdmin = await authApi.updateProfile({ email })
        onAdminUpdate?.(updatedAdmin)
      }
      if (newPassword) {
        await authApi.updatePassword({ old_password: oldPassword, new_password: newPassword })
        setOldPassword('')
        setNewPassword('')
      }
      setSaveSuccess(true)
      setTimeout(() => {
        setSaveSuccess(false)
        setShowSettings(false)
      }, 2000)
    } catch (error: any) {
      alert(error.response?.data?.detail || '保存失败')
    }
  }

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'error': return <AlertTriangle size={16} />
      case 'warning': return <AlertTriangle size={16} />
      default: return <Mail size={16} />
    }
  }

  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'error': return 'bg-red-100 text-red-500'
      case 'warning': return 'bg-yellow-100 text-yellow-500'
      default: return 'bg-blue-100 text-blue-500'
    }
  }

  return (
    <header className="bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between">
      <div>
        <h1 className="text-xl font-semibold text-gray-800">{title}</h1>
        {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
      </div>
      
      <div className="flex items-center gap-4">
        <div className="relative search-dropdown">
          <motion.button
            className="p-2 rounded-xl text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setShowSearch(!showSearch)}
          >
            <Search size={20} />
          </motion.button>
          <AnimatePresence>
            {showSearch && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: -10 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: -10 }}
                className="absolute right-0 top-full mt-2 w-80 bg-white rounded-xl shadow-lg border border-gray-100 p-2 z-50"
              >
                <div className="flex items-center gap-2">
                  <Search size={18} className="text-gray-400" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                    placeholder="搜索文档、用户、会话..."
                    className="flex-1 px-2 py-2 text-sm bg-gray-50 rounded-lg border-none outline-none focus:bg-white focus:ring-2 focus:ring-primary-200"
                    autoFocus
                  />
                  <motion.button
                    onClick={() => {
                      setShowSearch(false)
                      setSearchQuery('')
                    }}
                    className="p-1 rounded-lg hover:bg-gray-100 text-gray-400"
                    whileHover={{ scale: 1.1 }}
                  >
                    <X size={16} />
                  </motion.button>
                </div>
                <div className="mt-2 pt-2 border-t border-gray-100">
                  <p className="text-xs text-gray-400 px-2 mb-1">快捷搜索</p>
                  <div className="flex flex-wrap gap-1 px-2">
                    {['知识库文档', '用户列表', '会话记录', '系统日志'].map((item) => (
                      <button
                        key={item}
                        onClick={() => {
                          setSearchQuery(item)
                          handleSearch()
                        }}
                        className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded-lg hover:bg-primary-100 hover:text-primary-600 transition-colors"
                      >
                        {item}
                      </button>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
        
        <div className="relative notification-dropdown">
          <motion.button
            className="p-2 rounded-xl text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors relative"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => {
              setShowNotifications(!showNotifications)
              loadNotifications()
            }}
          >
            <Bell size={20} />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
            )}
          </motion.button>
          <AnimatePresence>
            {showNotifications && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: -10 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: -10 }}
                className="absolute right-0 top-full mt-2 w-96 bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden z-50"
              >
                <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
                  <h3 className="font-semibold text-gray-800">系统通知</h3>
                  <span className="text-xs text-gray-400">{notifications.length} 条</span>
                </div>
                <div className="max-h-80 overflow-y-auto">
                  {notifications.length > 0 ? (
                    notifications.map((notification) => (
                      <motion.div
                        key={notification.id}
                        className="px-4 py-3 hover:bg-gray-50 border-b border-gray-50 last:border-none cursor-pointer"
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        onClick={() => {
                          handleMarkAsRead(notification.id)
                          setSelectedNotification(notification)
                          setShowNotificationDetail(true)
                          setShowNotifications(false)
                        }}
                      >
                        <div className="flex items-start gap-3">
                          <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${getNotificationColor(notification.type)}`}>
                            {getNotificationIcon(notification.type)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between">
                              <h4 className={`text-sm font-medium ${notification.is_read ? 'text-gray-500' : 'text-gray-800'}`}>
                                {notification.title}
                              </h4>
                              <span className="text-xs text-gray-400">{new Date(notification.created_at).toLocaleString()}</span>
                            </div>
                            <p className="text-xs text-gray-500 mt-1 line-clamp-2">{notification.message}</p>
                          </div>
                        </div>
                      </motion.div>
                    ))
                  ) : (
                    <div className="px-4 py-8 text-center">
                      <Bell size={32} className="text-gray-300 mx-auto mb-2" />
                      <p className="text-sm text-gray-400">暂无通知</p>
                    </div>
                  )}
                </div>
                <div className="px-4 py-3 bg-gray-50">
                  <button 
                    onClick={() => {
                      setShowNotifications(false)
                      window.location.href = '/system'
                    }}
                    className="w-full text-sm text-primary-600 hover:text-primary-700 font-medium"
                  >
                    查看全部通知
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
        
        <div className="relative pl-4 border-l border-gray-200 user-menu">
          <motion.button
            className="flex items-center gap-3 p-1 rounded-xl hover:bg-gray-100 transition-colors"
            whileHover={{ scale: 1.02 }}
            onClick={() => setShowUserMenu(!showUserMenu)}
          >
            <div className="w-8 h-8 bg-gradient-to-br from-primary-100 to-accent-100 rounded-full flex items-center justify-center">
              <User size={16} className="text-primary-600" />
            </div>
            <div className="text-left">
              <p className="text-sm font-medium text-gray-800">{admin?.username || '管理员'}</p>
              <p className="text-xs text-gray-500">{admin?.role === 'platform_admin' ? '平台管理员' : '租户管理员'}</p>
            </div>
            <ChevronDown size={16} className="text-gray-400" />
          </motion.button>
          
          <AnimatePresence>
            {showUserMenu && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: -10 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: -10 }}
                className="absolute right-0 top-full mt-2 w-56 bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden z-50"
              >
                <div className="px-4 py-3 border-b border-gray-100 bg-gray-50">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-primary-100 to-accent-100 rounded-full flex items-center justify-center">
                      <User size={20} className="text-primary-600" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-gray-800">{admin?.username || '管理员'}</p>
                      <p className="text-xs text-gray-500">{admin?.email || ''}</p>
                    </div>
                  </div>
                </div>
                <div className="py-1">
                  <button
                    onClick={() => {
                      setShowUserMenu(false)
                      setShowProfile(true)
                    }}
                    className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-3"
                  >
                    <UserCircle size={16} className="text-gray-400" />
                    个人资料
                  </button>
                  <button
                    onClick={() => {
                      setShowUserMenu(false)
                      setShowSettings(true)
                    }}
                    className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-3"
                  >
                    <Settings size={16} className="text-gray-400" />
                    账户设置
                  </button>
                </div>
                <div className="border-t border-gray-100 py-1">
                  <button
                    onClick={() => {
                      onLogout?.()
                      setShowUserMenu(false)
                    }}
                    className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-3"
                  >
                    <LogOut size={16} />
                    退出登录
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      <AnimatePresence>
        {showProfile && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => setShowProfile(false)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="bg-white rounded-2xl p-6 w-full max-w-md mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-800">个人资料</h3>
                <button onClick={() => setShowProfile(false)} className="text-gray-400 hover:text-gray-600">
                  <X size={20} />
                </button>
              </div>
              <div className="flex flex-col items-center mb-6">
                <div className="w-20 h-20 bg-gradient-to-br from-primary-100 to-accent-100 rounded-full flex items-center justify-center mb-3">
                  <User size={32} className="text-primary-600" />
                </div>
                <h4 className="text-xl font-semibold text-gray-800">{admin?.username}</h4>
                <p className="text-sm text-gray-500">{admin?.email}</p>
              </div>
              <div className="space-y-4">
                <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                  <Shield size={18} className="text-gray-400" />
                  <div>
                    <p className="text-xs text-gray-500">角色</p>
                    <p className="text-sm font-medium text-gray-800">{admin?.role === 'platform_admin' ? '平台管理员' : '租户管理员'}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                  <Calendar size={18} className="text-gray-400" />
                  <div>
                    <p className="text-xs text-gray-500">创建时间</p>
                    <p className="text-sm font-medium text-gray-800">{admin?.created_at ? new Date(admin.created_at).toLocaleString() : '-'}</p>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showSettings && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => setShowSettings(false)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="bg-white rounded-2xl p-6 w-full max-w-md mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-800">账户设置</h3>
                <button onClick={() => setShowSettings(false)} className="text-gray-400 hover:text-gray-600">
                  <X size={20} />
                </button>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">用户名</label>
                  <input
                    type="text"
                    value={admin?.username || ''}
                    disabled
                    className="w-full px-4 py-2.5 bg-gray-100 border border-gray-200 rounded-xl text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">旧密码</label>
                  <input
                    type="password"
                    value={oldPassword}
                    onChange={(e) => setOldPassword(e.target.value)}
                    placeholder="输入旧密码"
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">新密码</label>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="输入新密码（至少6位）"
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                  />
                </div>
              </div>
              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setShowSettings(false)}
                  className="flex-1 px-4 py-2.5 border border-gray-200 rounded-xl text-sm text-gray-700 hover:bg-gray-50"
                >
                  取消
                </button>
                <button 
                  onClick={handleSaveSettings}
                  className={`flex-1 px-4 py-2.5 rounded-xl text-sm flex items-center justify-center gap-2 ${saveSuccess ? 'bg-green-500 text-white' : 'bg-primary-500 text-white hover:bg-primary-600'}`}
                >
                  {saveSuccess ? (
                    <>
                      <Check size={16} />
                      保存成功
                    </>
                  ) : (
                    '保存设置'
                  )}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showNotificationDetail && selectedNotification && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => setShowNotificationDetail(false)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="bg-white rounded-2xl p-6 w-full max-w-md mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-800">通知详情</h3>
                <button onClick={() => setShowNotificationDetail(false)} className="text-gray-400 hover:text-gray-600">
                  <X size={20} />
                </button>
              </div>
              <div className="flex items-center gap-3 mb-4">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${getNotificationColor(selectedNotification.type)}`}>
                  {getNotificationIcon(selectedNotification.type)}
                </div>
                <div>
                  <h4 className="text-base font-semibold text-gray-800">{selectedNotification.title}</h4>
                  <span className="text-xs text-gray-400">{new Date(selectedNotification.created_at).toLocaleString()}</span>
                </div>
              </div>
              <div className="p-4 bg-gray-50 rounded-xl">
                <p className="text-sm text-gray-600 leading-relaxed">{selectedNotification.message}</p>
              </div>
              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setShowNotificationDetail(false)}
                  className="flex-1 px-4 py-2.5 border border-gray-200 rounded-xl text-sm text-gray-700 hover:bg-gray-50"
                >
                  关闭
                </button>
                {selectedNotification.type === 'user_registration' && (
                  <button
                    onClick={() => {
                      setShowNotificationDetail(false)
                      setShowNotifications(false)
                      if (onTabChange) {
                        onTabChange('users')
                      }
                    }}
                    className="flex-1 px-4 py-2.5 bg-primary-500 text-white rounded-xl text-sm hover:bg-primary-600"
                  >
                    去审批
                  </button>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  )
}

export default Header
