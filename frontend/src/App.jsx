import { useState } from 'react'
import './App.css'

// Lazy-load components for better performance
import Dashboard from './components/Dashboard'
import Tools from './components/Tools'
import Search from './components/Search'
import Graph from './components/Graph'
import Settings from './components/Settings'

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')

  const tabs = [
    { id: 'dashboard', label: '📊 Dashboard' },
    { id: 'tools', label: '🔧 Інструменти' },
    { id: 'pages', label: '📄 Сторінки' },
    { id: 'search', label: '🔍 Пошук' },
    { id: 'graph', label: '🌐 Граф' },
    { id: 'settings', label: '⚙️ Налаштування' },
  ]

  const renderTab = () => {
    switch (activeTab) {
      case 'dashboard': return <Dashboard />
      case 'tools': return <Tools />
      case 'pages': return import('./components/Pages').then(m => <m.default />)
      case 'search': return <Search />
      case 'graph': return <Graph />
      case 'settings': return <Settings />
      default: return <Dashboard />
    }
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold">OSLW</h1>
          <p className="text-gray-400 text-sm">Open Source Lightweight Wiki Management System</p>
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
        {renderTab()}
      </main>
    </div>
  )
}

export default App
