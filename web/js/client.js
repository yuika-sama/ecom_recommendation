/**
 * SentimentIQ Client Page — client.js
 * Logic: Product search, Star rating, Review submit, Recommendations, Chatbot, LocalStorage
 */

const API_BASE    = 'http://localhost:8000';
const STORAGE_KEY = 'sentimentiq_reviews';
const EMOJIS      = ['👕','📱','💄','👟','🎮','📚','🍜','💻','⌚','🧴','🎒','🖥️','🎧','🏠','🌿'];

// ── State ──
let selectedProduct = null;
let currentRating   = 0;
let chatHistory     = [];
let searchDebounce  = null;
let allCategories   = [];

// ══════════════════════════════════════════════════════════
// INIT
// ══════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  checkApiStatus();
  loadCategories();
  initCharCount();
  loadHistoryUI();
  initMobileMenu();
  setInterval(checkApiStatus, 30_000);
});

function initMobileMenu() {
  document.getElementById('menu-btn')?.addEventListener('click', () => {
    document.getElementById('sidebar').classList.toggle('open');
  });
}

// ══════════════════════════════════════════════════════════
// API HELPERS
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

async function checkApiStatus() {
  const dot  = document.getElementById('status-dot');
  const text = document.getElementById('status-text');
  try {
    const data = await apiFetch('/');
    dot.className    = 'status-dot online';
    text.textContent = 'API đang chạy';
    // Cập nhật subtitle chatbot nếu có Gemini
    const sub = document.getElementById('chatbot-subtitle');
    if (sub) sub.textContent = data.gemini ? 'Gemini AI ✨' : 'Rule-based AI';
  } catch {
    dot.className    = 'status-dot offline';
    text.textContent = 'API offline';
  }
}

function showLoading()  { document.getElementById('loading-overlay')?.classList.remove('hidden'); }
function hideLoading()  { document.getElementById('loading-overlay')?.classList.add('hidden'); }

// ══════════════════════════════════════════════════════════
// PRODUCT SEARCH
// ══════════════════════════════════════════════════════════
async function loadCategories() {
  try {
    const data = await apiFetch('/api/products?limit=1');
    allCategories = (data.categories || []).slice(0, 12);
    renderCategoryChips();
  } catch (e) { console.warn('Khong load duoc categories:', e.message); }
}

function renderCategoryChips() {
  const wrap = document.getElementById('category-chips');
  if (!wrap) return;
  wrap.innerHTML = '<span class="chips-label">Danh mục:</span>';
  allCategories.forEach(cat => {
    const btn = document.createElement('button');
    btn.className = 'cat-chip';
    btn.textContent = cat;
    btn.onclick = () => {
      document.querySelectorAll('.cat-chip').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('product-search-input').value = cat;
      runSearch(cat);
    };
    wrap.appendChild(btn);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('product-search-input');
  if (input) {
    input.addEventListener('input', (e) => {
      clearTimeout(searchDebounce);
      const q = e.target.value.trim();
      document.getElementById('search-clear')?.classList.toggle('hidden', !q);
      if (q.length >= 2) {
        searchDebounce = setTimeout(() => runSearch(q), 350);
      } else {
        closeDropdown();
      }
    });
    // Đóng dropdown khi click ngoài
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.product-search-wrap')) closeDropdown();
    });
  }
});

async function runSearch(query, category = '') {
  const dropdown = document.getElementById('product-dropdown');
  if (!dropdown) return;
  dropdown.classList.remove('hidden');
  dropdown.innerHTML = '<div class="dropdown-loading">⏳ Đang tìm kiếm...</div>';
  try {
    const catParam = category ? `&category=${encodeURIComponent(category)}` : '';
    const data = await apiFetch(`/api/products?search=${encodeURIComponent(query)}&limit=12${catParam}`);
    renderDropdown(data.products || []);
  } catch {
    dropdown.innerHTML = '<div class="dropdown-empty">⚠️ Không thể kết nối API</div>';
  }
}

function renderDropdown(products) {
  const dropdown = document.getElementById('product-dropdown');
  if (!dropdown) return;
  if (!products.length) {
    dropdown.innerHTML = '<div class="dropdown-empty">🔍 Không tìm thấy sản phẩm</div>';
    return;
  }
  dropdown.innerHTML = '';
  products.forEach((p, i) => {
    const item = document.createElement('div');
    item.className = 'dropdown-item';
    const price = p.price ? `${Number(p.price).toLocaleString('vi')}đ` : '';
    item.innerHTML = `
      <span class="dropdown-item-emoji">${EMOJIS[i % EMOJIS.length]}</span>
      <span class="dropdown-item-name">${escapeHtml(p.name || '')}</span>
      ${p.category ? `<span class="dropdown-item-cat">${escapeHtml(p.category)}</span>` : ''}
      ${price ? `<span class="dropdown-item-price">${price}</span>` : ''}
    `;
    item.onclick = () => selectProduct(p, i);
    dropdown.appendChild(item);
  });
}

function selectProduct(product, emojiIdx = 0) {
  selectedProduct = product;
  const emoji = EMOJIS[emojiIdx % EMOJIS.length];
  const price = product.price ? `${Number(product.price).toLocaleString('vi')}đ` : 'Liên hệ';

  document.getElementById('sel-emoji').textContent = emoji;
  document.getElementById('sel-name').textContent  = product.name || 'Sản phẩm';
  document.getElementById('sel-cat').textContent   = product.category || '';
  document.getElementById('sel-price').textContent = price;
  document.getElementById('selected-product-card').classList.remove('hidden');
  document.getElementById('review-hint').classList.add('hidden');

  // Cập nhật search input
  document.getElementById('product-search-input').value = product.name || '';
  document.getElementById('search-clear')?.classList.remove('hidden');
  closeDropdown();
}

function clearProductSearch() {
  document.getElementById('product-search-input').value = '';
  document.getElementById('search-clear')?.classList.add('hidden');
  closeDropdown();
}

function clearProductSelection() {
  selectedProduct = null;
  document.getElementById('selected-product-card').classList.add('hidden');
  document.getElementById('product-search-input').value = '';
  document.getElementById('search-clear')?.classList.add('hidden');
  document.getElementById('review-hint').classList.remove('hidden');
  document.querySelectorAll('.cat-chip').forEach(b => b.classList.remove('active'));
}

function closeDropdown() {
  document.getElementById('product-dropdown')?.classList.add('hidden');
}

// ══════════════════════════════════════════════════════════
// STAR RATING
// ══════════════════════════════════════════════════════════
const RATING_LABELS = ['', 'Rất tệ 😞', 'Tệ 😕', 'Bình thường 😐', 'Tốt 😊', 'Tuyệt vời 🤩'];

function setRating(val) {
  currentRating = val;
  updateStarDisplay(val);
  document.getElementById('rating-text').textContent = RATING_LABELS[val] || '';
}

function hoverRating(val) { updateStarDisplay(val, true); }

function resetHover() { updateStarDisplay(currentRating); }

function updateStarDisplay(val, isHover = false) {
  document.querySelectorAll('.star').forEach(s => {
    const sv = parseInt(s.dataset.val);
    s.classList.remove('active', 'hover');
    if (sv <= val) s.classList.add(isHover ? 'hover' : 'active');
  });
}

function initCharCount() {
  const ta = document.getElementById('review-comment');
  if (!ta) return;
  ta.addEventListener('input', () => {
    const len = ta.value.length;
    document.getElementById('char-count').textContent = len;
    if (len > 500) ta.value = ta.value.slice(0, 500);
  });
}

// ══════════════════════════════════════════════════════════
// SUBMIT REVIEW
// ══════════════════════════════════════════════════════════
async function submitReview() {
  const comment = document.getElementById('review-comment')?.value.trim();
  if (!selectedProduct) {
    document.getElementById('review-hint').classList.remove('hidden');
    document.getElementById('section-product').scrollIntoView({ behavior: 'smooth' });
    return;
  }
  if (!comment) { alert('Vui lòng nhập bình luận!'); return; }
  if (!currentRating) { alert('Vui lòng chọn số sao!'); return; }

  const btn = document.getElementById('btn-submit-review');
  btn.disabled = true;
  btn.innerHTML = '<span class="btn-icon">⏳</span> Đang phân tích...';
  showLoading();

  try {
    const data = await apiFetch('/api/review', {
      method: 'POST',
      body: JSON.stringify({
        product_id: String(selectedProduct.product_id || selectedProduct.name || ''),
        comment,
        rating: currentRating,
      }),
    });

    renderResults(data);
    saveToStorage({ product: selectedProduct, comment, rating: currentRating, result: data });
    loadHistoryUI();

    document.getElementById('section-results').classList.remove('hidden');
    setTimeout(() => {
      document.getElementById('section-results').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);

  } catch (e) {
    alert(`Lỗi phân tích: ${e.message}\nHãy đảm bảo API đang chạy.`);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span class="btn-icon">🚀</span> Gửi đánh giá & Nhận gợi ý';
    hideLoading();
  }
}

function clearReviewForm() {
  document.getElementById('review-comment').value = '';
  document.getElementById('char-count').textContent = '0';
  currentRating = 0;
  updateStarDisplay(0);
  document.getElementById('rating-text').textContent = 'Chưa đánh giá';
  document.getElementById('section-results').classList.add('hidden');
}

// ══════════════════════════════════════════════════════════
// RENDER RESULTS
// ══════════════════════════════════════════════════════════
function renderResults(data) {
  const combined = data.combined_label;
  const isPos = combined === 'Tích cực';
  const isNeg = combined === 'Tiêu cực';

  // --- Sentiment card ---
  const sc = document.getElementById('rc-sentiment');
  sc.className = `result-card-new ${isPos ? 'positive' : isNeg ? 'negative' : 'neutral'}`;
  document.getElementById('rc-sentiment-icon').textContent = isPos ? '😊' : isNeg ? '😞' : '😐';
  document.getElementById('rc-sentiment-val').textContent  = data.sentiment?.label || '—';

  const posP = Math.round((data.sentiment?.confidence?.tich_cu ?? 0) * 100);
  const negP = Math.round((data.sentiment?.confidence?.tieu_cu ?? 0) * 100);
  document.getElementById('rc-sentiment-bars').innerHTML = `
    <div class="rc-bar-row">
      <span class="rc-bar-label">Tích cực</span>
      <div class="rc-bar-track"><div class="rc-bar-fill" id="rfbar-pos" style="width:0%;background:linear-gradient(90deg,#10b981,#34d399)"></div></div>
      <span class="rc-bar-pct">${posP}%</span>
    </div>
    <div class="rc-bar-row">
      <span class="rc-bar-label">Tiêu cực</span>
      <div class="rc-bar-track"><div class="rc-bar-fill" id="rfbar-neg" style="width:0%;background:linear-gradient(90deg,#ef4444,#f87171)"></div></div>
      <span class="rc-bar-pct">${negP}%</span>
    </div>`;
  setTimeout(() => {
    document.getElementById('rfbar-pos').style.width = `${posP}%`;
    document.getElementById('rfbar-neg').style.width = `${negP}%`;
  }, 80);

  // --- Rating card ---
  const rating = data.rating || 0;
  document.getElementById('rc-stars').textContent     = '★'.repeat(rating) + '☆'.repeat(5 - rating);
  document.getElementById('rc-rating-val').textContent = data.rating_label || '—';

  // --- Overall card ---
  const oc = document.getElementById('rc-overall');
  oc.className = `result-card-new ${isPos ? 'positive' : isNeg ? 'negative' : 'neutral'}`;
  document.getElementById('rc-overall-icon').textContent = isPos ? '✅' : isNeg ? '❌' : '⚠️';
  document.getElementById('rc-overall-val').textContent  = combined || '—';
  document.getElementById('rc-cluster-val').textContent  = data.cluster?.cluster_name
    ? `Chủ đề: ${data.cluster.cluster_name}` : '';

  // --- Recommendations ---
  const recType = data.rec_type === 'similar' ? 'similar' : 'alternative';
  const titleEl = document.getElementById('rec-title');
  titleEl.textContent = recType === 'similar'
    ? '🔵 Sản phẩm tương tự bạn có thể thích'
    : '🟢 Sản phẩm thay thế tốt hơn';
  renderRecGrid(data.recommendations || [], recType);
}

function renderRecGrid(products, recType) {
  const grid = document.getElementById('rec-grid');
  if (!products.length) {
    grid.innerHTML = '<p style="color:var(--text-muted);font-size:0.85rem">Không tìm thấy gợi ý phù hợp.</p>';
    return;
  }
  grid.innerHTML = '';
  products.forEach((p, i) => {
    const price = p.price ? `${Number(p.price).toLocaleString('vi')}đ` : 'Liên hệ';
    const score = p.similarity_score ? `Match ${Math.round(p.similarity_score * 100)}%` : '';
    const badgeClass  = recType === 'similar' ? 'badge-similar'     : 'badge-alternative';
    const badgeLabel  = recType === 'similar' ? 'Tương tự'          : 'Thay thế tốt hơn';
    const card = document.createElement('div');
    card.className = 'rec-card';
    card.onclick = () => {
      selectProduct(p, i);
      document.getElementById('section-product').scrollIntoView({ behavior: 'smooth' });
    };
    card.innerHTML = `
      <span class="rec-type-badge ${badgeClass}">${badgeLabel}</span>
      <div class="rec-emoji">${EMOJIS[i % EMOJIS.length]}</div>
      <div class="rec-name">${escapeHtml(p.name || 'Sản phẩm')}</div>
      <div class="rec-cat">${escapeHtml(p.category || '')}</div>
      <div class="rec-price">${price}</div>
      ${score ? `<div class="rec-score">${score}</div>` : ''}
    `;
    grid.appendChild(card);
  });
}

// ══════════════════════════════════════════════════════════
// LOCAL STORAGE — Persist reviews
// ══════════════════════════════════════════════════════════
function saveToStorage(entry) {
  const reviews = getStoredReviews();
  reviews.unshift({
    id:        Date.now(),
    timestamp: new Date().toISOString(),
    product:   entry.product,
    comment:   entry.comment,
    rating:    entry.rating,
    sentiment: entry.result?.sentiment?.label     || '—',
    combined:  entry.result?.combined_label        || '—',
  });
  localStorage.setItem(STORAGE_KEY, JSON.stringify(reviews.slice(0, 50)));
}

function getStoredReviews() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); } catch { return []; }
}

function clearHistory() {
  if (!confirm('Xóa toàn bộ lịch sử đánh giá?')) return;
  localStorage.removeItem(STORAGE_KEY);
  loadHistoryUI();
}

function loadHistoryUI() {
  const reviews = getStoredReviews();
  const list    = document.getElementById('history-list');
  if (!list) return;
  if (!reviews.length) {
    list.innerHTML = '<div class="history-empty">Chưa có đánh giá nào. Hãy thử đánh giá sản phẩm đầu tiên!</div>';
    return;
  }
  list.innerHTML = '';
  reviews.slice(0, 20).forEach((r, i) => {
    const combined = r.combined || r.sentiment || '—';
    const isPos = combined.includes('Tích cực');
    const isNeg = combined.includes('Tiêu cực');
    const badgeClass = isPos ? 'badge-pos' : isNeg ? 'badge-neg' : 'badge-neu';
    const stars   = '★'.repeat(r.rating || 0) + '☆'.repeat(5 - (r.rating || 0));
    const timeStr = r.timestamp ? new Date(r.timestamp).toLocaleString('vi') : '';
    const item = document.createElement('div');
    item.className = 'history-item';
    item.innerHTML = `
      <span class="history-item-emoji">${EMOJIS[i % EMOJIS.length]}</span>
      <div class="history-item-body">
        <div class="history-item-name">${escapeHtml(r.product?.name || 'Sản phẩm không xác định')}</div>
        <div class="history-item-comment">${escapeHtml(r.comment || '')}</div>
        <div class="history-item-meta">
          <span class="history-item-stars">${stars}</span>
          <span class="history-item-badge ${badgeClass}">${combined}</span>
          <span class="history-item-time">${timeStr}</span>
        </div>
      </div>
    `;
    list.appendChild(item);
  });
}

// ══════════════════════════════════════════════════════════
// CHATBOT
// ══════════════════════════════════════════════════════════
let chatbotOpen = false;

function toggleChatbot() {
  chatbotOpen = !chatbotOpen;
  document.getElementById('chatbot-panel').classList.toggle('hidden', !chatbotOpen);
  document.getElementById('fab-badge').classList.add('hidden');
  if (chatbotOpen) {
    document.getElementById('chatbot-input')?.focus();
    scrollChatBottom();
  }
}

function quickChat(msg) {
  document.getElementById('chatbot-input').value = msg;
  sendChatMessage();
}

async function sendChatMessage() {
  const input = document.getElementById('chatbot-input');
  const msg   = input?.value.trim();
  if (!msg) return;
  input.value = '';

  // Ẩn suggestions sau lần nhắn đầu
  document.getElementById('chat-suggestions')?.remove();

  appendBubble('user', escapeHtml(msg));
  chatHistory.push({ role: 'user', content: msg });

  const typingId = addTypingIndicator();

  try {
    const data = await apiFetch('/api/chatbot', {
      method: 'POST',
      body: JSON.stringify({
        message: msg,
        history: chatHistory.slice(-10),
        product_id: selectedProduct?.product_id ? String(selectedProduct.product_id) : null,
      }),
    });

    removeTypingIndicator(typingId);
    const reply = data.reply || 'Xin lỗi, tôi chưa hiểu. Bạn có thể hỏi lại không?';
    chatHistory.push({ role: 'model', content: reply });
    appendBubble('bot', formatReply(reply), data.products);

  } catch (e) {
    removeTypingIndicator(typingId);
    appendBubble('bot', `⚠️ Lỗi kết nối API: ${e.message}`);
  }
}

function appendBubble(role, html, products = null) {
  const container = document.getElementById('chatbot-messages');
  if (!container) return;
  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${role}`;
  bubble.innerHTML = html;

  // Nếu có sản phẩm đính kèm
  if (products && products.length && !products[0]?.type) {
    const list = document.createElement('div');
    list.className = 'chat-products';
    products.slice(0, 4).forEach((p, i) => {
      const price = p.price ? `${Number(p.price).toLocaleString('vi')}đ` : '';
      const item = document.createElement('div');
      item.className = 'chat-product-item';
      item.innerHTML = `
        <span class="chat-product-emoji">${EMOJIS[i % EMOJIS.length]}</span>
        <span class="chat-product-name">${escapeHtml(p.name || 'Sản phẩm')}</span>
        <span class="chat-product-price">${price}</span>
      `;
      item.onclick = () => {
        selectProduct(p, i);
        if (!chatbotOpen) toggleChatbot();
        document.getElementById('section-product').scrollIntoView({ behavior: 'smooth' });
      };
      list.appendChild(item);
    });
    bubble.appendChild(list);
  }

  container.appendChild(bubble);
  scrollChatBottom();

  // Notification badge nếu chatbot đóng
  if (!chatbotOpen && role === 'bot') {
    document.getElementById('fab-badge').classList.remove('hidden');
  }
}

function formatReply(text) {
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br/>');
}

function addTypingIndicator() {
  const id = 'typing-' + Date.now();
  const container = document.getElementById('chatbot-messages');
  const div = document.createElement('div');
  div.id = id;
  div.className = 'chat-bubble bot';
  div.innerHTML = `<div class="typing-indicator">
    <div class="typing-dot"></div>
    <div class="typing-dot"></div>
    <div class="typing-dot"></div>
  </div>`;
  container?.appendChild(div);
  scrollChatBottom();
  return id;
}

function removeTypingIndicator(id) {
  document.getElementById(id)?.remove();
}

function scrollChatBottom() {
  const el = document.getElementById('chatbot-messages');
  if (el) el.scrollTop = el.scrollHeight;
}

// ══════════════════════════════════════════════════════════
// UTILS
// ══════════════════════════════════════════════════════════
function escapeHtml(str) {
  if (typeof str !== 'string') return String(str ?? '');
  return str
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;').replace(/'/g,'&#039;');
}
