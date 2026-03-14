// src/components/StockChart.jsx
import React, { useEffect, useRef } from 'react'
import { createChart, CrosshairMode } from 'lightweight-charts'

export default function StockChart({ data, width, height = 300 }) {
  const containerRef = useRef(null)
  const chartRef     = useRef(null)
  const seriesRef    = useRef(null)

  useEffect(() => {
    if (!containerRef.current) return

    chartRef.current = createChart(containerRef.current, {
      width:  containerRef.current.clientWidth,
      height,
      layout: {
        background:   { color: 'transparent' },
        textColor:    '#8892a4',
      },
      grid: {
        vertLines:   { color: '#1e2535' },
        horzLines:   { color: '#1e2535' },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { color: '#2196f3', labelBackgroundColor: '#141820' },
        horzLine: { color: '#2196f3', labelBackgroundColor: '#141820' },
      },
      rightPriceScale: {
        borderColor: '#1e2535',
        textColor:   '#8892a4',
      },
      timeScale: {
        borderColor:     '#1e2535',
        timeVisible:     true,
        secondsVisible:  false,
      },
    })

    seriesRef.current = chartRef.current.addCandlestickSeries({
      upColor:          '#00e676',
      downColor:        '#ff3d57',
      borderUpColor:    '#00e676',
      borderDownColor:  '#ff3d57',
      wickUpColor:      '#00e676',
      wickDownColor:    '#ff3d57',
    })

    const handleResize = () => {
      chartRef.current?.applyOptions({ width: containerRef.current?.clientWidth ?? 600 })
    }
    window.addEventListener('resize', handleResize)
    return () => {
      window.removeEventListener('resize', handleResize)
      chartRef.current?.remove()
    }
  }, [height])

  // Update data
  useEffect(() => {
    if (!seriesRef.current || !data) return
    seriesRef.current.setData(data)
    chartRef.current?.timeScale().fitContent()
  }, [data])

  return <div ref={containerRef} className="w-full chart-container" />
}

// Convert OHLCV dict-of-dicts (from API) to lightweight-charts format
export function formatOHLCV(rawData) {
  if (!rawData?.data) return []
  return Object.entries(rawData.data)
    .map(([date, row]) => ({
      time:  date,
      open:  row.Open,
      high:  row.High,
      low:   row.Low,
      close: row.Close,
    }))
    .sort((a, b) => a.time.localeCompare(b.time))
}
