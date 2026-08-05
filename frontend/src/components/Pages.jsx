/**
 * Pages component — управління wiki-сторінками.
 * 
 * Показує список сторінок з можливістю:
 * - Перегляд деталей сторінки
 * - Створення нової сторінки
 * - Редагування існуючої
 * - Видалення
 */

import { useState, useEffect } from 'react';
import { api } from '../services/api';

function Pages() {
  const [pages, setPages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedPage, setSelectedPage] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [filter, setFilter] = useState('');
  const [tagFilter, setTagFilter] = useState('');

  // Form state
  const [formData, setFormData] = useState({
    title: '',
    slug: '',
    tags: [],
    content: '',
  });

  useEffect(() => {
    loadPages();
  }, [filter, tagFilter]);

  const loadPages = async () => {
    try {
      setLoading(true);
      const params = {};
      if (filter) params.q = filter;
      if (tagFilter) params.tag = tagFilter;
      
      const data = await api.getPages(params);
      setPages(data.pages || []);
      setError(null);
    } catch (err) {
      setError(err.message || 'Не вдалося завантажити сторінки');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await api.createPage(formData);
      setShowCreateForm(false);
      setFormData({ title: '', slug: '', tags: [], content: '' });
      loadPages();
    } catch (err) {
      alert(`Помилка створення: ${err.message}`);
    }
  };

  const handleDelete = async (slug) => {
    if (!confirm(`Видалити сторінку "${slug}"?`)) return;
    try {
      await api.deletePage(slug);
      loadPages();
      setSelectedPage(null);
    } catch (err) {
      alert(`Помилка видалення: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">📄 Wiki Сторінки</h2>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg"
        >
          {showCreateForm ? '❌ Скасувати' : '➕ Створити'}
        </button>
      </div>

      {/* Create Form */}
      {showCreateForm && (
        <form onSubmit={handleCreate} className="bg-gray-800 rounded-lg p-6 border border-gray-700 space-y-4">
          <h3 className="text-lg font-semibold">Нова сторінка</h3>
          
          <div>
            <label className="block text-sm text-gray-400 mb-1">Заголовок</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
              required
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Slug</label>
            <input
              type="text"
              value={formData.slug}
              onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
              required
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Теги (через кому)</label>
            <input
              type="text"
              value={formData.tags.join(', ')}
              onChange={(e) => setFormData({ ...formData, tags: e.target.value.split(',').map(t => t.trim()) })}
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
              placeholder="machine-learning, neural-networks"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Зміст</label>
            <textarea
              value={formData.content}
              onChange={(e) => setFormData({ ...formData, content: e.target.value })}
              rows={8}
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
              required
            />
          </div>

          <button type="submit" className="px-6 py-2 bg-green-600 hover:bg-green-700 rounded-lg">
            Створити
          </button>
        </form>
      )}

      {/* Filters */}
      <div className="flex gap-4">
        <input
          type="text"
          placeholder="Пошук по назві..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="flex-1 px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
        />
        <input
          type="text"
          placeholder="Фільтр по тегу..."
          value={tagFilter}
          onChange={(e) => setTagFilter(e.target.value)}
          className="w-48 px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
        />
      </div>

      {/* Pages List */}
      {loading ? (
        <div className="text-center py-8 text-gray-400">Завантаження...</div>
      ) : error ? (
        <div className="bg-red-900/50 border border-red-700 rounded-lg p-4 text-red-300">{error}</div>
      ) : (
        <div className="space-y-3">
          {pages.map((page) => (
            <div
              key={page.slug}
              className="bg-gray-800 rounded-lg p-4 border border-gray-700 hover:border-blue-600 transition-colors cursor-pointer"
              onClick={() => setSelectedPage(page)}
            >
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold text-lg">{page.title}</h3>
                  <p className="text-gray-400 text-sm">{page.slug}</p>
                  <div className="flex gap-2 mt-2">
                    {page.tags?.map((tag) => (
                      <span key={tag} className="px-2 py-1 bg-blue-900/50 text-blue-300 text-xs rounded">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(page.slug);
                  }}
                  className="px-3 py-1 bg-red-600/50 hover:bg-red-600 text-red-300 rounded text-sm"
                >
                  Видалити
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Page Detail Modal */}
      {selectedPage && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold">{selectedPage.title}</h3>
              <button
                onClick={() => setSelectedPage(null)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>
            <pre className="bg-gray-900 p-4 rounded-lg overflow-x-auto text-sm whitespace-pre-wrap">
              {selectedPage.content || 'No content'}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

export default Pages;
