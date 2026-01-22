import React from 'react'
import './EVMeter.css'

function EVMeter({ value }) {
  // Normalize EV to -20% to +20% range for display
  const normalizedValue = Math.max(-0.20, Math.min(0.20, value))
  const percentage = (normalizedValue * 100) / 0.20 // Convert to -100 to +100 range
  const displayValue = (value * 100).toFixed(1)
  
  const getColor = (val) => {
    if (val > 0.10) return '#10b981' // green
    if (val > 0.05) return '#3b82f6' // blue
    if (val > 0) return '#f59e0b' // amber
    return '#ef4444' // red
  }

  return (
    <div className="ev-meter">
      <div className="meter-container">
        <div className="meter-track">
          <div 
            className="meter-fill"
            style={{
              width: `${Math.abs(percentage)}%`,
              left: percentage < 0 ? '50%' : '50%',
              transform: percentage < 0 ? 'scaleX(-1)' : 'none',
              backgroundColor: getColor(value)
            }}
          />
          <div className="meter-center" />
        </div>
        <div className="meter-labels">
          <span>-20%</span>
          <span>0%</span>
          <span>+20%</span>
        </div>
      </div>
    </div>
  )
}

export default EVMeter
