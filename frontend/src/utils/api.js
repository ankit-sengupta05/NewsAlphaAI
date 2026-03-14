// src/utils/api.js
const BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const WS_BASE = BASE.replace(/^http/, 'ws')

export const api = {
  get: (path) => fetch(`${BASE}${path}`).then(r => r.json()),
  post: (path, body) => fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }).then(r => r.json()),
}

export const wsUrl = (path) => `${WS_BASE}${path}`

// ── Helpers ────────────────────────────────────────────────────
export const fmt = {
  price: (v) => v != null ? `$${Number(v).toFixed(2)}` : '—',
  pct:   (v) => v != null ? `${v > 0 ? '+' : ''}${Number(v).toFixed(2)}%` : '—',
  num:   (v, d = 2) => v != null ? Number(v).toFixed(d) : '—',
  k:     (v) => {
    if (v == null) return '—'
    if (Math.abs(v) >= 1e12) return `$${(v / 1e12).toFixed(2)}T`
    if (Math.abs(v) >= 1e9)  return `$${(v / 1e9).toFixed(2)}B`
    if (Math.abs(v) >= 1e6)  return `$${(v / 1e6).toFixed(2)}M`
    return `$${v.toLocaleString()}`
  },
  date: (iso) => {
    if (!iso) return '—'
    const d = new Date(iso)
    return d.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  },
}
