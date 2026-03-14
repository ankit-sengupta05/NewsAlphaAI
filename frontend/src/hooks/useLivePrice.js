// src/hooks/useLivePrice.js
import { useState, useEffect, useRef } from 'react'
import { wsUrl } from '../utils/api'

export function useLivePrice(ticker) {
  const [price, setPrice]       = useState(null)
  const [change, setChange]     = useState(null)
  const [changePct, setChangePct] = useState(null)
  const [flash, setFlash]       = useState(null)   // 'up' | 'down' | null
  const wsRef  = useRef(null)
  const prevRef = useRef(null)

  useEffect(() => {
    if (!ticker) return
    const ws = new WebSocket(wsUrl(`/ws/live/${ticker}`))
    wsRef.current = ws

    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data)
      if (msg.type !== 'price') return

      const newPrice = msg.price
      if (prevRef.current != null) {
        const dir = newPrice > prevRef.current ? 'up' : newPrice < prevRef.current ? 'down' : null
        if (dir) {
          setFlash(dir)
          setTimeout(() => setFlash(null), 800)
        }
      }
      prevRef.current = newPrice
      setPrice(newPrice)
      setChange(msg.change)
      setChangePct(msg.change_pct)
    }

    return () => ws.close()
  }, [ticker])

  return { price, change, changePct, flash }
}
