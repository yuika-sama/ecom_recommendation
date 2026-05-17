/**
 * SentimentIQ Dashboard — app.js
 * Kết nối Web Dashboard với FastAPI Backend
 * Phụ thuộc: shared.js (API_BASE, escapeHtml, apiFetch, showLoading, hideLoading, checkApiStatus, initMobileMenu)
 */

// ──────────────────────────────────────────────────────────
// KHỞI TẠO
// ──────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initMobileMenu();
  checkApiStatus();
  loadStats();

  // Tự động kiểm tra API mỗi 30 giây
  setInterval(checkApiStatus, 30_000);
});

// ──────────────────────────────────────────────────────────
// NAVIGATION
// ──────────────────────────────────────────────────────────
const TAB_TITLES = {
  overview:  'Tổng quan hệ thống',
  sentiment: 'Phân tích Cảm xúc',
  cluster:   'Phân cụm Chủ đề',
  rules:     'Luật Kết hợp',
  recommend: 'Gợi ý Sản phẩm',
};

function initNavigation() {
  document.querySelectorAll('.nav-item').forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.dataset.tab;
      switchTab(tab);

      // Đóng sidebar trên mobile
      if (window.innerWidth <= 900) {
        document.getElementById('sidebar').classList.remove('open');
      }
    });
  });
}

function switchTab(tabId) {
  document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
  document.getElementById(`nav-${tabId}`)?.classList.add('active');

  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  document.getElementById(`tab-${tabId}`)?.classList.add('active');

  document.getElementById('topbar-title').textContent = TAB_TITLES[tabId] || tabId;
}

// ──────────────────────────────────────────────────────────
// OVERVIEW — Stats & Charts
// ──────────────────────────────────────────────────────────
const _chartInstances = {};

function destroyChart(id) {
  if (_chartInstances[id]) {
    try { _chartInstances[id].destroy(); } catch (_) {}
    delete _chartInstances[id];
  }
}

async function loadStats() {
  try {
    const data = await apiFetch('/api/stats');
    const ds = data.dataset;
    if (ds && !ds.error) {
      document.getElementById('val-total').textContent    = ds.total_reviews?.toLocaleString('vi') ?? '—';
      document.getElementById('val-positive').textContent = ds.positive?.toLocaleString('vi') ?? '—';
      document.getElementById('val-negative').textContent = ds.negative?.toLocaleString('vi') ?? '—';
      renderSentimentChart(ds.positive, ds.negative);
      renderSourceChart(ds.sources || {});
    }
    const models = data.models || {};
    const readyCount = Object.values(models).filter(Boolean).length;
    document.getElementById('val-models').textContent = `${readyCount} / ${Object.keys(models).length}`;
    updateModelBadges(models);
  } catch (e) {
    console.warn('Không thể tải stats:', e.message);
    document.getElementById('val-total').textContent    = 'Offline';
    document.getElementById('val-positive').textContent = '—';
    document.getElementById('val-negative').textContent = '—';
    document.getElementById('val-models').textContent   = '—';
  }
}

function updateModelBadges(models) {
  const badgeNames = {
    naive_bayes:       'Naive Bayes',
    gmm_clustering:    'GMM Clustering',
    recommender:       'Recommender',
    association_rules: 'Assoc. Rules',
  };
  const container = document.getElementById('model-badges');
  if (!container) return;
  container.innerHTML = '';
  Object.entries(models).forEach(([key, ready]) => {
    const div = document.createElement('div');
    div.className = `model-badge ${ready ? 'ready' : 'error'}`;
    div.textContent = `${ready ? '✅' : '❌'} ${badgeNames[key] || key}`;
    container.appendChild(div);
  });
}

function renderSentimentChart(positive, negative) {
  destroyChart('chart-sentiment-dist');
  const ctx = document.getElementById('chart-sentiment-dist')?.getContext('2d');
  if (!ctx) return;
  _chartInstances['chart-sentiment-dist'] = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Tích cực', 'Tiêu cực'],
      datasets: [{
        data: [positive, negative],
        backgroundColor: ['rgba(16,185,129,0.8)', 'rgba(239,68,68,0.8)'],
        borderColor: ['#10b981', '#ef4444'],
        borderWidth: 2,
        hoverOffset: 8,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { color: '#94a3b8', padding: 16 } },
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.label}: ${ctx.parsed.toLocaleString('vi')} (${(ctx.parsed / (positive + negative) * 100).toFixed(1)}%)`,
          },
        },
      },
    },
  });
}

function renderSourceChart(sources) {
  destroyChart('chart-sources');
  const ctx = document.getElementById('chart-sources')?.getContext('2d');
  if (!ctx) return;
  const labels = Object.keys(sources).map(k => k.replace(/_/g, ' ').substring(0, 22));
  const values = Object.values(sources);
  const colors = ['rgba(124,58,237,0.8)', 'rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(245,158,11,0.8)'];
  _chartInstances['chart-sources'] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{ label: 'Số bình luận', data: values, backgroundColor: colors.slice(0, labels.length), borderRadius: 6 }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.08)' } },
        y: { ticks: { color: '#94a3b8', font: { size: 11 } }, grid: { display: false } },
      },
    },
  });
}

// ──────────────────────────────────────────────────────────
// SENTIMENT ANALYSIS
// ──────────────────────────────────────────────────────────
function setExample(text) {
  document.getElementById('sentiment-input').value = text;
}

function clearSentiment() {
  document.getElementById('sentiment-input').value = '';
  document.getElementById('sentiment-result')?.classList.add('hidden');
}

async function analyzeSentiment() {
  const text = document.getElementById('sentiment-input')?.value.trim();
  if (!text) { alert('Vui lòng nhập nội dung bình luận!'); return; }

  const btn = document.getElementById('btn-analyze-sentiment');
  btn.disabled = true;
  btn.textContent = '⏳ Đang phân tích...';
  showLoading();

  try {
    const data = await apiFetch('/api/sentiment', {
      method: 'POST',
      body: JSON.stringify({ text }),
    });

    const isPositive = data.label === 1;
    const posScore   = Math.round((data.confidence?.tich_cu ?? 0) * 100);
    const negScore   = Math.round((data.confidence?.tieu_cu ?? 0) * 100);

    const badge = document.getElementById('sentiment-badge');
    badge.textContent = isPositive ? '😊 Tích cực' : '😞 Tiêu cực';
    badge.className   = `result-badge ${isPositive ? 'positive' : 'negative'}`;

    document.getElementById('sentiment-confidence').textContent =
      `Độ tin cậy: ${isPositive ? posScore : negScore}%`;

    setTimeout(() => {
      document.getElementById('bar-positive').style.width = `${posScore}%`;
      document.getElementById('bar-negative').style.width = `${negScore}%`;
    }, 50);
    document.getElementById('pct-positive').textContent = `${posScore}%`;
    document.getElementById('pct-negative').textContent = `${negScore}%`;

    document.getElementById('processed-text-display').textContent =
      data.processed_text || '—';

    document.getElementById('sentiment-result').classList.remove('hidden');
  } catch (e) {
    alert(`Lỗi: ${e.message}\nHãy đảm bảo API server đang chạy.`);
  } finally {
    btn.disabled = false;
    btn.textContent = '🔍 Phân tích';
    hideLoading();
  }
}

// ──────────────────────────────────────────────────────────
// CLUSTER
// ──────────────────────────────────────────────────────────
function clearCluster() {
  document.getElementById('cluster-input').value = '';
  document.getElementById('cluster-result')?.classList.add('hidden');
}

async function analyzeCluster() {
  const text = document.getElementById('cluster-input')?.value.trim();
  if (!text) { alert('Vui lòng nhập nội dung!'); return; }

  const btn = document.getElementById('btn-cluster');
  btn.disabled = true;
  btn.textContent = '⏳ Đang phân cụm...';
  showLoading();

  try {
    const data = await apiFetch('/api/cluster', {
      method: 'POST',
      body: JSON.stringify({ text }),
    });

    document.getElementById('cluster-topic').textContent =
      `📌 Chủ đề: ${data.cluster_name || 'Không xác định'}`;

    const probsContainer = document.getElementById('cluster-probs');
    probsContainer.innerHTML = '';
    const probs = data.probabilities || [];
    probs.forEach((p, i) => {
      const pct = Math.round(p * 100);
      const div = document.createElement('div');
      div.className = 'bar-row';
      div.innerHTML = `
        <span class="bar-label" style="width:180px">Cụm ${i}</span>
        <div class="bar-track" style="flex:1">
          <div class="bar-fill positive-bar" style="width:0%;background:hsl(${(i*47+200)%360},60%,55%)"></div>
        </div>
        <span class="bar-pct">${pct}%</span>
      `;
      probsContainer.appendChild(div);
      setTimeout(() => {
        div.querySelector('.bar-fill').style.width = `${pct}%`;
      }, 50);
    });

    document.getElementById('cluster-result').classList.remove('hidden');
  } catch (e) {
    alert(`Lỗi: ${e.message}`);
  } finally {
    btn.disabled = false;
    btn.textContent = '🧩 Phân cụm';
    hideLoading();
  }
}

// ──────────────────────────────────────────────────────────
// ASSOCIATION RULES
// ──────────────────────────────────────────────────────────
async function loadRules() {
  const minLift = parseFloat(document.getElementById('filter-lift')?.value || 1.0);
  const minConf = parseFloat(document.getElementById('filter-conf')?.value || 0.5);
  const topK    = parseInt(document.getElementById('filter-topk')?.value || 20);

  showLoading();
  try {
    const data = await apiFetch(
      `/api/association-rules?top_k=${topK}&min_lift=${minLift}&min_confidence=${minConf}`
    );

    const tbody = document.getElementById('rules-tbody');
    tbody.innerHTML = '';

    if (!data.rules?.length) {
      tbody.innerHTML = '<tr><td colspan="6" class="empty-row">Không có luật nào với tiêu chí này</td></tr>';
      return;
    }

    data.rules.forEach((rule, idx) => {
      const lift = parseFloat(rule.lift).toFixed(3);
      const liftClass = lift >= 2 ? 'lift-high' : (lift >= 1.5 ? 'lift-mid' : 'lift-low');
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${idx + 1}</td>
        <td><code style="color:#a78bfa;font-size:0.82rem">${rule.antecedents_str}</code></td>
        <td><code style="color:#34d399;font-size:0.82rem">${rule.consequents_str}</code></td>
        <td>${(rule.support * 100).toFixed(2)}%</td>
        <td>${(rule.confidence * 100).toFixed(1)}%</td>
        <td><span class="lift-badge ${liftClass}">${lift}</span></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (e) {
    document.getElementById('rules-tbody').innerHTML =
      `<tr><td colspan="6" class="empty-row" style="color:#f87171">Lỗi: ${e.message}</td></tr>`;
  } finally {
    hideLoading();
  }
}

// ──────────────────────────────────────────────────────────
// RECOMMEND
// ──────────────────────────────────────────────────────────
const PRODUCT_EMOJIS = ['👕', '📱', '💄', '👟', '🎮', '📚', '🍜', '💻', '⌚', '🧴', '🎒', '🖥️'];

function quickSearch(query) {
  document.getElementById('recommend-input').value = query;
  searchRecommend();
}

async function searchRecommend() {
  const query = document.getElementById('recommend-input')?.value.trim();
  if (!query) { alert('Nhập từ khóa tìm kiếm!'); return; }
  const topK = parseInt(document.getElementById('topk-input')?.value || 10);

  showLoading();
  const grid = document.getElementById('products-grid');
  grid.innerHTML = '<div class="empty-state"><div class="spinner"></div></div>';

  try {
    const data = await apiFetch('/api/recommend', {
      method: 'POST',
      body: JSON.stringify({ query, top_k: topK }),
    });

    grid.innerHTML = '';
    if (!data.recommendations?.length) {
      grid.innerHTML = `<div class="empty-state"><div class="empty-icon">🔍</div><p>Không tìm thấy sản phẩm phù hợp</p></div>`;
      return;
    }

    data.recommendations.forEach((product, idx) => {
      const emoji = PRODUCT_EMOJIS[idx % PRODUCT_EMOJIS.length];
      const price = product.price ? `${Number(product.price).toLocaleString('vi')}đ` : 'Liên hệ';
      const score = product.similarity_score ? `Match: ${(product.similarity_score * 100).toFixed(0)}%` : '';
      const card = document.createElement('div');
      card.className = 'product-card';
      card.innerHTML = `
        <div class="product-rank">#${idx + 1}</div>
        <div class="product-emoji">${emoji}</div>
        <div class="product-name">${escapeHtml(product.name || 'Sản phẩm')}</div>
        <span class="product-category">${escapeHtml(product.category || 'Khác')}</span>
        <div class="product-meta">
          <span class="product-price">${price}</span>
          ${score ? `<span class="product-score">${score}</span>` : ''}
        </div>
      `;
      grid.appendChild(card);
    });
  } catch (e) {
    grid.innerHTML = `<div class="empty-state" style="color:#f87171"><div class="empty-icon">⚠️</div><p>Lỗi: ${escapeHtml(e.message)}</p></div>`;
  } finally {
    hideLoading();
  }
}
