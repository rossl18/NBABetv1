import React, { memo } from 'react'
import EVMeter from './EVMeter'
import './BetCard.css'

const BetCard = memo(function BetCard({ bet }) {
  const ev = bet.expected_value || 0
  const prob = bet.model_probability || 0
  const confidence = bet.confidence_score || 0
  const kelly = bet.kelly_fraction || 0
  
  const getEVColor = (ev) => {
    if (ev > 0.10) return '#10b981' // green
    if (ev > 0.05) return '#3b82f6' // blue
    if (ev > 0) return '#f59e0b' // amber
    return '#ef4444' // red
  }

  const getConfidenceColor = (conf) => {
    if (conf > 0.7) return '#10b981'
    if (conf > 0.5) return '#f59e0b'
    return '#ef4444'
  }

  return (
    <div className="bet-card">
      <div className="bet-header">
        <div className="player-name">{bet.player}</div>
        <div className="prop-type">{bet.prop}</div>
      </div>
      
      <div className="bet-details">
        <div className="detail-row">
          <span className="label">Line:</span>
          <span className="value">{bet.line} {bet.over_under}</span>
        </div>
        <div className="detail-row">
          <span className="label">Odds:</span>
          <span className="value">{bet.odds > 0 ? '+' : ''}{bet.odds}</span>
        </div>
        <div className="detail-row">
          <span className="label">Probability:</span>
          <span className="value">{(prob * 100).toFixed(1)}%</span>
        </div>
      </div>

      <div className="ev-section">
        <EVMeter value={ev} />
        <div className="ev-details">
          <div className="ev-value" style={{ color: getEVColor(ev) }}>
            {ev > 0 ? '+' : ''}{(ev * 100).toFixed(2)}%
          </div>
          <div className="ev-label">Expected Value</div>
          {bet.ev_ci_lower !== null && bet.ev_ci_upper !== null && (
            <div className="ev-ci">
              95% CI: [{((bet.ev_ci_lower || 0) * 100).toFixed(1)}%, {((bet.ev_ci_upper || 0) * 100).toFixed(1)}%]
            </div>
          )}
        </div>
      </div>

      <div className="metrics-row">
        <div className="metric">
          <div className="metric-label">Confidence</div>
          <div className="metric-bar">
            <div 
              className="metric-fill" 
              style={{ 
                width: `${confidence * 100}%`,
                backgroundColor: getConfidenceColor(confidence)
              }}
            />
          </div>
          <div className="metric-value">{(confidence * 100).toFixed(0)}%</div>
        </div>
        {kelly > 0 && (
          <div className="metric">
            <div className="metric-label">Kelly</div>
            <div className="metric-value kelly">{(kelly * 100).toFixed(1)}%</div>
          </div>
        )}
      </div>

      {bet.edge && (
        <div className="edge-badge">
          Edge: {bet.edge > 0 ? '+' : ''}{(bet.edge * 100).toFixed(1)}%
        </div>
      )}
    </div>
  )
})

export default BetCard
