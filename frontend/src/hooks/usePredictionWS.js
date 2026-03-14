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
  fetch_news:        { label: 'Fetching News',           icon: '📰' },
  analyse_sentiment: { label: 'Sentiment Analysis',      icon: '🧠' },
  embed_store:       { label: 'Vector Embedding',        icon: '🔢' },
  fetch_stock:       { label: 'Stock Data',              icon: '📈' },
  rag_retrieve:      { label: 'RAG Retrieval',           icon: '🔍' },
  llm_reason:        { label: 'LLM Reasoning',           icon: '💡' },
  ml_predict:        { label: 'ML Prediction',           icon: '⚙️' },
  final_predict:     { label: 'Final Prediction',        icon: '✅' },
}

export function usePredictionWS() {
  const [status, setStatus]         = useState('idle')       // idle | connecting | running | complete | error
  const [currentStep, setCurrentStep] = useState(null)
  const [completedSteps, setCompletedSteps] = useState([])
  const [stepData, setStepData]     = useState({})
  const [prediction, setPrediction] = useState(null)
  const [logs, setLogs]             = useState([])
  const [error, setError]           = useState(null)
  const wsRef = useRef(null)

  const reset = useCallback(() => {
    setStatus('idle')
    setCurrentStep(null)
    setCompletedSteps([])
    setStepData({})
    setPrediction(null)
    setLogs([])
    setError(null)
  }, [])

  const run = useCallback((ticker) => {
    if (wsRef.current) wsRef.current.close()
    reset()
    setStatus('connecting')

    const ws = new WebSocket(wsUrl(`/ws/predict/${ticker}`))
    wsRef.current = ws

    ws.onopen = () => setStatus('running')

    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data)

      if (msg.type === 'start') {
        setLogs(prev => [...prev, `▶ ${msg.message}`])
      }

      if (msg.type === 'step') {
        setCurrentStep(msg.step)
        setCompletedSteps(prev =>
          prev.includes(msg.step) ? prev : [...prev, msg.step]
        )
        if (msg.logs?.length) {
          setLogs(prev => [...prev, ...msg.logs])
        }
        setStepData(prev => ({ ...prev, [msg.step]: msg }))
      }

      if (msg.type === 'complete') {
        setStatus('complete')
        setPrediction(msg.prediction)
        setCurrentStep(null)
        setLogs(prev => [...prev, `✅ Pipeline complete`])
      }

      if (msg.type === 'error') {
        setStatus('error')
        setError(msg.message)
      }
    }

    ws.onerror = () => {
      setStatus('error')
      setError('WebSocket connection failed. Is the backend running?')
    }

    ws.onclose = () => {
      if (status === 'running') setStatus('idle')
    }
  }, [reset])

  useEffect(() => () => wsRef.current?.close(), [])

  return {
    status, currentStep, completedSteps, stepData,
    prediction, logs, error,
    run, reset,
    steps: STEPS,
    stepMeta: STEP_META,
    progress: STEPS.indexOf(currentStep) + 1,
    totalSteps: STEPS.length,
  }
}
