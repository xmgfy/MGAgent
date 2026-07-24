import { motion } from 'framer-motion'
import { 
  LayoutDashboard, 
  Database, 
  FileText, 
  Box, 
  Cpu, 
  Settings,
  Server,
  ChevronRight,
  Users
} from 'lucide-react'

interface SidebarProps {
  activeTab: string
  onTabChange: (tab: string) => void
}

const menuItems = [
  { id: 'dashboard', label: '概览', icon: LayoutDashboard },
  { id: 'knowledge-base', label: '知识库管理', icon: FileText },
  { id: 'vector-db', label: '向量数据库', icon: Box },
  { id: 'storage-db', label: '存储数据库', icon: Database },
  { id: 'model', label: '模型管理', icon: Cpu },
  { id: 'users', label: '用户管理', icon: Users },
  { id: 'system', label: '监控管理', icon: Server },
]

const Sidebar = ({ activeTab, onTabChange }: SidebarProps) => {
  return (
    <div className="w-64 bg-white border-r border-gray-100 flex flex-col h-screen fixed left-0 top-0">
      <div className="p-6 border-b border-gray-100">
        <h1 className="text-xl font-bold bg-gradient-to-r from-primary-600 to-accent-600 bg-clip-text text-transparent">
          MGAgent
        </h1>
        <p className="text-sm text-gray-500 mt-1">管理控制台</p>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {menuItems.map((item) => {
          const Icon = item.icon
          const isActive = activeTab === item.id
          
          return (
            <motion.button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                isActive
                  ? 'bg-primary-50 text-primary-600 font-medium'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              }`}
              whileHover={{ x: 4 }}
              whileTap={{ scale: 0.98 }}
            >
              <Icon size={20} />
              <span className="flex-1 text-left">{item.label}</span>
              {isActive && <ChevronRight size={16} />}
            </motion.button>
          )
        })}
      </nav>

      <div className="p-4 border-t border-gray-100">
        <button 
          onClick={() => onTabChange('system')}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-all"
        >
          <Settings size={20} />
          <span>系统设置</span>
        </button>
      </div>
    </div>
  )
}

export default Sidebar