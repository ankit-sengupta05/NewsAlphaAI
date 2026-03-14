// src/components/SentimentGauge.jsx
import React from 'react'
import clsx from 'clsx'

export default function SentimentGauge({ sentiment }) {
  if (!sentiment) return null
  const {
    overall_sentiment, sentiment_score, confidence,
    dominant_themes, risk_factors, catalysts, summary,
  } = sentiment

  const score  = parseFloat(sentiment_score ?? 0)
  const pct    = Math.round(((score + 1) / 2) * 100)   // map -1..1 → 0..100
  const isBull = overall_sentiment === 'BULLISH'
  const isBear = overall_sentiment === 'BEARISH'

  return (
    <div className="card p-5 space-y-4">
      <div className="stat-label">NEWS SENTIMENT</div>

      {/* Gauge bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-[10px] font-mono text-text-muted">
          <span>BEARISH</span>
          <span className={clsx(
            'font-semibold text-xs',
            isBull ? 'text-accent-green' : isBear ? 'text-accent-red' : 'text-text-secondary'
          )}>
            {overall_sentiment}
          </span>
          <span>BULLISH</span>
        </div>
        <div className="relative h-3 bg-bg-secondary rounded-full overflow-hidden border border-bg-border">
          {/* Gradient track */}
          <div className="absolute inset-0 bg-gradient-to-r from-accent-red/40 via-text-muted/20 to-accent-green/40 rounded-full" />
          {/* Marker */}
          <div
            className={clsx(
              'absolute top-0.5 h-2 w-2 rounded-full border-2 transition-all duration-700',
              isBull ? 'bg-accent-green border-accent-green/70' :
              isBear ? 'bg-accent-red border-accent-red/70' :
                       'bg-text-secondary border-text-muted'
            )}
            style={{ left: `calc(${pct}% - 4px)` }}
          />
        </div>
        <div className="text-center text-xs font-mono text-text-muted">
          Score: <span className={clsx(
            'font-semibold',
            score > 0.1 ? 'text-accent-green' : score < -0.1 ? 'text-accent-red' : 'text-text-secondary'
          )}>{score > 0 ? '+' : ''}{score.toFixed(3)}</span>
          <span className="ml-3">Confidence: <span className="text-text-primary">{Math.round((confidence ?? 0) * 100)}%</span></span>
        </div>
      </div>

      {/* Summary */}
      {summary && (
        <p className="text-xs text-text-secondary leading-relaxed">{summary}</p>
      )}

      {/* Tags */}
      <div className="space-y-2">
        {dominant_themes?.length > 0 && (
          <TagRow label="Themes" tags={dominant_themes} color="accent-blue" />
        )}
        {catalysts?.length > 0 && (
          <TagRow label="Catalysts" tags={catalysts} color="accent-green" />
        )}
        {risk_factors?.length > 0 && (
          <TagRow label="Risks" tags={risk_factors} color="accent-red" />
        )}
      </div>
    </div>
  )
}

function TagRow({ label, tags, color }) {
  return (
    <div className="flex items-start gap-2">
      <span className="text-[9px] font-mono text-text-muted uppercase w-14 flex-shrink-0 pt-0.5">{label}</span>
      <div className="flex flex-wrap gap-1">
        {tags.map((t, i) => (
          <span key={i} className={`text-[10px] font-mono px-1.5 py-0.5 rounded bg-${color}/10 text-${color} border border-${color}/20`}>
            {t}
          </span>
        ))}
      </div>
    </div>
  )
}
