// src/components/Layout.jsx
import React, { useState } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, TrendingUp, Clock, Settings,
  BrainCircuit, Zap, Search, X
} from 'lucide-react'
import TickerTape from './TickerTape.jsx'
import clsx from 'clsx'

const NAV = [
  { to: '/',         icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/history',  icon: Clock,           label: 'History'   },
]

const WATCHLIST = ['AAPL','TSLA','NVDA','MSFT','GOOGL','AMZN','META','BTC-USD']

export default function Layout() {
  const [search, setSearch] = useState('')
  const [showSearch, setShowSearch] = useState(false)
  const navigate = useNavigate()

  const filtered = WATCHLIST.filter(t =>
    t.toLowerCase().includes(search.toLowerCase())
  )

  const go = (ticker) => {
    navigate(`/stock/${ticker}`)
    setSearch('')
    setShowSearch(false)
  }

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-bg-primary">
      {/* ── Ticker Tape ─────────────────────────────────────── */}
      <TickerTape tickers={WATCHLIST} />

      <div className="flex flex-1 overflow-hidden">
        {/* ── Sidebar ────────────────────────────────────────── */}
        <aside className="w-56 flex-shrink-0 bg-bg-secondary border-r border-bg-border flex flex-col">
          {/* Logo */}
          <div className="px-5 py-5 border-b border-bg-border">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-accent-blue/20 border border-accent-blue/30 flex items-center justify-center">
                <BrainCircuit size={16} className="text-accent-blue" />
              </div>
              <div>
                <div className="text-sm font-mono font-semibold text-text-primary">NewsAlpha</div>
                <div className="text-[10px] text-accent-blue font-mono tracking-wider">AI EDITION</div>
              </div>
            </div>
          </div>

          {/* Nav */}
          <nav className="px-3 py-4 flex flex-col gap-1">
            {NAV.map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to} to={to} end={to === '/'}
                className={({ isActive }) => clsx(
                  'flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all duration-150',
                  isActive
                    ? 'bg-accent-blue/10 text-accent-blue border border-accent-blue/20'
                    : 'text-text-secondary hover:text-text-primary hover:bg-bg-hover'
                )}
              >
                <Icon size={15} />
                {label}
              </NavLink>
            ))}
          </nav>

          {/* Watchlist */}
          <div className="px-3 py-3 border-t border-bg-border flex-1 overflow-y-auto">
            <div className="flex items-center justify-between mb-2 px-2">
              <span className="stat-label">Watchlist</span>
              <button
                onClick={() => setShowSearch(v => !v)}
                className="text-text-muted hover:text-accent-blue transition-colors"
              >
                {showSearch ? <X size={13} /> : <Search size={13} />}
              </button>
            </div>

            {showSearch && (
              <input
                className="input-field mb-2 text-xs py-1.5"
                placeholder="Search ticker…"
                value={search}
                onChange={e => setSearch(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && filtered[0] && go(filtered[0])}
                autoFocus
              />
            )}

            <div className="flex flex-col gap-0.5">
              {(search ? filtered : WATCHLIST).map(ticker => (
                <WatchlistRow key={ticker} ticker={ticker} onClick={() => go(ticker)} />
              ))}
            </div>
          </div>

          {/* Bottom */}
          <div className="px-4 py-3 border-t border-bg-border">
            <div className="flex items-center gap-2 text-[10px] text-text-muted font-mono">
              <Zap size={10} className="text-accent-green animate-pulse-green" />
              AI PIPELINE READY
            </div>
          </div>
        </aside>

        {/* ── Main ────────────────────────────────────────────── */}
        <main className="flex-1 overflow-y-auto bg-bg-primary">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

// ── Mini watchlist row ─────────────────────────────────────────
function WatchlistRow({ ticker, onClick }) {
  const { price, changePct, flash } = useLivePriceInline(ticker)
  const isUp = changePct >= 0

  return (
    <button
      onClick={onClick}
      className={clsx(
        'w-full flex items-center justify-between px-2 py-1.5 rounded-md',
        'text-xs hover:bg-bg-hover transition-all duration-150 group',
        flash === 'up'   && 'bg-accent-green/5',
        flash === 'down' && 'bg-accent-red/5',
      )}
    >
      <span className="font-mono text-text-secondary group-hover:text-text-primary transition-colors">
        {ticker}
      </span>
      <div className="text-right">
        {price != null ? (
          <>
            <div className={clsx('font-mono font-medium', isUp ? 'text-accent-green' : 'text-accent-red')}>
              ${price.toFixed(2)}
            </div>
            <div className={clsx('text-[10px] font-mono', isUp ? 'text-accent-green/70' : 'text-accent-red/70')}>
              {isUp ? '+' : ''}{changePct?.toFixed(2)}%
            </div>
          </>
        ) : (
          <span className="text-text-muted font-mono">—</span>
        )}
      </div>
    </button>
  )
}

// Inline hook to avoid circular imports
function useLivePriceInline(ticker) {
  const [price, setPrice]       = React.useState(null)
  const [changePct, setChangePct] = React.useState(0)
  const [flash, setFlash]       = React.useState(null)
  const prevRef = React.useRef(null)
  const wsRef   = React.useRef(null)

  React.useEffect(() => {
    const WS_BASE = (import.meta.env.VITE_API_BASE || 'http://localhost:8000').replace(/^http/, 'ws')
    const ws = new WebSocket(`${WS_BASE}/ws/live/${ticker}`)
    wsRef.current = ws
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data)
      if (msg.type !== 'price') return
      const p = msg.price
      if (prevRef.current != null) {
        const dir = p > prevRef.current ? 'up' : p < prevRef.current ? 'down' : null
        if (dir) { setFlash(dir); setTimeout(() => setFlash(null), 700) }
      }
      prevRef.current = p
      setPrice(p)
      setChangePct(msg.change_pct ?? 0)
    }
    return () => ws.close()
  }, [ticker])

  return { price, changePct, flash }
}
