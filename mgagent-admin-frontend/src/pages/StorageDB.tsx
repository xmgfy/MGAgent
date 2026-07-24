import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Database, Table, Play, RefreshCw } from 'lucide-react'
import Button from '../components/Button'
import { storageDbApi } from '../api/client'
import type { StorageDBStats, TableInfo } from '../api/client'

const StorageDB = () => {
  const [stats, setStats] = useState<StorageDBStats>({ database_path: '', tables: [], total_records: {} })
  const [tables, setTables] = useState<TableInfo[]>([])
  const [selectedTable, setSelectedTable] = useState<TableInfo | null>(null)
  const [tableData, setTableData] = useState<{ columns: string[]; data: Record<string, any>[] }>({ columns: [], data: [] })
  const [loading, setLoading] = useState(true)
  const [query, setQuery] = useState('')
  const [queryResult, setQueryResult] = useState<{ columns?: string[]; data?: Record<string, any>[]; message?: string; error?: string } | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [statsData, tablesData] = await Promise.all([
        storageDbApi.getStats(),
        storageDbApi.getTables(),
      ])
      setStats(statsData)
      setTables(tablesData)
    } catch (error) {
      console.error('Failed to load storage DB data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleTableSelect = async (table: TableInfo) => {
    try {
      setSelectedTable(table)
      const data = await storageDbApi.getTableData(table.name, 50, 0)
      setTableData(data)
      setQueryResult(null)
    } catch (error) {
      console.error('Failed to load table data:', error)
    }
  }

  const handleExecuteQuery = async () => {
    if (!query.trim()) return
    try {
      const result = await storageDbApi.executeQuery(query)
      setQueryResult(result)
    } catch (error) {
      console.error('Failed to execute query:', error)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-100 rounded-xl">
            <Database size={20} className="text-purple-500" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-800">存储数据库</h2>
            <p className="text-sm text-gray-500">管理和查询 SQLite 数据库</p>
          </div>
        </div>
        <Button variant="secondary" onClick={loadData}>
          <RefreshCw size={18} />
          刷新
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-xl p-4 shadow-sm border border-gray-100"
        >
          <p className="text-sm text-gray-500 mb-1">数据库路径</p>
          <p className="text-sm text-gray-800 truncate">{stats.database_path}</p>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-xl p-4 shadow-sm border border-gray-100"
        >
          <p className="text-sm text-gray-500 mb-1">表数量</p>
          <p className="text-2xl font-bold text-gray-800">{stats.tables.length}</p>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-xl p-4 shadow-sm border border-gray-100"
        >
          <p className="text-sm text-gray-500 mb-1">总记录数</p>
          <p className="text-2xl font-bold text-gray-800">
            {Object.values(stats.total_records).reduce((a, b) => a + b, 0)}
          </p>
        </motion.div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="p-4 border-b border-gray-100">
            <h3 className="font-medium text-gray-800 flex items-center gap-2">
              <Table size={18} />
              表列表
            </h3>
          </div>
          {loading ? (
            <div className="flex items-center justify-center h-48">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                className="w-8 h-8 border-4 border-primary-200 border-t-primary-500 rounded-full"
              />
            </div>
          ) : (
            <div className="max-h-[400px] overflow-y-auto">
              {tables.map((table) => (
                <motion.button
                  key={table.name}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className={`w-full text-left p-4 border-b border-gray-100 hover:bg-gray-50 transition-colors ${
                    selectedTable?.name === table.name ? 'bg-primary-50' : ''
                  }`}
                  onClick={() => handleTableSelect(table)}
                >
                  <div className="flex items-center justify-between">
                    <span className={`font-medium ${selectedTable?.name === table.name ? 'text-primary-600' : 'text-gray-800'}`}>
                      {table.name}
                    </span>
                    <span className="text-xs text-gray-400">{table.record_count} 条</span>
                  </div>
                  <div className="mt-1">
                    {table.columns.map((col, i) => (
                      <span
                        key={col.name}
                        className={`text-xs px-2 py-0.5 rounded-full ${col.is_pk ? 'bg-primary-100 text-primary-600' : 'bg-gray-100 text-gray-600'}`}
                      >
                        {col.name}: {col.type}{i < table.columns.length - 1 ? ', ' : ''}
                      </span>
                    ))}
                  </div>
                </motion.button>
              ))}
            </div>
          )}
        </div>

        <div className="lg:col-span-2 space-y-6">
          {selectedTable && (
            <>
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="p-4 border-b border-gray-100 flex items-center justify-between">
                  <h3 className="font-medium text-gray-800">
                    表: <span className="text-primary-600">{selectedTable.name}</span>
                  </h3>
                  <span className="text-sm text-gray-500">
                    共 {selectedTable.record_count} 条记录
                  </span>
                </div>
                <div className="overflow-x-auto max-h-[400px] overflow-y-auto">
                  <table>
                    <thead>
                      <tr>
                        {tableData.columns.map((col) => (
                          <th key={col}>{col}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {tableData.data.map((row, index) => (
                        <tr key={index}>
                          {tableData.columns.map((col) => (
                            <td key={col} className="text-sm text-gray-700">
                              {String(row[col])}
                            </td>
                          ))}
                        </tr>
                      ))}
                      {tableData.data.length === 0 && (
                        <tr>
                          <td colSpan={tableData.columns.length} className="text-center text-gray-400 py-8">
                            暂无数据
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}

          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
            <h3 className="font-medium text-gray-800 mb-4 flex items-center gap-2">
              <Play size={18} className="text-green-500" />
              SQL 查询
            </h3>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="输入 SQL 查询语句..."
              className="w-full h-32 p-4 bg-gray-50 border border-gray-200 rounded-xl text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400 resize-none"
            />
            <div className="flex justify-end mt-3">
              <Button onClick={handleExecuteQuery}>
                <Play size={18} />
                执行
              </Button>
            </div>
            
            {queryResult && (
              <div className="mt-4 p-4 rounded-xl" style={{ backgroundColor: queryResult.error ? '#fef2f2' : '#f9fafb' }}>
                {queryResult.error ? (
                  <p className="text-red-600">{queryResult.error}</p>
                ) : queryResult.message ? (
                  <p className="text-green-600">{queryResult.message}</p>
                ) : queryResult.data ? (
                  <div className="overflow-x-auto max-h-[300px] overflow-y-auto">
                    <table>
                      <thead>
                        <tr>
                          {queryResult.columns?.map((col) => (
                            <th key={col}>{col}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {queryResult.data.map((row, index) => (
                          <tr key={index}>
                            {queryResult.columns?.map((col) => (
                              <td key={col} className="text-sm text-gray-700">
                                {String(row[col])}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : null}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default StorageDB