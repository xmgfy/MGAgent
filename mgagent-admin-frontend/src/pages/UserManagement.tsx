import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Users, CheckCircle, XCircle, Trash2, RefreshCw, Filter, Lock, Unlock, Ban, Plus, UserPlus, Building2, Shield, Crown, User as UserIcon } from 'lucide-react'
import Button from '../components/Button'
import { userApi, tenantApi, adminApi } from '../api/client'
import type { User, Tenant, Admin } from '../api/client'

type TabType = 'users' | 'admins'

const UserManagement = () => {
  const [activeTab, setActiveTab] = useState<TabType>('users')
  const [users, setUsers] = useState<User[]>([])
  const [admins, setAdmins] = useState<Admin[]>([])
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [selectedTenant, setSelectedTenant] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [showTenantModal, setShowTenantModal] = useState(false)
  const [showUserModal, setShowUserModal] = useState(false)
  const [showAdminModal, setShowAdminModal] = useState(false)
  const [newTenant, setNewTenant] = useState({ name: '', description: '', max_users: 100 })
  const [newUser, setNewUser] = useState({ username: '', email: '', password: '', tenant_id: '' })
  const [newAdmin, setNewAdmin] = useState({ username: '', email: '', password: '', role: 'tenant_admin', tenant_id: '' })
  const [currentAdmin, setCurrentAdmin] = useState<Admin | null>(null)

  useEffect(() => {
    loadData()
    loadAdminInfo()
  }, [activeTab])

  const loadAdminInfo = async () => {
    try {
      const adminInfo = localStorage.getItem('admin_info')
      if (adminInfo) {
        setCurrentAdmin(JSON.parse(adminInfo))
      }
    } catch (error) {
      console.error('Failed to load admin info:', error)
    }
  }

  const loadData = async () => {
    try {
      setLoading(true)
      if (activeTab === 'users') {
        const [usersData, tenantsData] = await Promise.all([
          userApi.getUsers(),
          tenantApi.getTenants()
        ])
        setUsers(usersData)
        setTenants(tenantsData)
      } else {
        const [adminsData, tenantsData] = await Promise.all([
          adminApi.getAdmins(),
          tenantApi.getTenants()
        ])
        setAdmins(adminsData)
        setTenants(tenantsData)
      }
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredItems = activeTab === 'users' 
    ? users.filter(user => {
        const tenantMatch = !selectedTenant || user.tenant_id === selectedTenant
        const statusMatch = statusFilter === 'all' || user.status === statusFilter
        return tenantMatch && statusMatch
      })
    : admins.filter(admin => {
        const tenantMatch = !selectedTenant || admin.tenant_id === selectedTenant
        const statusMatch = statusFilter === 'all' || admin.status === statusFilter
        return tenantMatch && statusMatch
      })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
      case 'active': return 'bg-green-100 text-green-600'
      case 'pending': return 'bg-yellow-100 text-yellow-600'
      case 'frozen': return 'bg-blue-100 text-blue-600'
      case 'disabled': return 'bg-red-100 text-red-600'
      default: return 'bg-gray-100 text-gray-600'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'approved': return '已通过'
      case 'active': return '活跃'
      case 'pending': return '待审核'
      case 'frozen': return '已冻结'
      case 'disabled': return '已禁用'
      default: return status
    }
  }

  const getRoleText = (role: string) => {
    switch (role) {
      case 'platform_admin': return '平台管理员'
      case 'tenant_admin': return '租户管理员'
      case 'user': return '普通用户'
      default: return role
    }
  }

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'platform_admin': return 'bg-purple-100 text-purple-600'
      case 'tenant_admin': return 'bg-blue-100 text-blue-600'
      case 'user': return 'bg-gray-100 text-gray-600'
      default: return 'bg-gray-100 text-gray-600'
    }
  }

  const handleUserStatusChange = async (userId: string, status: string) => {
    try {
      const updatedUser = await userApi.updateUserStatus(userId, status)
      setUsers(users.map(u => u.id === userId ? updatedUser : u))
    } catch (error) {
      console.error('Failed to update user status:', error)
    }
  }

  const handleAdminStatusChange = async (adminId: string, status: string) => {
    try {
      const updatedAdmin = await adminApi.updateAdmin(adminId, { status })
      setAdmins(admins.map(a => a.id === adminId ? updatedAdmin : a))
    } catch (error) {
      console.error('Failed to update admin status:', error)
    }
  }

  const handleUserDelete = async (userId: string) => {
    try {
      await userApi.deleteUser(userId)
      setUsers(users.filter(u => u.id !== userId))
      setConfirmDelete(null)
    } catch (error) {
      console.error('Failed to delete user:', error)
    }
  }

  const handleAdminDelete = async (adminId: string) => {
    try {
      await adminApi.deleteAdmin(adminId)
      setAdmins(admins.filter(a => a.id !== adminId))
      setConfirmDelete(null)
    } catch (error) {
      console.error('Failed to delete admin:', error)
    }
  }

  const handleCreateTenant = async () => {
    if (!newTenant.name) {
      alert('请输入租户名称')
      return
    }
    try {
      await tenantApi.createTenant(newTenant)
      setShowTenantModal(false)
      setNewTenant({ name: '', description: '', max_users: 100 })
      loadData()
    } catch (error) {
      console.error('Failed to create tenant:', error)
    }
  }

  const handleCreateUser = async () => {
    if (!newUser.username || !newUser.email || !newUser.password) {
      alert('请填写所有必填字段')
      return
    }
    try {
      await userApi.updateUserStatus('dummy', 'pending')
      setShowUserModal(false)
      setNewUser({ username: '', email: '', password: '', tenant_id: '' })
      loadData()
    } catch (error) {
      console.error('Failed to create user:', error)
    }
  }

  const handleCreateAdmin = async () => {
    if (!newAdmin.username || !newAdmin.email || !newAdmin.password) {
      alert('请填写所有必填字段')
      return
    }
    if (newAdmin.role === 'tenant_admin' && !newAdmin.tenant_id) {
      alert('租户管理员必须分配租户')
      return
    }
    try {
      await adminApi.createAdmin(newAdmin)
      setShowAdminModal(false)
      setNewAdmin({ username: '', email: '', password: '', role: 'tenant_admin', tenant_id: '' })
      loadData()
    } catch (error) {
      console.error('Failed to create admin:', error)
    }
  }

  const getTenantName = (tenantId: string) => {
    const tenant = tenants.find(t => t.id === tenantId)
    return tenant?.name || '-'
  }

  const isPlatformAdmin = currentAdmin?.role === 'platform_admin'

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 rounded-xl">
            <Users size={20} className="text-blue-500" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-800">用户管理</h2>
            <p className="text-sm text-gray-500">管理系统用户和租户权限</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="secondary" onClick={loadData}>
            <RefreshCw size={18} />
            刷新
          </Button>
          {isPlatformAdmin && (
            <>
              <Button variant="secondary" onClick={() => setShowTenantModal(true)}>
                <Building2 size={18} />
                添加租户
              </Button>
            </>
          )}
          {activeTab === 'users' ? (
            <Button onClick={() => setShowUserModal(true)}>
              <UserPlus size={18} />
              添加用户
            </Button>
          ) : (
            <Button onClick={() => setShowAdminModal(true)}>
              <Shield size={18} />
              添加管理员
            </Button>
          )}
        </div>
      </div>

      <div className="flex gap-2 bg-gray-100 p-1 rounded-xl w-fit">
        <button
          onClick={() => setActiveTab('users')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            activeTab === 'users' ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          <span className="flex items-center gap-2">
              <UserIcon size={16} />
              用户管理
            </span>
        </button>
        {isPlatformAdmin && (
          <button
            onClick={() => setActiveTab('admins')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'admins' ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <span className="flex items-center gap-2">
              <Crown size={16} />
              管理员管理
            </span>
          </button>
        )}
      </div>

      {isPlatformAdmin && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {tenants.map((tenant) => (
            <motion.div
              key={tenant.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${
                selectedTenant === tenant.id
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-100 hover:border-gray-200 hover:bg-gray-50'
              }`}
              onClick={() => setSelectedTenant(selectedTenant === tenant.id ? null : tenant.id)}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-800">{tenant.name}</p>
                  <p className="text-sm text-gray-500">
                    {activeTab === 'users' ? tenant.user_count : tenant.admin_count} 个{activeTab === 'users' ? '用户' : '管理员'}
                  </p>
                </div>
                <div className={`w-2 h-2 rounded-full ${tenant.status === 'active' ? 'bg-green-500' : 'bg-gray-400'}`} />
              </div>
            </motion.div>
          ))}
        </div>
      )}

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Filter size={18} className="text-gray-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
          >
            <option value="all">全部状态</option>
            <option value="pending">待审核</option>
            <option value="approved">已通过</option>
            <option value="active">活跃</option>
            <option value="frozen">已冻结</option>
            <option value="disabled">已禁用</option>
          </select>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span className="text-gray-500">共 {filteredItems.length} 个{activeTab === 'users' ? '用户' : '管理员'}</span>
          {activeTab === 'users' && (
            <>
              <span className="text-gray-400">|</span>
              <span className="text-gray-500">待审核: <span className="text-yellow-600">{users.filter(u => u.status === 'pending').length}</span></span>
              <span className="text-gray-500">已通过: <span className="text-green-600">{users.filter(u => u.status === 'approved').length}</span></span>
            </>
          )}
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden"
      >
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr>
                <th className="text-left px-6 py-4 text-sm font-semibold text-gray-500">用户名</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-gray-500">邮箱</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-gray-500">角色</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-gray-500">租户</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-gray-500">状态</th>
                {activeTab === 'users' && <th className="text-left px-6 py-4 text-sm font-semibold text-gray-500">对话数</th>}
                <th className="text-left px-6 py-4 text-sm font-semibold text-gray-500">操作</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={activeTab === 'users' ? 7 : 6} className="text-center py-12">
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                      className="w-8 h-8 border-4 border-primary-200 border-t-primary-500 rounded-full mx-auto"
                    />
                  </td>
                </tr>
              ) : filteredItems.length === 0 ? (
                <tr>
                  <td colSpan={activeTab === 'users' ? 7 : 6} className="text-center py-12">
                    <Users size={40} className="text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-400">暂无{activeTab === 'users' ? '用户' : '管理员'}</p>
                  </td>
                </tr>
              ) : (
                filteredItems.map((item) => (
                  <motion.tr
                    key={item.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="border-t border-gray-100 hover:bg-gray-50"
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-gradient-to-br from-primary-100 to-accent-100 rounded-full flex items-center justify-center">
                          {activeTab === 'users' ? <Users size={14} className="text-primary-600" /> : <Shield size={14} className="text-primary-600" />}
                        </div>
                        <span className="font-medium text-gray-800">{item.username}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">{item.email}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 text-xs rounded-full ${getRoleColor(item.role)}`}>
                        {getRoleText(item.role)}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded-full">
                        {getTenantName(item.tenant_id)}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(item.status)}`}>
                        {getStatusText(item.status)}
                      </span>
                    </td>
                    {activeTab === 'users' && (
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {(item as User).chat_count}/{(item as User).max_chats}
                      </td>
                    )}
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        {['pending', 'approved', 'active'].includes(item.status as string) && (
                          <>
                            {item.status === 'pending' && (
                              <>
                                <motion.button
                                  className="p-2 text-green-500 hover:bg-green-50 rounded-lg transition-colors"
                                  whileHover={{ scale: 1.1 }}
                                  whileTap={{ scale: 0.9 }}
                                  onClick={() => activeTab === 'users' 
                                    ? handleUserStatusChange(item.id, 'approved') 
                                    : handleAdminStatusChange(item.id, 'active')
                                  }
                                  title="通过审核"
                                >
                                  <CheckCircle size={16} />
                                </motion.button>
                                <motion.button
                                  className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                                  whileHover={{ scale: 1.1 }}
                                  whileTap={{ scale: 0.9 }}
                                  onClick={() => activeTab === 'users' 
                                    ? handleUserStatusChange(item.id, 'disabled') 
                                    : handleAdminStatusChange(item.id, 'disabled')
                                  }
                                  title="拒绝"
                                >
                                  <XCircle size={16} />
                                </motion.button>
                              </>
                            )}
                            {['approved', 'active'].includes(item.status as string) && (
                              <>
                                {activeTab !== 'admins' || item.id !== currentAdmin?.id ? (
                                  <motion.button
                                    className="p-2 text-blue-500 hover:bg-blue-50 rounded-lg transition-colors"
                                    whileHover={{ scale: 1.1 }}
                                    whileTap={{ scale: 0.9 }}
                                    onClick={() => activeTab === 'users' 
                                      ? handleUserStatusChange(item.id, 'frozen') 
                                      : handleAdminStatusChange(item.id, 'frozen')
                                    }
                                    title="冻结"
                                  >
                                    <Lock size={16} />
                                  </motion.button>
                                ) : null}
                                {isPlatformAdmin && (activeTab !== 'admins' || item.role !== 'platform_admin') && (activeTab !== 'admins' || item.id !== currentAdmin?.id) && (
                                  <motion.button
                                    className="p-2 text-gray-500 hover:bg-gray-50 rounded-lg transition-colors"
                                    whileHover={{ scale: 1.1 }}
                                    whileTap={{ scale: 0.9 }}
                                    onClick={() => activeTab === 'users' 
                                      ? handleUserStatusChange(item.id, 'disabled') 
                                      : handleAdminStatusChange(item.id, 'disabled')
                                    }
                                    title="禁用"
                                  >
                                    <Ban size={16} />
                                  </motion.button>
                                )}
                              </>
                            )}
                          </>
                        )}
                        {(item.status === 'frozen' || item.status === 'disabled') && (
                          <motion.button
                            className="p-2 text-green-500 hover:bg-green-50 rounded-lg transition-colors"
                            whileHover={{ scale: 1.1 }}
                            whileTap={{ scale: 0.9 }}
                            onClick={() => activeTab === 'users' 
                              ? handleUserStatusChange(item.id, 'approved') 
                              : handleAdminStatusChange(item.id, 'active')
                            }
                            title="解除限制"
                          >
                            <Unlock size={16} />
                          </motion.button>
                        )}
                        <AnimatePresence>
                          {confirmDelete === item.id ? (
                            <motion.div
                              initial={{ opacity: 0, scale: 0.8 }}
                              animate={{ opacity: 1, scale: 1 }}
                              className="flex gap-1"
                            >
                              <Button
                                size="sm"
                                onClick={() => activeTab === 'users' ? handleUserDelete(item.id) : handleAdminDelete(item.id)}
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
                              onClick={() => setConfirmDelete(item.id)}
                              title="删除"
                            >
                              <Trash2 size={16} />
                            </motion.button>
                          )}
                        </AnimatePresence>
                      </div>
                    </td>
                  </motion.tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </motion.div>

      <AnimatePresence>
        {showTenantModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => setShowTenantModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="bg-white rounded-2xl p-6 w-full max-w-md mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold text-gray-800 mb-6">添加租户</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">租户名称</label>
                  <input
                    type="text"
                    value={newTenant.name}
                    onChange={(e) => setNewTenant({ ...newTenant, name: e.target.value })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                    placeholder="输入租户名称"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">描述</label>
                  <textarea
                    value={newTenant.description}
                    onChange={(e) => setNewTenant({ ...newTenant, description: e.target.value })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                    placeholder="输入租户描述"
                    rows={3}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">最大用户数</label>
                  <input
                    type="number"
                    value={newTenant.max_users}
                    onChange={(e) => setNewTenant({ ...newTenant, max_users: parseInt(e.target.value) || 100 })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                  />
                </div>
              </div>
              <div className="flex gap-3 mt-6">
                <Button variant="secondary" onClick={() => setShowTenantModal(false)}>
                  取消
                </Button>
                <Button onClick={handleCreateTenant}>
                  <Plus size={18} />
                  创建租户
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showUserModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => setShowUserModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="bg-white rounded-2xl p-6 w-full max-w-md mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold text-gray-800 mb-6">添加用户</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">用户名</label>
                  <input
                    type="text"
                    value={newUser.username}
                    onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                    placeholder="输入用户名"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
                  <input
                    type="email"
                    value={newUser.email}
                    onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                    placeholder="输入邮箱"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">密码</label>
                  <input
                    type="password"
                    value={newUser.password}
                    onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                    placeholder="输入密码"
                  />
                </div>
                {isPlatformAdmin && tenants.length > 0 && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">所属租户</label>
                    <select
                      value={newUser.tenant_id}
                      onChange={(e) => setNewUser({ ...newUser, tenant_id: e.target.value })}
                      className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                    >
                      <option value="">选择租户</option>
                      {tenants.map((tenant) => (
                        <option key={tenant.id} value={tenant.id}>{tenant.name}</option>
                      ))}
                    </select>
                  </div>
                )}
              </div>
              <div className="flex gap-3 mt-6">
                <Button variant="secondary" onClick={() => setShowUserModal(false)}>
                  取消
                </Button>
                <Button onClick={handleCreateUser}>
                  <UserPlus size={18} />
                  创建用户
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showAdminModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => setShowAdminModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="bg-white rounded-2xl p-6 w-full max-w-md mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold text-gray-800 mb-6">添加管理员</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">用户名</label>
                  <input
                    type="text"
                    value={newAdmin.username}
                    onChange={(e) => setNewAdmin({ ...newAdmin, username: e.target.value })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                    placeholder="输入用户名"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
                  <input
                    type="email"
                    value={newAdmin.email}
                    onChange={(e) => setNewAdmin({ ...newAdmin, email: e.target.value })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                    placeholder="输入邮箱"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">密码</label>
                  <input
                    type="password"
                    value={newAdmin.password}
                    onChange={(e) => setNewAdmin({ ...newAdmin, password: e.target.value })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                    placeholder="输入密码"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">角色</label>
                  <select
                    value={newAdmin.role}
                    onChange={(e) => setNewAdmin({ ...newAdmin, role: e.target.value })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                  >
                    <option value="tenant_admin">租户管理员</option>
                  </select>
                </div>
                {newAdmin.role === 'tenant_admin' && tenants.length > 0 && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">所属租户</label>
                    <select
                      value={newAdmin.tenant_id}
                      onChange={(e) => setNewAdmin({ ...newAdmin, tenant_id: e.target.value })}
                      className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                    >
                      <option value="">选择租户</option>
                      {tenants.map((tenant) => (
                        <option key={tenant.id} value={tenant.id}>{tenant.name}</option>
                      ))}
                    </select>
                  </div>
                )}
              </div>
              <div className="flex gap-3 mt-6">
                <Button variant="secondary" onClick={() => setShowAdminModal(false)}>
                  取消
                </Button>
                <Button onClick={handleCreateAdmin}>
                  <Shield size={18} />
                  创建管理员
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default UserManagement