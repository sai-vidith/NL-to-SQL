// General utility functions for dates, numbers, toasts, SQL highlighting, copy-to-clipboard

export function formatDate(dateStr) {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}

export function formatNumber(num) {
  if (num === null || num === undefined) return '-';
  if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B';
  if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M';
  if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K';
  return num.toLocaleString();
}

export function formatDuration(ms) {
  if (ms < 1000) return `${ms.toFixed(0)}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

export function showToast(message, type = 'success') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast animate-slide-up`;
  
  const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';
  toast.innerHTML = `
    <div style="font-size: 1.25rem;">${icon}</div>
    <div style="flex: 1; font-size: 13px;">${escapeHtml(message)}</div>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

export function escapeHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

export function highlightSQL(sql) {
  if (!sql) return '';
  const keywords = [
    'SELECT', 'FROM', 'JOIN', 'USING', 'ON', 'WHERE', 'GROUP BY', 'ORDER BY', 
    'LIMIT', 'AND', 'OR', 'SUM', 'COUNT', 'AVG', 'MIN', 'MAX', 'LEFT', 'RIGHT',
    'INNER', 'FULL', 'OUTER', 'AS', 'IN', 'IS', 'NULL', 'LIKE', 'ILIKE', 'DESC', 'ASC'
  ];
  
  let escaped = escapeHtml(sql);
  
  keywords.forEach(keyword => {
    const regex = new RegExp(`\\b${keyword}\\b`, 'gi');
    escaped = escaped.replace(regex, `<span style="color: var(--accent-cyan); font-weight: 600;">$&</span>`);
  });

  return escaped;
}

export function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(
    () => showToast('Copied to clipboard!'),
    () => showToast('Failed to copy', 'error')
  );
}

export function createSkeletonLoader(count = 3, type = 'card') {
  let skeletons = '';
  for (let i = 0; i < count; i++) {
    if (type === 'card') {
      skeletons += `
        <div class="card skeleton skeleton-card"></div>
      `;
    } else {
      skeletons += `
        <div class="skeleton skeleton-text" style="width: ${80 + Math.random() * 20}%;"></div>
        <div class="skeleton skeleton-text" style="width: ${60 + Math.random() * 30}%;"></div>
        <br/>
      `;
    }
  }
  return skeletons;
}
