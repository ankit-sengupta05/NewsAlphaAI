// src/pages/History.jsx
import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Clock, TrendingUp, TrendingDown, Minus, RefreshCw } from 'lucide-react'
import clsx from 'clsx'
import { api, fmt } from '../utils/api.js'

const WATCHED = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL', 'AMZN', 'META', 'AMD', 'BTC-USD']

export default function History() {
  const [all, setAll]       = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  const load = async () => {
    setLoading(true)
    const results = await Promise.allSettled(
      WATCHED.map(t => api.get(`/api/prediction/${t}/history`))
    )
    const flat = results
      .filter(r => r.status === 'fulfilled')
      .flatMap(r => (r.value.history || []).map(h => ({ ...h, ticker: r.value.ticker })))
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
    setAll(flat)
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  if (loading) return (
    <div className="flex items-center justify-center h-64 text-text-muted text-sm">
      <RefreshCw size={16} className="animate-spin mr-2" /> Loading history…
    </div>
  )

  return (
    <div className="p-5 space-y-5 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Clock size={16} className="text-text-muted" />
          <h1 className="text-lg font-mono font-semibold text-text-primary">Prediction History</h1>
          <span className="text-xs text-text-muted font-mono">({all.length} records)</span>
        </div>
        <button className="btn-ghost flex items-center gap-2 text-xs" onClick={load}>
          <RefreshCw size={12} /> Refresh
        </button>
      </div>

      {all.length === 0 ? (
        <div className="card p-12 text-center space-y-3">
          <div className="text-4xl">📭</div>
          <div className="text-sm text-text-secondary">No predictions yet.</div>
          <div className="text-xs text-text-muted">Run a prediction from any stock page to see history here.</div>
        </div>
      ) : (
        <div className="space-y-2">
          {all.map((p, i) => <HistoryRow key={i} p={p} onClick={() => navigate(`/stock/${p.ticker}`)} />)}
        </div>
      )}
    </div>
  )
}

function HistoryRow({ p, onClick }) {
  const isUp   = p.direction === 'UP'
  const isDown = p.direction === 'DOWN'

  return (
    <div
      onClick={onClick}
      className="card-hover p-4 flex items-center justify-between cursor-pointer animate-slide-up"
    >
      <div className="flex items-center gap-4">
        {/* Direction icon */}
        <div className={clsx(
          'w-9 h-9 rounded-lg flex items-center justify-center border',
          isUp   ? 'bg-accent-green/10 border-accent-green/20' :
          isDown ? 'bg-accent-red/10   border-accent-red/20'   :
                   'bg-bg-hover        border-bg-border'
        )}>
          {isUp   ? <TrendingUp  size={16} className="text-accent-green" /> :
           isDown ? <TrendingDown size={16} className="text-accent-red" />  :
                    <Minus        size={16} className="text-text-muted"  />}
        </div>

        {/* Ticker + summary */}
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono font-semibold text-text-primary">{p.ticker}</span>
            <span className={clsx(
              'text-xs font-mono font-bold',
              isUp ? 'text-accent-green' : isDown ? 'text-accent-red' : 'text-text-muted'
            )}>
              {p.direction}
            </span>
            <ConfidenceDot confidence={p.confidence} />
          </div>
          {p.summary && (
            <div className="text-xs text-text-muted mt-0.5 max-w-lg truncate">{p.summary}</div>
          )}
        </div>
      </div>

      <div className="flex items-center gap-6 text-right flex-shrink-0">
        {/* Probability */}
        <div>
          <div className="stat-label">PROBABILITY</div>
          <div className={clsx('font-mono font-semibold text-sm',
            isUp ? 'text-accent-green' : 'text-accent-red'
          )}>
            {p.probability != null ? `${Math.round(p.probability * 100)}%` : '—'}
          </div>
        </div>

        {/* Price */}
        {p.price != null && (
          <div>
            <div className="stat-label">PRICE</div>
            <div className="font-mono text-sm text-text-primary">{fmt.price(p.price)}</div>
          </div>
        )}

        {/* Sentiment */}
        {p.sentiment && (
          <div>
            <div className="stat-label">SENTIMENT</div>
            <div className={clsx('font-mono text-xs font-semibold',
              p.sentiment === 'BULLISH' ? 'text-accent-green' :
              p.sentiment === 'BEARISH' ? 'text-accent-red'   : 'text-text-muted'
            )}>
              {p.sentiment}
            </div>
          </div>
        )}

        {/* Timestamp */}
        <div className="text-[10px] text-text-muted font-mono">{fmt.date(p.timestamp)}</div>
      </div>
    </div>
  )
}

function ConfidenceDot({ confidence }) {
  const map = {
    HIGH:   'bg-accent-green',
    MEDIUM: 'bg-accent-gold',
    LOW:    'bg-text-muted',
  }
  return (
    <span title={`Confidence: ${confidence}`}
      className={`inline-block w-2 h-2 rounded-full ${map[confidence] || map.LOW}`} />
  )
}
