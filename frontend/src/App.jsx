import { useState, useEffect } from 'react'
import { api } from './services/api'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [stats, setStats] = useState(null)
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboard()
  }, [activeTab])

  const loadDashboard = async () => {
    try {
      const [statsData, healthData] = await Promise.all([
        api.getDashboard(),
        api.getHealth(),
      ])
      setStats(statsData)
      setHealth(healthData)
      setLoading(false)
    } catch (error) {
      console.error('Failed to load dashboard:', error)
      setLoading(false)
    }
  }

  const tabs = [
    { id: 'dashboard', label: '📊 Dashboard' },
    { id: 'tools', label: '🔧 Інструменти' },
    { id: 'search', label: '🔍 Пошук' },
    { id: 'graph', label: '🌐 Граф' },
    { id: 'settings', label: '⚙️ Налаштування' },
  ]

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold">LLM Wiki App</h1>
          <p className="text-gray-400 text-sm">Knowledge Base Management System</p>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-gray-800 border-b border-gray-700">
        <div className="container mx-auto px-4">
          <div className="flex space-x-1 overflow-x-auto">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-3 font-medium transition-colors whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'bg-gray-700 text-white border-b-2 border-blue-500'
                    : 'text-gray-400 hover:text-white hover:bg-gray-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="text-xl text-gray-400">Завантаження...</div>
          </div>
        ) : (
          <>
            {activeTab === 'dashboard' && (
              <Dashboard stats={stats} health={health} />
            )}
            {activeTab === 'tools' && <Tools />}
            {activeTab === 'search' && <Search />}
            {activeTab === 'graph' && <Graph />}
            {activeTab === 'settings' && <Settings />}
          </>
        )}
      </main>
    </div>
  )
}

// Dashboard Component
function Dashboard({ stats, health }) {
  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Всього сторінок"
          value={stats?.total_pages || 0}
          icon="📄"
          color="blue"
        />
        <StatCard
          title="Тегів"
          value={stats?.total_tags || 0}
          icon="🏷️"
          color="green"
        />
        <StatCard
          title="Raw джерел"
          value={stats?.total_raw || 0}
          icon="📥"
          color="purple"
        />
        <StatCard
          title="Node у графі"
          value={stats?.graph_nodes || 0}
          icon="🔗"
          color="orange"
        />
      </div>

      {/* Health Check */}
      {health && (
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold mb-4">🏥 Health Check</h2>
          <div className="space-y-2">
            <HealthItem status={health.wiki_ok} label="Wiki OKF Compliant" />
            <HealthItem status={health.schema_ok} label="SCHEMA.md Valid" />
            <HealthItem status={health.index_ok} label="Index.md Valid" />
            <HealthItem status={health.hash_ok} label="SHA256 Hashes Valid" />
          </div>
        </div>
      )}

      {/* Recent Changes */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-xl font-semibold mb-4">📝 Останні зміни</h2>
        <div className="text-gray-400">Завантаження...</div>
      </div>

      {/* Quick Actions */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-xl font-semibold mb-4">⚡ Швидкі дії</h2>
        <div className="flex flex-wrap gap-3">
          <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg">
            Запустити Wiki Doctor
          </button>
          <button className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg">
            Запустити Integrator
          </button>
          <button className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg">
            Оновити граф
          </button>
          <button className="px-4 py-2 bg-orange-600 hover:bg-orange-700 rounded-lg">
            Git Sync
          </button>
        </div>
      </div>
    </div>
  )
}

function StatCard({ title, value, icon, color }) {
  const colorClasses = {
    blue: 'bg-blue-900/50 border-blue-700',
    green: 'bg-green-900/50 border-green-700',
    purple: 'bg-purple-900/50 border-purple-700',
    orange: 'bg-orange-900/50 border-orange-700',
  }

  return (
    <div className={`bg-gray-800 rounded-lg p-6 border ${colorClasses[color] || colorClasses.blue}`}>
      <div className="text-3xl mb-2">{icon}</div>
      <div className="text-3xl font-bold">{value}</div>
      <div className="text-gray-400 text-sm">{title}</div>
    </div>
  )
}

function HealthItem({ status, label }) {
  return (
    <div className="flex items-center justify-between py-2">
      <span>{label}</span>
      <span className={`px-3 py-1 rounded-full text-sm font-medium ${
        status
          ? 'bg-green-900 text-green-300'
          : 'bg-red-900 text-red-300'
      }`}>
        {status ? '✅ OK' : '❌ FAIL'}
      </span>
    </div>
  )
}

// Placeholder Components
function Tools() {
  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <h2 className="text-xl font-semibold mb-4">🔧 Інструменти</h2>
      <p className="text-gray-400">Список інструментів для запуску...</p>
    </div>
  )
}

function Search() {
  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <h2 className="text-xl font-semibold mb-4">🔍 Пошук</h2>
      <input
        type="text"
        placeholder="Введіть запит..."
        className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
      />
    </div>
  )
}

function Graph() {
  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <h2 className="text-xl font-semibold mb-4">🌐 Візуалізація графу</h2>
      <p className="text-gray-400">Інтерактивний граф концептів...</p>
    </div>
  )
}

function Settings() {
  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <h2 className="text-xl font-semibold mb-4">⚙️ Налаштування</h2>
      <p className="text-gray-400">Конфігурація системи...</p>
    </div>
  )
}

export default App
