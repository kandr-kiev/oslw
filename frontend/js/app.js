/**
 * OSLW Wiki Frontend Application
 * 
 * SPA для перегляду wiki сторінок з API OSLW.
 * Підтримує:
 * - Перегляд списку сторінок
 * - Пошук по всіх сторінках
 * - Статистика wiki
 * - Детальний перегляд сторінок
 * - Пагінація та фільтрація
 */

// ============================================
// State Management
// ============================================

const state = {
    currentPage: 'pages',
    pages: [],
    stats: null,
    searchResults: [],
    pagination: {
        offset: 0,
        limit: 50,
        total: 0,
    },
    filters: {
        category: '',
        searchQuery: '',
    },
};

// ============================================
// API Client
// ============================================

const API = {
    async get(endpoint, params = {}) {
        const url = new URL(endpoint, window.location.origin);
        Object.entries(params).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== '') {
                url.searchParams.append(key, value);
            }
        });

        try {
            const response = await fetch(url.toString());
            if (!response.ok) {
                throw new Error(`API Error: ${response.status} ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`API GET ${endpoint} failed:`, error);
            throw error;
        }
    },

    async listPages(category = '', limit = 50, offset = 0) {
        return this.get('/api/pages', { category, limit, offset });
    },

    async getPage(slug) {
        return this.get(`/api/pages/${slug}`);
    },

    async getStats() {
        return this.get('/api/stats');
    },

    async search(query, limit = 50) {
        return this.get('/api/search', { q: query, limit });
    },
};

// ============================================
// Navigation
// ============================================

function switchView(viewName) {
    // Update nav buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === viewName);
    });

    // Update views
    document.querySelectorAll('.view').forEach(view => {
        view.classList.toggle('active', view.id === `${viewName}-view`);
    });

    state.currentPage = viewName;

    // Load data for the view
    switch (viewName) {
        case 'pages':
            loadPages();
            break;
        case 'stats':
            loadStats();
            break;
        case 'search':
            // Search view is loaded on demand
            break;
    }
}

// ============================================
// Pages View
// ============================================

async function loadPages() {
    const pagesList = document.getElementById('pages-list');
    pagesList.innerHTML = '<div class="loading">Завантаження...</div>';

    try {
        const data = await API.listPages(
            state.filters.category,
            state.pagination.limit,
            state.pagination.offset,
        );

        state.pages = data.pages;
        state.pagination.total = data.total;

        if (data.pages.length === 0) {
            pagesList.innerHTML = '<div class="empty-state">Не знайдено сторінок</div>';
            return;
        }

        pagesList.innerHTML = data.pages.map(page => `
            <div class="page-card" onclick="showPage('${page.slug}')">
                <div class="page-card-title">${escapeHtml(page.title)}</div>
                <div class="page-card-meta">
                    <span>📁 ${escapeHtml(page.type)}</span>
                    ${page.created ? `<span>📅 ${formatDate(page.created)}</span>` : ''}
                </div>
                <div class="page-card-tags">
                    ${page.tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}
                </div>
            </div>
        `).join('');

        renderPagination();
        updateCategoryFilter();

    } catch (error) {
        pagesList.innerHTML = `<div class="empty-state">Помилка завантаження: ${escapeHtml(error.message)}</div>`;
    }
}

function renderPagination() {
    const pagination = document.getElementById('pagination');
    const { offset, limit, total } = state.pagination;
    const totalPages = Math.ceil(total / limit);
    const currentPage = Math.floor(offset / limit) + 1;

    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }

    let html = '';

    // Previous button
    html += `<button class="page-btn" ${offset === 0 ? 'disabled' : ''} 
                    onclick="changePage(${offset - limit})">← Попередня</button>`;

    // Page numbers
    const maxVisible = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);

    if (endPage - startPage < maxVisible - 1) {
        startPage = Math.max(1, endPage - maxVisible + 1);
    }

    if (startPage > 1) {
        html += `<button class="page-btn" onclick="changePage(0)">1</button>`;
        if (startPage > 2) html += `<span class="page-btn" style="cursor:default">...</span>`;
    }

    for (let i = startPage; i <= endPage; i++) {
        html += `<button class="page-btn ${i === currentPage ? 'active' : ''}" 
                        onclick="changePage(${(i - 1) * limit})">${i}</button>`;
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) html += `<span class="page-btn" style="cursor:default">...</span>`;
        html += `<button class="page-btn" onclick="changePage(${(totalPages - 1) * limit})">${totalPages}</button>`;
    }

    // Next button
    html += `<button class="page-btn" ${offset + limit >= total ? 'disabled' : ''} 
                    onclick="changePage(${offset + limit})">Наступна →</button>`;

    html += `<span class="page-btn" style="cursor:default">Всього: ${total} сторінок</span>`;

    pagination.innerHTML = html;
}

function changePage(offset) {
    state.pagination.offset = offset;
    loadPages();
    window.scrollTo(0, 0);
}

function updateCategoryFilter() {
    const select = document.getElementById('category-filter');
    const currentValue = select.value;

    // Extract unique categories from pages
    const categories = [...new Set(state.pages.map(p => p.type))].sort();

    select.innerHTML = '<option value="">Всі категорії</option>' +
        categories.map(cat => `<option value="${cat}" ${cat === currentValue ? 'selected' : ''}>${cat}</option>`).join('');
}

// ============================================
// Stats View
// ============================================

async function loadStats() {
    const statsContent = document.getElementById('stats-content');
    statsContent.innerHTML = '<div class="loading">Завантаження...</div>';

    try {
        const data = await API.getStats();
        state.stats = data;

        statsContent.innerHTML = `
            <div class="stat-card">
                <h3>Загальна статистика</h3>
                <div class="stat-big-number">${data.total_pages}</div>
                <div class="stat-item">
                    <span class="stat-label">Всього сторінок</span>
                    <span class="stat-value">${data.total_pages}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Всього тегів</span>
                    <span class="stat-value">${data.total_tags}</span>
                </div>
            </div>

            <div class="stat-card">
                <h3>Типи сторінок</h3>
                ${Object.entries(data.types).map(([type, count]) => `
                    <div class="stat-item">
                        <span class="stat-label">${escapeHtml(type)}</span>
                        <span class="stat-value">${count}</span>
                    </div>
                `).join('')}
            </div>

            <div class="stat-card">
                <h3>Категорії</h3>
                ${Object.entries(data.categories).map(([cat, count]) => `
                    <div class="stat-item">
                        <span class="stat-label">${escapeHtml(cat)}</span>
                        <span class="stat-value">${count}</span>
                    </div>
                `).join('')}
            </div>

            <div class="stat-card">
                <h3>Теги (${data.tags.length})</h3>
                <div class="page-card-tags" style="padding: 0.5rem 0;">
                    ${data.tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}
                </div>
            </div>
        `;

    } catch (error) {
        statsContent.innerHTML = `<div class="empty-state">Помилка завантаження: ${escapeHtml(error.message)}</div>`;
    }
}

// ============================================
// Search View
// ============================================

async function performSearch(query) {
    const resultsContainer = document.getElementById('search-results');

    if (!query || query.trim().length < 2) {
        resultsContainer.innerHTML = '<div class="empty-state">Введіть мінімум 2 символи для пошуку</div>';
        return;
    }

    resultsContainer.innerHTML = '<div class="loading">Пошук...</div>';

    try {
        const data = await API.search(query.trim());

        if (data.results.length === 0) {
            resultsContainer.innerHTML = `<div class="empty-state">Не знайдено результатів для "${escapeHtml(query)}"</div>`;
            return;
        }

        resultsContainer.innerHTML = `
            <p style="margin-bottom: 1rem; color: var(--text-secondary);">
                Знайдено ${data.total} результатів для "${escapeHtml(query)}"
            </p>
            ${data.results.map(result => `
                <div class="search-result" onclick="showPage('${result.slug}')">
                    <div class="search-result-title">
                        ${escapeHtml(result.title)}
                        <span class="search-result-score">Релевантність: ${result.score}</span>
                    </div>
                    <div class="page-card-meta">
                        <span>📁 ${escapeHtml(result.type)}</span>
                        ${result.created ? `<span>📅 ${formatDate(result.created)}</span>` : ''}
                    </div>
                    <div class="page-card-tags">
                        ${result.tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}
                    </div>
                </div>
            `).join('')}
        `;

    } catch (error) {
        resultsContainer.innerHTML = `<div class="empty-state">Помилка пошуку: ${escapeHtml(error.message)}</div>`;
    }
}

// ============================================
// Page Detail View
// ============================================

async function showPage(slug) {
    const pageTitle = document.getElementById('page-title');
    const pageMeta = document.getElementById('page-meta');
    const pageContent = document.getElementById('page-content');

    // Show loading state
    pageTitle.textContent = 'Завантаження...';
    pageMeta.innerHTML = '';
    pageContent.innerHTML = '<div class="loading">Завантаження сторінки...</div>';

    // Show page view
    document.querySelectorAll('.view').forEach(view => view.classList.remove('active'));
    document.getElementById('page-view').classList.add('active');
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));

    try {
        const page = await API.getPage(slug);

        pageTitle.textContent = page.title;
        pageMeta.innerHTML = `
            <span>📁 Тип: ${escapeHtml(page.type)}</span>
            ${page.created ? `<span>📅 Створено: ${formatDate(page.created)}</span>` : ''}
            ${page.updated ? `<span>✏️ Оновлено: ${formatDate(page.updated)}</span>` : ''}
        `;

        // Render markdown content
        pageContent.innerHTML = renderMarkdown(page.content);

    } catch (error) {
        pageTitle.textContent = 'Помилка';
        pageContent.innerHTML = `<div class="empty-state">Помилка завантаження: ${escapeHtml(error.message)}</div>`;
    }
}

function goBack() {
    switchView(state.currentPage || 'pages');
}

// ============================================
// Markdown Renderer (Simple)
// ============================================

function renderMarkdown(text) {
    if (!text) return '<p>Немає контенту</p>';

    let html = escapeHtml(text);

    // Code blocks
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
        return `<pre><code class="language-${lang}">${code.trim()}</code></pre>`;
    });

    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Headers
    html = html.replace(/^#### (.+)$/gm, '<h4>$1</h4>');
    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

    // Bold and italic
    html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');

    // Images
    html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" style="max-width:100%;" />');

    // Blockquotes
    html = html.replace(/^&gt; (.+)$/gm, '<blockquote>$1</blockquote>');

    // Unordered lists
    html = html.replace(/^[\-\*] (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

    // Ordered lists
    html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

    // Tables
    html = html.replace(/\|(.+)\|\n\|[-\s|:]+\|\n((?:\|.+\|\n?)*)/g, (match, header, body) => {
        const headers = header.split('|').map(h => h.trim()).filter(Boolean);
        const rows = body.trim().split('\n').map(row =>
            row.split('|').map(cell => cell.trim()).filter(Boolean)
        );

        let tableHtml = '<table><thead><tr>';
        headers.forEach(h => tableHtml += `<th>${h}</th>`);
        tableHtml += '</tr></thead><tbody>';
        rows.forEach(row => {
            tableHtml += '<tr>';
            row.forEach(cell => tableHtml += `<td>${cell}</td>`);
            tableHtml += '</tr>';
        });
        tableHtml += '</tbody></table>';
        return tableHtml;
    });

    // Paragraphs
    html = html.replace(/\n\n/g, '</p><p>');
    html = html.replace(/\n/g, '<br>');

    // Clean up
    html = `<p>${html}</p>`;
    html = html.replace(/<p><(h[1-4]|ul|ol|pre|blockquote|table)/g, '<$1');
    html = html.replace(/<\/(h[1-4]|ul|ol|pre|blockquote|table)><\/p>/g, '</$1>');
    html = html.replace(/<p><\/p>/g, '');

    return html;
}

// ============================================
// Utilities
// ============================================

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    try {
        const date = new Date(dateStr);
        return date.toLocaleDateString('uk-UA');
    } catch {
        return dateStr;
    }
}

// ============================================
// Event Listeners
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // Navigation buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => switchView(btn.dataset.view));
    });

    // Back button
    document.getElementById('back-btn').addEventListener('click', goBack);

    // Search in header
    document.getElementById('search-btn').addEventListener('click', () => {
        const query = document.getElementById('search-input').value;
        switchView('search');
        performSearch(query);
    });

    document.getElementById('search-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const query = e.target.value;
            switchView('search');
            performSearch(query);
        }
    });

    // Category filter
    document.getElementById('category-filter').addEventListener('change', (e) => {
        state.filters.category = e.target.value;
        state.pagination.offset = 0;
        loadPages();
    });

    // Limit input
    document.getElementById('limit-input').addEventListener('change', (e) => {
        const limit = parseInt(e.target.value) || 50;
        state.pagination.limit = Math.min(1000, Math.max(1, limit));
        state.pagination.offset = 0;
        loadPages();
    });

    // Search view search
    const searchViewInput = document.querySelector('#search-view input');
    if (searchViewInput) {
        searchViewInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') performSearch(e.target.value);
        });
    }

    // Initial load
    loadPages();
});
