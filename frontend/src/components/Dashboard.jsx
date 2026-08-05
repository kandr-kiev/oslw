/**
 * Dashboard component — відображає статистику wiki-системи.
 * 
 * Показує:
 * - Загальна кількість сторінок, тегів, raw джерел
 * - Статус системи (health check)
 * - Останні зміни
 * - Швидкі дії
 */

import { useState, useEffect } from 'react';
import { api } from '../services/api';

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [health, setHealth] = useState(null);
  const [recentPages, setRecentPages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const [dashboardData, healthData, recentData] = await Promise.all([
        api.getDashboard(),
        api.getHealth(),
        api.getPages({ limit: 5 }),
      ]);

      setStats(dashboardData);
      setHealth(healthData);
      setRecentPages(recentData.pages || []);
      setError(null);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
      setError(err.message || 'Не вдалося завантажити дані');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickAction = async (action) => {
    try {
      switch (action) {
        case 'doctor':
          await api.cure({ fix_sha256: true, fix_wikilinks: true });
          alert('Wiki Doctor завершено');
          break;
        case 'graph':
          await api.generateGraph();
          alert('Граф оновлено');
          break;
        case 'digest':
          const digest = await api.getDigest(24, 'markdown');
          alert(`Дайджест:\n${digest.substring(0, 200)}...`);
          break;
        default:
          break;
      }
      loadDashboard();
    } catch (err) {
      alert(`Помилка: ${err.message}`);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-xl text-gray-400">Завантаження...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/50 border border-red-700 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-red-300 mb-2">⚠️ Помилка</h2>
        <p className="text-red-200">{error}</p>
        <button
          onClick={loadDashboard}
          className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg"
        >
          Повторити
        </button>
      </div>
    );
  }

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
          title="Node у графі"
          value={stats?.graph_nodes || 0}
          icon="🔗"
          color="purple"
        />
        <StatCard
          title="Ребер у графі"
          value={stats?.graph_edges || 0}
          icon="🌐"
          color="orange"
        />
      </div>

      {/* Health Check */}
      {health && (
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold mb-4">🏥 Health Check</h2>
          <div className="space-y-2">
            <HealthItem
              status={health.wiki_exists}
              label="Wiki Root Exists"
            />
            <HealthItem
              status={health.status === 'ok'}
              label="API Status: OK"
            />
            <div className="text-gray-400 text-sm mt-2">
              Wiki: {health.wiki_root}
            </div>
          </div>
        </div>
      )}

      {/* Recent Pages */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-xl font-semibold mb-4">📝 Останні зміни</h2>
        {recentPages.length > 0 ? (
          <div className="space-y-2">
            {recentPages.map((page) => (
              <div
                key={page.slug}
                className="flex items-center justify-between py-2 px-3 bg-gray-700/50 rounded"
              >
                <div>
                  <div className="font-medium">{page.title}</div>
                  <div className="text-gray-400 text-sm">{page.slug}</div>
                </div>
                <div className="text-gray-400 text-sm">
                  {page.updated_at || 'N/A'}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-gray-400">Немає даних</div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-xl font-semibold mb-4">⚡ Швидкі дії</h2>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => handleQuickAction('doctor')}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
          >
            Запустити Wiki Doctor
          </button>
          <button
            onClick={() => handleQuickAction('graph')}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
          >
            Оновити граф
          </button>
          <button
            onClick={() => handleQuickAction('digest')}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors"
          >
            Згенерувати дайджест
          </button>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon, color }) {
  const colorClasses = {
    blue: 'bg-blue-900/50 border-blue-700',
    green: 'bg-green-900/50 border-green-700',
    purple: 'bg-purple-900/50 border-purple-700',
    orange: 'bg-orange-900/50 border-orange-700',
  };

  return (
    <div className={`bg-gray-800 rounded-lg p-6 border ${colorClasses[color] || colorClasses.blue}`}>
      <div className="text-3xl mb-2">{icon}</div>
      <div className="text-3xl font-bold">{value}</div>
      <div className="text-gray-400 text-sm">{title}</div>
    </div>
  );
}

function HealthItem({ status, label }) {
  return (
    <div className="flex items-center justify-between py-2">
      <span>{label}</span>
      <span
        className={`px-3 py-1 rounded-full text-sm font-medium ${
          status
            ? 'bg-green-900 text-green-300'
            : 'bg-red-900 text-red-300'
        }`}
      >
        {status ? '✅ OK' : '❌ FAIL'}
      </span>
    </div>
  );
}

export default Dashboard;
