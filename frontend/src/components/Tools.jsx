/**
 * Tools component — управління інструментами OSLW.
 * 
 * Показує список доступних інструментів та дозволяє:
 * - Запускати діагностику (Doctor)
 * - Генерувати граф
 * - Створювати дайджести
 * - Перевіряти джерела
 */

import { useState } from 'react';
import { api } from '../services/api';

const TOOLS = [
  {
    id: 'doctor',
    name: 'Wiki Doctor',
    description: 'Аудит та виправлення проблем wiki',
    icon: '🏥',
    color: 'blue',
  },
  {
    id: 'graph',
    name: 'Graph Generator',
    description: 'Генерація графа знань',
    icon: '🌐',
    color: 'green',
  },
  {
    id: 'digest',
    name: 'Digest Generator',
    description: 'Створення дайджесту змін',
    icon: '📰',
    color: 'purple',
  },
  {
    id: 'sources',
    name: 'Source Checker',
    description: 'Перевірка актуальності джерел',
    icon: '📥',
    color: 'orange',
  },
];

function Tools() {
  const [runningTool, setRunningTool] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleRun = async (toolId) => {
    setRunningTool(toolId);
    setResult(null);
    setError(null);

    try {
      let data;
      switch (toolId) {
        case 'doctor':
          data = await api.cure({ fix_sha256: true, fix_wikilinks: true });
          break;
        case 'graph':
          data = await api.generateGraph();
          break;
        case 'digest':
          const text = await api.getDigest(24, 'markdown');
          data = { content: text };
          break;
        case 'sources':
          data = await api.checkSources();
          break;
        default:
          throw new Error('Невідомий інструмент');
      }
      setResult(data);
    } catch (err) {
      setError(err.message || 'Помилка виконання');
    } finally {
      setRunningTool(null);
    }
  };

  const colorClasses = {
    blue: 'bg-blue-900/50 border-blue-700 hover:border-blue-500',
    green: 'bg-green-900/50 border-green-700 hover:border-green-500',
    purple: 'bg-purple-900/50 border-purple-700 hover:border-purple-500',
    orange: 'bg-orange-900/50 border-orange-700 hover:border-orange-500',
  };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">🔧 Інструменти</h2>

      {/* Tools Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {TOOLS.map((tool) => (
          <div
            key={tool.id}
            className={`bg-gray-800 rounded-lg p-6 border ${colorClasses[tool.color]}`}
          >
            <div className="flex items-center gap-3 mb-3">
              <span className="text-3xl">{tool.icon}</span>
              <div>
                <h3 className="font-semibold">{tool.name}</h3>
                <p className="text-gray-400 text-sm">{tool.description}</p>
              </div>
            </div>
            <button
              onClick={() => handleRun(tool.id)}
              disabled={runningTool !== null}
              className="w-full px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg disabled:opacity-50 transition-colors"
            >
              {runningTool === tool.id ? '⏳ Виконується...' : '▶ Запустити'}
            </button>
          </div>
        ))}
      </div>

      {/* Results */}
      {result && (
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="text-lg font-semibold mb-3">📋 Результат</h3>
          {result.content ? (
            <pre className="bg-gray-900 p-4 rounded-lg overflow-x-auto text-sm whitespace-pre-wrap max-h-96 overflow-y-auto">
              {result.content}
            </pre>
          ) : (
            <pre className="bg-gray-900 p-4 rounded-lg overflow-x-auto text-sm">
              {JSON.stringify(result, null, 2)}
            </pre>
          )}
        </div>
      )}

      {error && (
        <div className="bg-red-900/50 border border-red-700 rounded-lg p-4 text-red-300">
          {error}
        </div>
      )}
    </div>
  );
}

export default Tools;
