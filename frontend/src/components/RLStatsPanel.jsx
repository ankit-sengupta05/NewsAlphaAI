// src/components/RLStatsPanel.jsx
import React from 'react'
import clsx from 'clsx'
import { Target, TrendingUp, RefreshCw } from 'lucide-react'

export default function RLStatsPanel({ stats }) {
  if (!stats) return null
  const { accuracy, total, correct, recent_rewards } = stats

  const accPct = accuracy != null ? Math.round(accuracy * 100) : null
  const recentCorrect = recent_rewards?.filter(r => r === 1.0).length ?? 0
  const recentTotal   = recent_rewards?.filter(r => r !== 0).length ?? 0

  return (
    <div className="card p-5 space-y-4">
      <div className="flex items-center gap-2">
        <Target size={14} className="text-accent-purple" />
        <div className="stat-label">RL MODEL ACCURACY</div>
      </div>

      {total === 0 ? (
        <div className="text-xs text-text-muted">
          Insufficient prediction history. Accuracy improves after 3+ days of predictions.
        </div>
      ) : (
        <>
          <div className="grid grid-cols-3 gap-3">
            <Stat label="Accuracy" value={accPct != null ? `${accPct}%` : '—'}
              color={accPct >= 60 ? 'text-accent-green' : accPct >= 45 ? 'text-accent-gold' : 'text-accent-red'} />
            <Stat label="Correct"  value={correct ?? '—'} color="text-accent-green" />
            <Stat label="Total"    value={total   ?? '—'} color="text-text-primary" />
          </div>

          {/* Recent rewards strip */}
          {recent_rewards?.length > 0 && (
            <div className="space-y-1.5">
              <div className="stat-label">RECENT (LAST 10)</div>
              <div className="flex gap-1">
                {recent_rewards.map((r, i) => (
                  <div key={i} className={clsx(
                    'flex-1 h-5 rounded-sm flex items-center justify-center text-[9px] font-mono',
                    r === 1.0  ? 'bg-accent-green/20 text-accent-green' :
                    r === -1.0 ? 'bg-accent-red/20   text-accent-red'   :
                                 'bg-bg-secondary     text-text-muted',
                  )}>
                    {r === 1.0 ? '✓' : r === -1.0 ? '✗' : '·'}
                  </div>
                ))}
              </div>
              <div className="text-[10px] text-text-muted font-mono">
                Recent: {recentCorrect}/{recentTotal}
              </div>
            </div>
          )}
        </>
      )}

      <div className="flex items-center gap-1.5 text-[10px] text-text-muted font-mono">
        <RefreshCw size={10} />
        Model retrains automatically after 20+ labelled outcomes
      </div>
    </div>
  )
}

function Stat({ label, value, color }) {
  return (
    <div className="bg-bg-secondary border border-bg-border rounded-lg p-2.5 text-center">
      <div className="stat-label mb-1">{label}</div>
      <div className={clsx('text-lg font-mono font-semibold', color)}>{value}</div>
    </div>
  )
}
