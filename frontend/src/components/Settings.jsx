/**
 * Settings component — налаштування системи.
 * 
 * Показує:
 * - Конфігурацію wiki-кореня
 * - API статус
 * - Можливість оновити конфігурацію
 */

import { useState, useEffect } from 'react';
import { api } from '../services/api';

function Settings() {
  const [health, setHealth] = useState(null);
  const [config, setConfig] = useState({
    wiki_root: '',
    raw_root: '',
    index_file: 'index.md',
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const healthData = await api.getHealth();
      setHealth(healthData);
      setConfig({
        wiki_root: healthData.wiki_root || '',
        raw_root: healthData.raw_root || '',
        index_file: healthData.index_file || 'index.md',
      });
      setError(null);
    } catch (err) {
      setError(err.message || 'Не вдалося завантажити налаштування');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      // In a real app, this would POST to /api/v1/settings
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err.message || 'Не вдалося зберегти налаштування');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-xl text-gray-400">Завантаження...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">⚙️ Налаштування</h2>

      {success && (
        <div className="bg-green-900/50 border border-green-700 rounded-lg p-4 text-green-300">
          ✅ Налаштування збережено
        </div>
      )}

      {error && (
        <div className="bg-red-900/50 border border-red-700 rounded-lg p-4 text-red-300">
          {error}
        </div>
      )}

      {/* System Info */}
      {health && (
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="text-lg font-semibold mb-4">🖥️ Система</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">API Status</span>
              <span className={health.status === 'ok' ? 'text-green-300' : 'text-red-300'}>
                {health.status}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Wiki Root</span>
              <span className="text-white">{health.wiki_root}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Wiki Exists</span>
              <span className={health.wiki_exists ? 'text-green-300' : 'text-red-300'}>
                {health.wiki_exists ? '✅ Так' : '❌ Ні'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Configuration */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-lg font-semibold mb-4">📁 Конфігурація шляхів</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Wiki Root</label>
            <input
              type="text"
              value={config.wiki_root}
              onChange={(e) => setConfig({ ...config, wiki_root: e.target.value })}
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Raw Root</label>
            <input
              type="text"
              value={config.raw_root}
              onChange={(e) => setConfig({ ...config, raw_root: e.target.value })}
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Index File</label>
            <input
              type="text"
              value={config.index_file}
              onChange={(e) => setConfig({ ...config, index_file: e.target.value })}
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
            />
          </div>
          <button
            onClick={handleSave}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg"
          >
            💾 Зберегти
          </button>
        </div>
      </div>
    </div>
  );
}

export default Settings;
