// src/components/PipelineProgress.jsx
import React from 'react'
import clsx from 'clsx'
import { CheckCircle2, Loader2 } from 'lucide-react'

const STEP_ICONS = {
  fetch_news:        '📰',
  analyse_sentiment: '🧠',
  embed_store:       '🔢',
  fetch_stock:       '📈',
  rag_retrieve:      '🔍',
  llm_reason:        '💡',
  ml_predict:        '⚙️',
  final_predict:     '✅',
}

const STEP_LABELS = {
  fetch_news:        'Fetch News',
  analyse_sentiment: 'Sentiment LLM',
  embed_store:       'Vector Embed',
  fetch_stock:       'Stock Data',
  rag_retrieve:      'RAG Retrieval',
  llm_reason:        'LLM Reasoning',
  ml_predict:        'ML Predict',
  final_predict:     'Ensemble',
}

export default function PipelineProgress({
  steps,
  currentStep,
  completedSteps,
  logs,
  status,
  progress,
  completedCount,
  totalSteps,
}) {
  return (
    <div className="card p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text-primary font-mono tracking-wide">
          AI PIPELINE
        </h3>
        <PipelineStatusBadge status={status} />
      </div>

      {/* Step grid */}
      <div className="grid grid-cols-4 gap-2">
        {steps.map((step) => {
          // isDone: in completedSteps but NOT currently active
          const isDone    = completedSteps.includes(step) && step !== currentStep
          const isActive  = step === currentStep
          const isPending = !isDone && !isActive

          return (
            <div
              key={step}
              className={clsx(
                'relative flex flex-col items-center gap-1.5 p-2.5 rounded-lg border transition-all duration-300',
                isDone    && 'bg-accent-green/5 border-accent-green/20',
                isActive  && 'bg-accent-blue/10 border-accent-blue/30',
                isPending && 'bg-bg-secondary border-bg-border opacity-40',
              )}
            >
              {/* Icon */}
              <div className="text-lg leading-none">
                {isActive ? (
                  <Loader2 size={18} className="text-accent-blue animate-spin" />
                ) : isDone ? (
                  <CheckCircle2 size={18} className="text-accent-green" />
                ) : (
                  <span className="text-base opacity-50">
                    {STEP_ICONS[step]}
                  </span>
                )}
              </div>

              {/* Label */}
              <span className={clsx(
                'text-[9px] font-mono text-center leading-tight',
                isDone    && 'text-accent-green',
                isActive  && 'text-accent-blue',
                isPending && 'text-text-muted',
              )}>
                {STEP_LABELS[step]}
              </span>

              {/* Active pulse ring */}
              {isActive && (
                <div className="absolute inset-0 rounded-lg border border-accent-blue/50 animate-ping opacity-30" />
              )}
            </div>
          )
        })}
      </div>

      {/* Progress bar */}
      <div className="h-1 bg-bg-secondary rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-accent-blue to-accent-cyan rounded-full transition-all duration-700 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Step counter + current step label */}
      <div className="flex justify-between text-[9px] font-mono text-text-muted">
        <span>{completedCount ?? completedSteps.length} / {totalSteps ?? steps.length} steps complete</span>
        {currentStep && (
          <span className="text-accent-blue animate-pulse">
            {STEP_LABELS[currentStep]}...
          </span>
        )}
      </div>

      {/* Live log */}
      {logs.length > 0 && (
        <div className="bg-bg-secondary rounded-lg p-3 max-h-28 overflow-y-auto font-mono text-[10px] space-y-1">
          {logs.slice(-8).map((log, i, arr) => (
            <div
              key={i}
              className={clsx(
                'leading-relaxed',
                i === arr.length - 1 ? 'text-accent-blue' : 'text-text-secondary',
              )}
            >
              <span className="text-text-muted mr-2">&gt;</span>{log}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function PipelineStatusBadge({ status }) {
  const map = {
    idle:       { label: 'IDLE',       cls: 'text-text-muted bg-bg-secondary border-bg-border' },
    connecting: { label: 'CONNECTING', cls: 'text-accent-gold bg-accent-gold/10 border-accent-gold/20' },
    running:    { label: 'RUNNING',    cls: 'text-accent-blue bg-accent-blue/10 border-accent-blue/20' },
    complete:   { label: 'COMPLETE',   cls: 'text-accent-green bg-accent-green/10 border-accent-green/20' },
    error:      { label: 'ERROR',      cls: 'text-accent-red bg-accent-red/10 border-accent-red/20' },
  }
  const { label, cls } = map[status] || map.idle
  return (
    <span className={`text-[9px] font-mono px-2 py-0.5 rounded-full border ${cls}`}>
      {label}
    </span>
  )
}
