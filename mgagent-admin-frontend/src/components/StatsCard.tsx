import { motion } from 'framer-motion'
import type { LucideIcon } from 'lucide-react'

interface StatsCardProps {
  icon: LucideIcon
  title: string
  value: string | number
  change?: { value: number; isPositive: boolean }
  color: 'blue' | 'green' | 'purple' | 'orange'
}

const colorMap = {
  blue: {
    bg: 'bg-blue-50',
    icon: 'text-blue-500',
    gradient: 'from-blue-500 to-blue-600',
  },
  green: {
    bg: 'bg-green-50',
    icon: 'text-green-500',
    gradient: 'from-green-500 to-green-600',
  },
  purple: {
    bg: 'bg-purple-50',
    icon: 'text-purple-500',
    gradient: 'from-purple-500 to-purple-600',
  },
  orange: {
    bg: 'bg-orange-50',
    icon: 'text-orange-500',
    gradient: 'from-orange-500 to-orange-600',
  },
}

const StatsCard = ({ icon: Icon, title, value, change, color }: StatsCardProps) => {
  const colors = colorMap[color]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow"
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-500 mb-1">{title}</p>
          <p className="text-3xl font-bold text-gray-800">{value}</p>
          {change && (
            <p className={`text-sm mt-2 ${change.isPositive ? 'text-green-500' : 'text-red-500'}`}>
              {change.isPositive ? '+' : ''}{change.value}% 较上次
            </p>
          )}
        </div>
        <div className={`w-12 h-12 rounded-xl ${colors.bg} flex items-center justify-center`}>
          <Icon size={24} className={colors.icon} />
        </div>
      </div>
    </motion.div>
  )
}

export default StatsCard