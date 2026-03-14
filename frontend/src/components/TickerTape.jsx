// src/components/TickerTape.jsx
import React from 'react'
import { useLivePrice } from '../hooks/useLivePrice.js'
import clsx from 'clsx'

function TickerItem({ ticker }) {
  const { price, changePct, flash } = useLivePrice(ticker)
  const isUp = changePct >= 0

  return (
    <span className={clsx(
      'inline-flex items-center gap-2 px-4 text-xs font-mono transition-colors duration-300',
      flash === 'up'   && 'text-accent-green',
      flash === 'down' && 'text-accent-red',
      !flash && 'text-text-secondary',
    )}>
      <span className="text-text-muted">{ticker}</span>
      {price != null ? (
        <>
          <span className={clsx('font-semibold', isUp ? 'text-accent-green' : 'text-accent-red')}>
            ${price.toFixed(2)}
          </span>
          <span className={clsx('text-[10px]', isUp ? 'text-accent-green/60' : 'text-accent-red/60')}>
            {isUp ? '▲' : '▼'} {Math.abs(changePct ?? 0).toFixed(2)}%
          </span>
        </>
      ) : (
        <span className="text-text-muted">—</span>
      )}
      <span className="text-bg-border mx-1">|</span>
    </span>
  )
}

export default function TickerTape({ tickers }) {
  const doubled = [...tickers, ...tickers]

  return (
    <div className="h-8 bg-bg-secondary border-b border-bg-border overflow-hidden flex items-center relative">
      {/* Fade edges */}
      <div className="absolute left-0 top-0 h-full w-12 bg-gradient-to-r from-bg-secondary to-transparent z-10 pointer-events-none" />
      <div className="absolute right-0 top-0 h-full w-12 bg-gradient-to-l from-bg-secondary to-transparent z-10 pointer-events-none" />

      <div className="ticker-tape">
        <div className="ticker-content animate-ticker-scroll flex">
          {doubled.map((t, i) => <TickerItem key={`${t}-${i}`} ticker={t} />)}
        </div>
      </div>
    </div>
  )
}
