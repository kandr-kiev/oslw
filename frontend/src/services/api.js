const API_BASE = '/api';

export const api = {
  // Dashboard
  getDashboard: async () => {
    const response = await fetch(`${API_BASE}/dashboard`);
    return response.json();
  },

  // Tools
  runTool: async (toolName) => {
    const response = await fetch(`${API_BASE}/tools/${toolName}/run`, {
      method: 'POST',
    });
    return response.json();
  },

  // Search
  search: async (query) => {
    const response = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}`);
    return response.json();
  },

  // Graph
  getGraph: async () => {
    const response = await fetch(`${API_BASE}/graph`);
    return response.json();
  },

  // Health
  getHealth: async () => {
    const response = await fetch(`${API_BASE}/health`);
    return response.json();
  },
};
