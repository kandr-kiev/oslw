/**
 * OSLW API Client — інтеграція з FastAPI бекендом.
 * 
 * Endpoints:
 * - GET /api/v1/wiki/pages — список сторінок
 * - GET /api/v1/wiki/pages/{slug} — отримати сторінку
 * - POST /api/v1/wiki/pages — створити сторінку
 * - PUT /api/v1/wiki/pages/{slug} — оновити сторінку
 * - DELETE /api/v1/wiki/pages/{slug} — видалити сторінку
 * - POST /api/v1/search — пошук
 * - GET /api/v1/graph — граф знань
 * - POST /api/v1/graph/generate — згенерувати граф
 * - GET /api/v1/doctor/diagnose — аудит wiki
 * - POST /api/v1/doctor/cure — виправити проблеми
 * - GET /api/v1/digest — дайджест
 * - GET /api/v1/sources — список джерел
 * - POST /api/v1/sources/check — перевірити джерела
 * - GET /api/v1/health — health check
 */

const API_BASE = '/api/v1';

export const api = {
  // ==================== HEALTH ====================
  
  getHealth: async () => {
    const response = await fetch(`${API_BASE}/health`);
    return response.json();
  },

  // ==================== WIKI PAGES ====================
  
  getPages: async (params = {}) => {
    const query = new URLSearchParams({
      limit: params.limit || '50',
      offset: params.offset || '0',
      ...(params.type && { type: params.type }),
      ...(params.tag && { tag: params.tag }),
    }).toString();
    
    const response = await fetch(`${API_BASE}/wiki/pages?${query}`);
    return response.json();
  },

  getPage: async (slug, raw = false) => {
    const query = raw ? '?raw=true' : '';
    const response = await fetch(`${API_BASE}/wiki/pages/${encodeURIComponent(slug)}${query}`);
    return response.json();
  },

  createPage: async (pageData) => {
    const response = await fetch(`${API_BASE}/wiki/pages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(pageData),
    });
    return response.json();
  },

  updatePage: async (slug, pageData) => {
    const response = await fetch(`${API_BASE}/wiki/pages/${encodeURIComponent(slug)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(pageData),
    });
    return response.json();
  },

  deletePage: async (slug) => {
    const response = await fetch(`${API_BASE}/wiki/pages/${encodeURIComponent(slug)}`, {
      method: 'DELETE',
    });
    return response.json();
  },

  // ==================== SEARCH ====================
  
  search: async (query, options = {}) => {
    const response = await fetch(`${API_BASE}/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        limit: options.limit || 10,
        ...(options.type && { type: options.type }),
      }),
    });
    return response.json();
  },

  // ==================== GRAPH ====================
  
  getGraph: async () => {
    const response = await fetch(`${API_BASE}/graph`);
    return response.json();
  },

  generateGraph: async () => {
    const response = await fetch(`${API_BASE}/graph/generate`, {
      method: 'POST',
    });
    return response.json();
  },

  // ==================== DOCTOR ====================
  
  diagnose: async (layers = null) => {
    const query = layers ? `?layers=${layers}` : '';
    const response = await fetch(`${API_BASE}/doctor/diagnose${query}`);
    return response.json();
  },

  cure: async (options = {}) => {
    const response = await fetch(`${API_BASE}/doctor/cure`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(options),
    });
    return response.json();
  },

  // ==================== DIGEST ====================
  
  getDigest: async (hours = 24, format = 'markdown') => {
    const response = await fetch(`${API_BASE}/digest?hours=${hours}&format=${format}`);
    return response.text();
  },

  // ==================== SOURCES ====================
  
  getSources: async () => {
    const response = await fetch(`${API_BASE}/sources`);
    return response.json();
  },

  checkSources: async (sourceName = null) => {
    const response = await fetch(`${API_BASE}/sources/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source_name: sourceName }),
    });
    return response.json();
  },

  // ==================== DASHBOARD ====================
  
  getDashboard: async () => {
    // Gather stats from multiple endpoints
    const [pages, graph, health] = await Promise.all([
      api.getPages({ limit: 1000 }),
      api.getGraph(),
      api.getHealth(),
    ]);

    // Count tags
    const allTags = new Set();
    (pages.pages || []).forEach(p => (p.tags || []).forEach(t => allTags.add(t)));

    return {
      total_pages: pages.total || 0,
      total_tags: allTags.size,
      wiki_exists: health.wiki_exists,
      graph_nodes: graph.total || 0,
      graph_edges: (graph.edges || []).length,
    };
  },
};

export default api;
