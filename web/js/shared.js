/**
 * SentimentIQ — Shared Utilities
 * Hàm dùng chung cho tất cả trang: Dashboard, Client, Chatbot
 */

const API_BASE = 'http://localhost:8000';

// ══════════════════════════════════════════════════════════
// HTML ESCAPE
// ══════════════════════════════════════════════════════════
function escapeHtml(str) {
  if (typeof str !== 'string') return String(str ?? '');
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// ══════════════════════════════════════════════════════════
// API FETCH
// ══════════════════════════════════════════════════════════
async function apiFetch(endpoint, options = {}) {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// ══════════════════════════════════════════════════════════
// LOADING OVERLAY
// ══════════════════════════════════════════════════════════
function showLoading() {
  document.getElementById('loading-overlay')?.classList.remove('hidden');
}

function hideLoading() {
  document.getElementById('loading-overlay')?.classList.add('hidden');
}

// ══════════════════════════════════════════════════════════
// API STATUS CHECK
// ══════════════════════════════════════════════════════════
async function checkApiStatus() {
  const dot  = document.getElementById('status-dot');
  const text = document.getElementById('status-text');
  if (!dot || !text) return;
  try {
    const data = await fetch(`${API_BASE}/`, { signal: AbortSignal.timeout(3000) });
    dot.className  = 'status-dot online';
    text.textContent = 'API đang chạy';
    return await data.json();
  } catch {
    dot.className  = 'status-dot offline';
    text.textContent = 'API offline';
    return null;
  }
}

// ══════════════════════════════════════════════════════════
// MOBILE SIDEBAR MENU
// ══════════════════════════════════════════════════════════
function initMobileMenu() {
  document.getElementById('menu-btn')?.addEventListener('click', () => {
    document.getElementById('sidebar').classList.toggle('open');
  });
}
