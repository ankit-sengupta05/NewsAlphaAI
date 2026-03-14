// src/components/PredictionCard.jsx
import React from 'react'
import clsx from 'clsx'
import { TrendingUp, TrendingDown, Minus, AlertCircle, Brain, BarChart2 } from 'lucide-react'
import { fmt } from '../utils/api.js'

export default function PredictionCard({ prediction }) {
  if (!prediction) return null

  const { direction, probability, confidence, llm_direction, llm_probability,
          ml_direction, ml_probability, sentiment, sentiment_score,
          reasoning_bullets, summary, price, rsi, macd, ticker, timestamp } = prediction

  const isUp   = direction === 'UP'
  const isDown = direction === 'DOWN'

  const dirColor = isUp ? 'text-accent-green' : isDown ? 'text-accent-red' : 'text-text-secondary'
  const dirBg    = isUp ? 'bg-accent-green/10 border-accent-green/30' : isDown ? 'bg-accent-red/10 border-accent-red/30' : 'bg-bg-hover border-bg-border'
  const dirGlow  = isUp ? 'shadow-[0_0_32px_rgba(0,230,118,0.15)]' : isDown ? 'shadow-[0_0_32px_rgba(255,61,87,0.15)]' : ''
  const pct      = Math.round((probability ?? 0) * 100)

  return (
    <div className={clsx('card p-5 space-y-5 animate-fade-in', dirGlow)}>
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="stat-label mb-1">AI PREDICTION · 2–3 DAYS</div>
          <div className={clsx('text-3xl font-mono font-bold flex items-center gap-2', dirColor)}>
            {isUp && <TrendingUp size={28} />}
            {isDown && <TrendingDown size={28} />}
            {!isUp && !isDown && <Minus size={28} />}
            {direction}
          </div>
        </div>

        {/* Confidence ring */}
        <ConfidenceRing pct={pct} isUp={isUp} isDown={isDown} confidence={confidence} />
      </div>

      {/* Summary */}
      {summary && (
        <p className="text-sm text-text-secondary leading-relaxed border-l-2 border-accent-blue/40 pl-3 italic">
          {summary}
        </p>
      )}

      {/* Model breakdown */}
      <div className="grid grid-cols-2 gap-3">
        <ModelBadge
          icon={<Brain size={13} />}
          label="LLM"
          direction={llm_direction}
          probability={llm_probability}
        />
        <ModelBadge
          icon={<BarChart2 size={13} />}
          label="ML Model"
          direction={ml_direction}
          probability={ml_probability}
        />
      </div>

      {/* Sentiment + technicals */}
      <div className="grid grid-cols-3 gap-3">
        <StatBox label="Sentiment" value={sentiment}
          color={sentiment === 'BULLISH' ? 'text-accent-green' : sentiment === 'BEARISH' ? 'text-accent-red' : 'text-text-secondary'} />
        <StatBox label="RSI" value={fmt.num(rsi, 1)}
          color={rsi > 70 ? 'text-accent-red' : rsi < 30 ? 'text-accent-green' : 'text-text-primary'} />
        <StatBox label="MACD" value={fmt.num(macd, 3)}
          color={macd > 0 ? 'text-accent-green' : 'text-accent-red'} />
      </div>

      {/* Reasoning bullets */}
      {reasoning_bullets?.length > 0 && (
        <div className="bg-bg-secondary rounded-lg p-3 space-y-2">
          <div className="stat-label mb-2">AI REASONING</div>
          {reasoning_bullets.slice(0, 5).map((b, i) => (
            <div key={i} className="flex items-start gap-2 text-xs text-text-secondary">
              <span className="text-accent-blue mt-0.5 flex-shrink-0">▸</span>
              <span>{b}</span>
            </div>
          ))}
        </div>
      )}

      {/* Confidence badge + timestamp */}
      <div className="flex items-center justify-between pt-1">
        <ConfidenceBadge confidence={confidence} />
        <span className="text-[10px] text-text-muted font-mono">{fmt.date(timestamp)}</span>
      </div>
    </div>
  )
}

// ── Sub-components ──────────────────────────────────────────────

function ConfidenceRing({ pct, isUp, isDown, confidence }) {
  const r = 40
  const circ = 2 * Math.PI * r
  const offset = circ - (pct / 100) * circ
  const color = isUp ? '#00e676' : isDown ? '#ff3d57' : '#8892a4'

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width="96" height="96" viewBox="0 0 96 96">
        <circle cx="48" cy="48" r={r} fill="none" stroke="#1e2535" strokeWidth="6" />
        <circle
          cx="48" cy="48" r={r}
          fill="none" stroke={color} strokeWidth="6"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 48 48)"
          style={{ transition: 'stroke-dashoffset 1s cubic-bezier(0.4,0,0.2,1)' }}
        />
        <text x="48" y="44" textAnchor="middle" fill={color} fontSize="18" fontFamily="JetBrains Mono" fontWeight="600">
          {pct}%
        </text>
        <text x="48" y="58" textAnchor="middle" fill="#4a5568" fontSize="9" fontFamily="JetBrains Mono">
          PROB
        </text>
      </svg>
    </div>
  )
}

function ModelBadge({ icon, label, direction, probability }) {
  const isUp = direction === 'UP'
  const isDown = direction === 'DOWN'
  return (
    <div className="bg-bg-secondary border border-bg-border rounded-lg p-2.5">
      <div className="flex items-center gap-1.5 mb-1.5 text-text-muted">
        {icon}
        <span className="text-[10px] font-mono uppercase">{label}</span>
      </div>
      <div className={clsx(
        'text-sm font-mono font-semibold',
        isUp ? 'text-accent-green' : isDown ? 'text-accent-red' : 'text-text-secondary'
      )}>
        {direction ?? '—'}
      </div>
      <div className="text-[10px] text-text-muted font-mono">
        {probability != null ? `${Math.round(probability * 100)}%` : '—'}
      </div>
    </div>
  )
}

function StatBox({ label, value, color }) {
  return (
    <div className="bg-bg-secondary border border-bg-border rounded-lg p-2.5 text-center">
      <div className="stat-label mb-1">{label}</div>
      <div className={clsx('text-sm font-mono font-semibold', color)}>{value}</div>
    </div>
  )
}

function ConfidenceBadge({ confidence }) {
  const map = {
    HIGH:   'text-accent-green border-accent-green/30 bg-accent-green/10',
    MEDIUM: 'text-accent-gold  border-accent-gold/30  bg-accent-gold/10',
    LOW:    'text-text-muted   border-text-muted/30   bg-bg-hover',
  }
  return (
    <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${map[confidence] || map.LOW}`}>
      {confidence ?? '—'} CONFIDENCE
    </span>
  )
}
