// src/hooks/usePredictionWS.js
import { useState, useEffect, useRef, useCallback } from 'react'
import { wsUrl } from '../utils/api'

const STEPS = [
  'fetch_news',
  'analyse_sentiment',
  'embed_store',
  'fetch_stock',
  'rag_retrieve',
  'llm_reason',
  'ml_predict',
  'final_predict',
]

const STEP_META = {
  fetch_news:        { label: 'Fetching News',      icon: '📰' },
  analyse_sentiment: { label: 'Sentiment Analysis', icon: '🧠' },
  embed_store:       { label: 'Vector Embedding',   icon: '🔢' },
  fetch_stock:       { label: 'Stock Data',         icon: '📈' },
  rag_retrieve:      { label: 'RAG Retrieval',      icon: '🔍' },
  llm_reason:        { label: 'LLM Reasoning',      icon: '💡' },
  ml_predict:        { label: 'ML Prediction',      icon: '⚙️' },
  final_predict:     { label: 'Final Prediction',   icon: '✅' },
}

export function usePredictionWS() {
  const [status, setStatus]                 = useState('idle')
  const [currentStep, setCurrentStep]       = useState(null)
  const [completedSteps, setCompletedSteps] = useState([])
  const [stepData, setStepData]             = useState({})
  const [prediction, setPrediction]         = useState(null)
  const [logs, setLogs]                     = useState([])
  const [error, setError]                   = useState(null)

  const wsRef     = useRef(null)
  const statusRef = useRef('idle')

  const updateStatus = useCallback((s) => {
    statusRef.current = s
    setStatus(s)
  }, [])

  const reset = useCallback(() => {
    updateStatus('idle')
    setCurrentStep(null)
    setCompletedSteps([])
    setStepData({})
    setPrediction(null)
    setLogs([])
    setError(null)
  }, [updateStatus])

  const addLog = useCallback((line) => {
    if (!line?.trim()) return
    setLogs(prev => {
      if (prev.length > 0 && prev[prev.length - 1] === line) return prev
      return [...prev, line]
    })
  }, [])

  const run = useCallback((ticker) => {
    if (wsRef.current) wsRef.current.close()
    reset()
    updateStatus('connecting')

    const ws = new WebSocket(wsUrl(`/ws/predict/${ticker}`))
    wsRef.current = ws

    ws.onopen = () => updateStatus('running')

    ws.onmessage = (e) => {
      let msg
      try { msg = JSON.parse(e.data) } catch { return }

      // ── start ─────────────────────────────────────────────────
      if (msg.type === 'start') {
        addLog(`▶ ${msg.message}`)
        return
      }

      // ── step_start: node just BEGAN — mark it active immediately
      if (msg.type === 'step_start') {
        setCurrentStep(msg.step)
        if (msg.logs?.length) msg.logs.forEach(l => addLog(l))
        return
      }

      // ── step: node just FINISHED — mark it complete, clear active
      if (msg.type === 'step') {
        const done = msg.step
        setCompletedSteps(cs => cs.includes(done) ? cs : [...cs, done])
        // Only clear currentStep if this step is still the active one
        setCurrentStep(cur => cur === done ? null : cur)
        setStepData(sd => ({ ...sd, [done]: msg }))
        if (msg.logs?.length) msg.logs.forEach(l => addLog(l))
        if (
          msg.article_count !== undefined &&
          !msg.logs?.some(l => l.includes('article'))
        ) {
          addLog(`Fetched ${msg.article_count} articles from 3 sources`)
        }
        return
      }

      // ── complete ───────────────────────────────────────────────
      if (msg.type === 'complete') {
        setCompletedSteps([...STEPS])
        setCurrentStep(null)
        setPrediction(msg.prediction)
        updateStatus('complete')
        addLog('Pipeline complete')
        return
      }

      // ── error ──────────────────────────────────────────────────
      if (msg.type === 'error') {
        updateStatus('error')
        setError(msg.message)
        addLog(`Error: ${msg.message}`)
      }
    }

    ws.onerror = () => {
      updateStatus('error')
      setError('WebSocket connection failed. Is the backend running?')
    }

    ws.onclose = () => {
      if (
        statusRef.current === 'running' ||
        statusRef.current === 'connecting'
      ) {
        updateStatus('idle')
      }
    }
  }, [reset, updateStatus, addLog])

  useEffect(() => () => wsRef.current?.close(), [])

  const completedCount = completedSteps.length
  const currentIndex   = currentStep ? STEPS.indexOf(currentStep) : -1
  const progress = status === 'complete'
    ? 100
    : currentIndex >= 0
      ? Math.round(((currentIndex + 0.5) / STEPS.length) * 100)
      : completedCount > 0
        ? Math.round((completedCount / STEPS.length) * 100)
        : 0

  return {
    status,
    currentStep,
    completedSteps,
    stepData,
    prediction,
    logs,
    error,
    run,
    reset,
    steps: STEPS,
    stepMeta: STEP_META,
    progress,
    completedCount,
    totalSteps: STEPS.length,
  }
}
