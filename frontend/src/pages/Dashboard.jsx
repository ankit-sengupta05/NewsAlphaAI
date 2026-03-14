// src/pages/Dashboard.jsx
import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, TrendingUp, Zap, BrainCircuit, Database, RefreshCw } from 'lucide-react'
import clsx from 'clsx'

const POPULAR = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL', 'AMZN', 'META', 'AMD']

export default function Dashboard() {
  const [ticker, setTicker] = useState('')
  const navigate = useNavigate()

  const go = (t) => {
    if (t.trim()) navigate(`/stock/${t.trim().toUpperCase()}`)
  }

  return (
    <div className="min-h-full bg-bg-primary bg-grid-pattern bg-grid">
      {/* Hero */}
      <div className="max-w-4xl mx-auto px-6 pt-20 pb-12">
        {/* Headline */}
        <div className="text-center space-y-4 mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent-blue/10 border border-accent-blue/20 text-accent-blue text-xs font-mono mb-4">
            <Zap size={11} className="animate-pulse" />
            POWERED BY GEMMA LLM + LANGGRAPH + RAG
          </div>

          <h1 className="text-5xl font-mono font-bold tracking-tight">
            <span className="text-text-primary">News</span>
            <span className="text-accent-blue">Alpha</span>
            <span className="text-text-secondary">AI</span>
          </h1>

          <p className="text-base text-text-muted max-w-2xl mx-auto leading-relaxed">
            AI-powered stock direction prediction using real-time news sentiment,
            LLM reasoning, vector RAG, and reinforcement learning feedback loops.
          </p>
        </div>

        {/* Search */}
        <div className="relative max-w-lg mx-auto">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-text-muted" />
              <input
                className="input-field pl-10 py-3 text-base"
                placeholder="Enter stock ticker (e.g. AAPL, TSLA)…"
                value={ticker}
                onChange={e => setTicker(e.target.value.toUpperCase())}
                onKeyDown={e => e.key === 'Enter' && go(ticker)}
              />
            </div>
            <button
              className="btn-primary px-6 py-3 text-base"
              onClick={() => go(ticker)}
            >
              Predict
            </button>
          </div>
        </div>

        {/* Popular chips */}
        <div className="flex flex-wrap gap-2 justify-center mt-5">
          {POPULAR.map(t => (
            <button
              key={t}
              onClick={() => go(t)}
              className="px-3 py-1 rounded-lg bg-bg-card border border-bg-border text-xs font-mono text-text-secondary
                         hover:text-accent-blue hover:border-accent-blue/30 transition-all duration-150"
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Feature grid */}
      <div className="max-w-4xl mx-auto px-6 pb-16">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {FEATURES.map(({ icon: Icon, title, desc, color }) => (
            <div key={title} className="card-hover p-4 space-y-2 text-center">
              <div className={`w-10 h-10 rounded-lg bg-${color}/10 border border-${color}/20 flex items-center justify-center mx-auto`}>
                <Icon size={18} className={`text-${color}`} />
              </div>
              <div className="text-sm font-semibold text-text-primary">{title}</div>
              <div className="text-[11px] text-text-muted leading-relaxed">{desc}</div>
            </div>
          ))}
        </div>

        {/* Pipeline diagram */}
        <div className="mt-8 card p-6">
          <div className="stat-label mb-4 text-center">AI PIPELINE FLOW</div>
          <div className="flex items-center justify-between gap-1 overflow-x-auto">
            {PIPELINE_STEPS.map((step, i) => (
              <React.Fragment key={step.label}>
                <div className="flex flex-col items-center gap-1 flex-shrink-0">
                  <div className={`w-9 h-9 rounded-lg bg-${step.color}/10 border border-${step.color}/20 flex items-center justify-center text-base`}>
                    {step.icon}
                  </div>
                  <span className="text-[9px] font-mono text-text-muted text-center w-16 leading-tight">{step.label}</span>
                </div>
                {i < PIPELINE_STEPS.length - 1 && (
                  <div className="flex-shrink-0 text-text-muted text-xs">→</div>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

const FEATURES = [
  { icon: TrendingUp,   title: 'Live News',    desc: 'Real-time ingestion from multiple financial news APIs',      color: 'accent-blue'   },
  { icon: BrainCircuit, title: 'LLM Analysis', desc: 'Gemma LLM analyses sentiment and market impact',            color: 'accent-purple' },
  { icon: Database,     title: 'Vector RAG',   desc: 'ChromaDB powered news embedding and retrieval',             color: 'accent-cyan'   },
  { icon: RefreshCw,    title: 'RL Feedback',  desc: 'Model continuously improves from prediction outcomes',      color: 'accent-green'  },
]

const PIPELINE_STEPS = [
  { icon: '📰', label: 'Fetch News',     color: 'accent-blue'   },
  { icon: '🧠', label: 'LLM Sentiment',  color: 'accent-purple' },
  { icon: '🔢', label: 'Embed & Store',  color: 'accent-cyan'   },
  { icon: '📈', label: 'Stock Data',     color: 'accent-green'  },
  { icon: '🔍', label: 'RAG Retrieve',   color: 'accent-blue'   },
  { icon: '💡', label: 'LLM Reason',     color: 'accent-gold'   },
  { icon: '⚙️', label: 'ML Predict',    color: 'accent-purple' },
  { icon: '✅', label: 'Prediction',     color: 'accent-green'  },
]
