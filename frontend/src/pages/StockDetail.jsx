// src/pages/StockDetail.jsx
import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Play, RotateCcw, AlertTriangle } from 'lucide-react'
import clsx from 'clsx'

import { api } from '../utils/api.js'
import { usePredictionWS } from '../hooks/usePredictionWS.js'

import LivePriceHeader   from '../components/LivePriceHeader.jsx'
import StockChart, { formatOHLCV } from '../components/StockChart.jsx'
import PipelineProgress  from '../components/PipelineProgress.jsx'
import PredictionCard    from '../components/PredictionCard.jsx'
import SentimentGauge    from '../components/SentimentGauge.jsx'
import TechnicalsPanel   from '../components/TechnicalsPanel.jsx'
import RLStatsPanel      from '../components/RLStatsPanel.jsx'

export default function StockDetail() {
  const { ticker }  = useParams()
  const navigate    = useNavigate()
  const TICKER      = ticker?.toUpperCase()

  const [stockInfo,   setStockInfo]   = useState(null)
  const [chartData,   setChartData]   = useState(null)
  const [technicals,  setTechnicals]  = useState(null)
  const [rlStats,     setRlStats]     = useState(null)
  const [period,      setPeriod]      = useState('30d')

  const {
    status, currentStep, completedSteps, stepData,
    prediction, logs, error,
    run, reset,
    steps, stepMeta, totalSteps,
  } = usePredictionWS()

  // Load static data on mount
  useEffect(() => {
    if (!TICKER) return
    api.get(`/api/stock/${TICKER}/info`).then(setStockInfo).catch(() => {})
    api.get(`/api/prediction/${TICKER}/rl-stats`).then(setRlStats).catch(() => {})
  }, [TICKER])

  useEffect(() => {
    if (!TICKER) return
    api.get(`/api/stock/${TICKER}/chart?period=${period}`).then(d => setChartData(formatOHLCV(d))).catch(() => {})
  }, [TICKER, period])

  // Update technicals from step data when pipeline runs
  useEffect(() => {
    const td = stepData?.fetch_stock?.technicals
    if (td) setTechnicals(td)
  }, [stepData])

  // Load technicals independently if no pipeline run yet
  useEffect(() => {
    if (!TICKER || technicals) return
    api.get(`/api/stock/${TICKER}/technicals`).then(setTechnicals).catch(() => {})
  }, [TICKER])

  const sentiment = stepData?.analyse_sentiment?.sentiment

  const canRun = status === 'idle' || status === 'complete' || status === 'error'

  return (
    <div className="p-5 space-y-4 animate-fade-in">
      {/* Top bar */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-sm text-text-muted hover:text-text-primary transition-colors"
        >
          <ArrowLeft size={15} />
          Back
        </button>

        <div className="flex gap-2">
          {(status === 'complete' || status === 'error') && (
            <button className="btn-ghost flex items-center gap-2 text-xs" onClick={reset}>
              <RotateCcw size={13} />
              Reset
            </button>
          )}
          <button
            className={clsx(
              'btn-primary flex items-center gap-2 text-xs',
              !canRun && 'opacity-60 pointer-events-none'
            )}
            onClick={() => run(TICKER)}
            disabled={!canRun}
          >
            <Play size={13} />
            {status === 'running' ? 'Running…' : 'Run AI Prediction'}
          </button>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-accent-red/10 border border-accent-red/20 text-accent-red text-sm">
          <AlertTriangle size={15} />
          {error}
        </div>
      )}

      {/* Live price header */}
      <LivePriceHeader ticker={TICKER} stockInfo={stockInfo} />

      {/* Main grid */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">

        {/* Left column (2/3) */}
        <div className="xl:col-span-2 space-y-4">

          {/* Chart */}
          <div className="card p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="stat-label">PRICE CHART</div>
              <div className="flex gap-1">
                {['7d','30d','90d'].map(p => (
                  <button
                    key={p}
                    onClick={() => setPeriod(p)}
                    className={clsx(
                      'px-2.5 py-1 rounded text-[10px] font-mono transition-all',
                      period === p
                        ? 'bg-accent-blue/20 text-accent-blue border border-accent-blue/30'
                        : 'text-text-muted hover:text-text-primary border border-transparent'
                    )}
                  >
                    {p.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>
            {chartData ? (
              <StockChart data={chartData} height={280} />
            ) : (
              <div className="h-72 flex items-center justify-center text-text-muted text-sm">
                Loading chart…
              </div>
            )}
          </div>

          {/* Pipeline */}
          {status !== 'idle' && (
            <PipelineProgress
              steps={steps}
              currentStep={currentStep}
              completedSteps={completedSteps}
              logs={logs}
              status={status}
            />
          )}

          {/* Sentiment gauge */}
          {(sentiment || prediction) && (
            <SentimentGauge sentiment={sentiment || {
              overall_sentiment: prediction?.sentiment,
              sentiment_score: prediction?.sentiment_score,
              confidence: prediction?.probability,
            }} />
          )}
        </div>

        {/* Right column (1/3) */}
        <div className="space-y-4">

          {/* Prediction card (or idle CTA) */}
          {prediction ? (
            <PredictionCard prediction={prediction} />
          ) : (
            <div className="card p-6 text-center space-y-3">
              <div className="text-3xl">🔮</div>
              <div className="text-sm font-semibold text-text-primary">No prediction yet</div>
              <div className="text-xs text-text-muted">
                Click "Run AI Prediction" to start the full pipeline
              </div>
              <button
                className="btn-primary w-full text-sm"
                onClick={() => run(TICKER)}
                disabled={!canRun}
              >
                Run AI Prediction
              </button>
            </div>
          )}

          {/* Technicals */}
          <TechnicalsPanel technicals={technicals} />

          {/* RL stats */}
          <RLStatsPanel stats={rlStats} />
        </div>
      </div>
    </div>
  )
}
