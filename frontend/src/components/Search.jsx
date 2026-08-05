/**
 * Search component — пошук по wiki-сторінках.
 * 
 * Підтримує:
 * - Повнотекстовий пошук за запитом
 * - Фільтрація за типом
 * - Відображення результатів з підсвіткою контексту
 */

import { useState } from 'react';
import { api } from '../services/api';

function Search() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [typeFilter, setTypeFilter] = useState('');

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    try {
      setLoading(true);
      const data = await api.search(query, {
        limit: 20,
        ...(typeFilter && { type: typeFilter }),
      });
      setResults(data.results || []);
      setError(null);
    } catch (err) {
      setError(err.message || 'Пошук не вдався');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">🔍 Пошук по Wiki</h2>

      {/* Search Form */}
      <form onSubmit={handleSearch} className="flex gap-4">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Введіть запит для пошуку..."
          className="flex-1 px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white text-lg"
        />
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white"
        >
          <option value="">Всі типи</option>
          <option value="article">Статті</option>
          <option value="event">Події</option>
          <option value="concept">Концепти</option>
        </select>
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg disabled:opacity-50"
        >
          {loading ? 'Шукаю...' : '🔎'}
        </button>
      </form>

      {/* Results */}
      {error && (
        <div className="bg-red-900/50 border border-red-700 rounded-lg p-4 text-red-300">
          {error}
        </div>
      )}

      {results.length > 0 && (
        <div className="space-y-3">
          <div className="text-gray-400">Знайдено: {results.length}</div>
          {results.map((result, index) => (
            <div
              key={index}
              className="bg-gray-800 rounded-lg p-4 border border-gray-700 hover:border-blue-600 transition-colors"
            >
              <h3 className="font-semibold text-lg text-blue-300">
                {result.title || result.slug}
              </h3>
              <div className="text-gray-400 text-sm mb-2">
                {result.slug} • {result.type || 'N/A'}
              </div>
              {result.content && (
                <p className="text-gray-300 text-sm">
                  {result.content.substring(0, 300)}...
                </p>
              )}
              <div className="flex gap-2 mt-2">
                {result.tags?.map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-1 bg-blue-900/50 text-blue-300 text-xs rounded"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && !error && results.length === 0 && query && (
        <div className="text-center py-8 text-gray-400">
          Нічого не знайдено
        </div>
      )}
    </div>
  );
}

export default Search;
