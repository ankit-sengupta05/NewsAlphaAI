// src/components/LivePriceHeader.jsx
import React from 'react'
import clsx from 'clsx'
import { Wifi, WifiOff } from 'lucide-react'
import { useLivePrice } from '../hooks/useLivePrice.js'
import { fmt } from '../utils/api.js'

export default function LivePriceHeader({ ticker, stockInfo }) {
  const { price, change, changePct, flash } = useLivePrice(ticker)
  const isUp = changePct >= 0

  return (
    <div className={clsx(
      'card p-5 transition-all duration-300',
      flash === 'up'   && 'border-accent-green/40',
      flash === 'down' && 'border-accent-red/40',
    )}>
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          {/* Ticker + name */}
          <div className="flex items-center gap-3">
            <span className="text-2xl font-mono font-bold text-text-primary">{ticker}</span>
            {stockInfo?.name && (
              <span className="text-sm text-text-muted">{stockInfo.name}</span>
            )}
          </div>

          {/* Sector tags */}
          {(stockInfo?.sector || stockInfo?.exchange) && (
            <div className="flex gap-2">
              {stockInfo.sector && (
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-accent-blue/10 text-accent-blue border border-accent-blue/20">
                  {stockInfo.sector}
                </span>
              )}
              {stockInfo.exchange && (
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-bg-secondary text-text-muted border border-bg-border">
                  {stockInfo.exchange}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Live price */}
        <div className="text-right">
          <div className={clsx(
            'text-3xl font-mono font-bold transition-colors duration-300',
            flash === 'up'   ? 'text-accent-green' :
            flash === 'down' ? 'text-accent-red'   :
            isUp             ? 'text-accent-green' : 'text-accent-red'
          )}>
            {price != null ? fmt.price(price) : '—'}
          </div>
          <div className={clsx('text-sm font-mono', isUp ? 'text-accent-green' : 'text-accent-red')}>
            {change != null ? (change > 0 ? '+' : '') + fmt.price(change) : ''}{' '}
            <span className="text-sm">({fmt.pct(changePct)})</span>
          </div>
          {stockInfo?.market_cap ? (
            <div className="text-[10px] text-text-muted font-mono mt-0.5">
              MCap: {fmt.k(stockInfo.market_cap)}
            </div>
          ) : null}
        </div>
      </div>

      {/* Live indicator */}
      <div className="flex items-center gap-1.5 mt-3 pt-3 border-t border-bg-border">
        <div className="w-1.5 h-1.5 rounded-full bg-accent-green animate-pulse-green" />
        <span className="text-[10px] font-mono text-text-muted">LIVE · refreshes every 15s</span>
      </div>
    </div>
  )
}
