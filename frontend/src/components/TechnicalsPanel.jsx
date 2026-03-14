// src/components/TechnicalsPanel.jsx
import React from 'react'
import clsx from 'clsx'
import { fmt } from '../utils/api.js'

const INDICATOR_DEFS = [
  {
    key: 'rsi',
    label: 'RSI (14)',
    format: v => fmt.num(v, 1),
    signal: v => v > 70 ? { text: 'OVERBOUGHT', color: 'text-accent-red' }
               : v < 30 ? { text: 'OVERSOLD',   color: 'text-accent-green' }
               :           { text: 'NEUTRAL',    color: 'text-text-muted' },
  },
  {
    key: 'macd',
    label: 'MACD',
    format: v => fmt.num(v, 4),
    signal: v => v > 0 ? { text: 'BULLISH', color: 'text-accent-green' }
               :          { text: 'BEARISH', color: 'text-accent-red' },
  },
  {
    key: 'macd_hist',
    label: 'MACD Hist',
    format: v => fmt.num(v, 4),
    signal: v => v > 0 ? { text: '▲ RISING', color: 'text-accent-green' }
               :          { text: '▼ FALLING', color: 'text-accent-red' },
  },
  {
    key: 'bb_pct',
    label: 'BB %',
    format: v => `${fmt.num(v * 100, 1)}%`,
    signal: v => v > 0.8 ? { text: 'NEAR UPPER', color: 'text-accent-red' }
               : v < 0.2 ? { text: 'NEAR LOWER', color: 'text-accent-green' }
               :             { text: 'MID BAND',   color: 'text-text-muted' },
  },
  {
    key: 'vol_ratio',
    label: 'Vol Ratio',
    format: v => fmt.num(v, 2) + 'x',
    signal: v => v > 1.5 ? { text: 'HIGH VOL', color: 'text-accent-gold' }
               : v < 0.7 ? { text: 'LOW VOL',  color: 'text-text-muted' }
               :             { text: 'NORMAL',   color: 'text-text-muted' },
  },
  {
    key: 'sma_crossover',
    label: 'SMA Cross',
    format: v => v ? 'GOLDEN' : 'DEATH',
    signal: v => v ? { text: 'BULLISH', color: 'text-accent-green' }
               :      { text: 'BEARISH', color: 'text-accent-red' },
  },
  {
    key: 'change_1d_pct',
    label: '1D Change',
    format: v => fmt.pct(v),
    signal: v => v > 0 ? { text: 'UP', color: 'text-accent-green' }
               : v < 0 ? { text: 'DOWN', color: 'text-accent-red' }
               :          { text: 'FLAT', color: 'text-text-muted' },
  },
  {
    key: 'change_5d_pct',
    label: '5D Change',
    format: v => fmt.pct(v),
    signal: v => v > 0 ? { text: 'UP', color: 'text-accent-green' }
               : v < 0 ? { text: 'DOWN', color: 'text-accent-red' }
               :          { text: 'FLAT', color: 'text-text-muted' },
  },
]

export default function TechnicalsPanel({ technicals }) {
  if (!technicals || technicals.error) {
    return (
      <div className="card p-5">
        <div className="stat-label mb-3">TECHNICAL INDICATORS</div>
        <p className="text-xs text-text-muted">No data available.</p>
      </div>
    )
  }

  const bullCount = INDICATOR_DEFS.filter(d => {
    const sig = d.signal(technicals[d.key] ?? 0)
    return sig.color === 'text-accent-green'
  }).length
  const bearCount = INDICATOR_DEFS.filter(d => {
    const sig = d.signal(technicals[d.key] ?? 0)
    return sig.color === 'text-accent-red'
  }).length

  return (
    <div className="card p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div className="stat-label">TECHNICAL INDICATORS</div>
        <div className="flex gap-2 text-[10px] font-mono">
          <span className="text-accent-green">{bullCount} BUY</span>
          <span className="text-text-muted">/</span>
          <span className="text-accent-red">{bearCount} SELL</span>
        </div>
      </div>

      {/* Price row */}
      <div className="flex items-baseline gap-2 border-b border-bg-border pb-3">
        <span className="text-2xl font-mono font-bold text-text-primary">
          {fmt.price(technicals.price)}
        </span>
        <span className={clsx(
          'text-sm font-mono',
          technicals.change_1d_pct > 0 ? 'text-accent-green' : 'text-accent-red'
        )}>
          {fmt.pct(technicals.change_1d_pct)}
        </span>
      </div>

      {/* Indicator grid */}
      <div className="grid grid-cols-2 gap-2">
        {INDICATOR_DEFS.map(({ key, label, format, signal }) => {
          const val = technicals[key]
          const sig = signal(val ?? 0)
          return (
            <div key={key} className="bg-bg-secondary rounded-lg p-2.5 flex items-center justify-between">
              <div>
                <div className="text-[9px] font-mono text-text-muted uppercase">{label}</div>
                <div className="text-sm font-mono text-text-primary mt-0.5">
                  {val != null ? format(val) : '—'}
                </div>
              </div>
              <span className={clsx('text-[9px] font-mono font-semibold', sig.color)}>
                {sig.text}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
