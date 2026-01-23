import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react'
import BetCard from './BetCard'
import './ParlayBuilder.css'

function ParlayBuilder({ bets = [] }) {
  const [selectedBets, setSelectedBets] = useState([])
  const [betAmount, setBetAmount] = useState(100)
  const selectedSectionRef = useRef(null)

  // Convert American odds to decimal
  const americanToDecimal = useCallback((americanOdds) => {
    if (americanOdds > 0) {
      return 1 + (americanOdds / 100)
    } else {
      return 1 + (100 / Math.abs(americanOdds))
    }
  }, [])

  // Convert decimal odds to American
  const decimalToAmerican = useCallback((decimalOdds) => {
    if (decimalOdds >= 2.0) {
      return Math.round((decimalOdds - 1) * 100)
    } else {
      return Math.round(-100 / (decimalOdds - 1))
    }
  }, [])

  // Memoize selected bet IDs for fast lookup
  const selectedBetIds = useMemo(() => {
    return new Set(selectedBets.map(b => 
      `${b.player}|${b.prop}|${b.line}|${b.over_under}`
    ))
  }, [selectedBets])

  // Calculate parlay odds and probability - memoized
  const parlay = useMemo(() => {
    if (selectedBets.length === 0) {
      return {
        combinedOdds: null,
        combinedProbability: null,
        potentialProfit: null,
        totalReturn: null
      }
    }

    // Multiply decimal odds together for parlay
    let combinedDecimalOdds = 1
    let combinedProbability = 1

    selectedBets.forEach(bet => {
      const decimalOdds = americanToDecimal(bet.odds)
      combinedDecimalOdds *= decimalOdds
      
      // Use model probability if available, otherwise use implied probability
      const prob = bet.model_probability || bet.implied_probability || (1 / decimalOdds)
      combinedProbability *= prob
    })

    const combinedAmericanOdds = decimalToAmerican(combinedDecimalOdds)
    const potentialProfit = (betAmount * combinedDecimalOdds) - betAmount
    const totalReturn = betAmount * combinedDecimalOdds

    return {
      combinedOdds: combinedAmericanOdds,
      combinedDecimalOdds,
      combinedProbability,
      potentialProfit,
      totalReturn
    }
  }, [selectedBets, betAmount, americanToDecimal, decimalToAmerican])

  // Scroll to selected bets section when a bet is added
  useEffect(() => {
    if (selectedBets.length > 0 && selectedSectionRef.current) {
      // Small delay to ensure DOM has updated
      const timeoutId = setTimeout(() => {
        selectedSectionRef.current?.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'start',
          inline: 'nearest'
        })
      }, 150)
      return () => clearTimeout(timeoutId)
    }
  }, [selectedBets.length]) // Only trigger when count changes (bet added/removed)

  const toggleBet = useCallback((bet) => {
    const betId = `${bet.player}|${bet.prop}|${bet.line}|${bet.over_under}`
    const isSelected = selectedBetIds.has(betId)

    if (isSelected) {
      setSelectedBets(prev => prev.filter(b => 
        `${b.player}|${b.prop}|${b.line}|${b.over_under}` !== betId
      ))
    } else {
      setSelectedBets(prev => [...prev, bet])
    }
  }, [selectedBetIds])

  const removeBet = useCallback((index) => {
    setSelectedBets(prev => prev.filter((_, i) => i !== index))
  }, [])

  const clearParlay = useCallback(() => {
    setSelectedBets([])
  }, [])

  return (
    <div className="parlay-builder">
      <div className="parlay-container">
        <h1>Parlay Builder</h1>
        <p className="parlay-description">
          Select multiple bets to build a parlay. The combined odds, probability, and potential profit will be calculated automatically.
        </p>

        {/* Selected Bets */}
        <div className="selected-bets-section" ref={selectedSectionRef}>
          <div className="selected-bets-header">
            <h2>Selected Bets ({selectedBets.length})</h2>
            {selectedBets.length > 0 && (
              <button className="clear-btn" onClick={clearParlay}>
                Clear All
              </button>
            )}
          </div>

          {selectedBets.length === 0 ? (
            <div className="empty-parlay">
              <p>No bets selected. Click on bets below to add them to your parlay.</p>
            </div>
          ) : (
            <>
              <div className="selected-bets-list">
                {selectedBets.map((bet, index) => (
                  <div key={index} className="selected-bet-item">
                    <div className="selected-bet-info">
                      <strong>{bet.player}</strong> - {bet.prop} {bet.over_under} {bet.line} ({bet.odds > 0 ? '+' : ''}{bet.odds})
                    </div>
                    <button className="remove-btn" onClick={() => removeBet(index)}>
                      ✕
                    </button>
                  </div>
                ))}
              </div>

              {/* Parlay Calculation */}
              {parlay.combinedOdds !== null && (
                <div className="parlay-calculation">
                  <h3>Parlay Details</h3>
                  <div className="parlay-stats">
                    <div className="parlay-stat">
                      <div className="parlay-stat-label">Combined Odds</div>
                      <div className="parlay-stat-value">
                        {parlay.combinedOdds > 0 ? '+' : ''}{parlay.combinedOdds}
                      </div>
                    </div>
                    <div className="parlay-stat">
                      <div className="parlay-stat-label">Estimated Probability</div>
                      <div className="parlay-stat-value">
                        {(parlay.combinedProbability * 100).toFixed(2)}%
                      </div>
                    </div>
                    <div className="parlay-stat">
                      <div className="parlay-stat-label">Bet Amount</div>
                      <div className="parlay-stat-value">
                        ${betAmount.toFixed(2)}
                      </div>
                    </div>
                    <div className="parlay-stat highlight">
                      <div className="parlay-stat-label">Potential Profit</div>
                      <div className="parlay-stat-value profit">
                        +${parlay.potentialProfit.toFixed(2)}
                      </div>
                    </div>
                    <div className="parlay-stat highlight">
                      <div className="parlay-stat-label">Total Return</div>
                      <div className="parlay-stat-value return">
                        ${parlay.totalReturn.toFixed(2)}
                      </div>
                    </div>
                  </div>
                  
                  <div className="bet-amount-input">
                    <label>Bet Amount ($):</label>
                    <input
                      type="number"
                      min="1"
                      step="1"
                      value={betAmount}
                      onChange={(e) => setBetAmount(Math.max(1, parseFloat(e.target.value) || 1))}
                    />
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Available Bets */}
        <div className="available-bets-section">
          <h2>Available Bets</h2>
          <p className="section-description">
            Click on any bet card to add it to your parlay. Click again to remove it.
          </p>
          <div className="bets-grid">
            {bets.slice(0, 200).map((bet, index) => {
              const betId = `${bet.player}|${bet.prop}|${bet.line}|${bet.over_under}`
              const isSelected = selectedBetIds.has(betId)
              return (
                <div 
                  key={`${bet.player}-${bet.prop}-${bet.line}-${bet.over_under}-${index}`} 
                  className={`bet-card-wrapper ${isSelected ? 'selected' : ''}`}
                  onClick={() => toggleBet(bet)}
                >
                  <BetCard bet={bet} />
                  {isSelected && (
                    <div className="selected-badge">✓ Selected</div>
                  )}
                </div>
              )
            })}
            {bets.length > 200 && (
              <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '2rem', color: '#666' }}>
                Showing first 200 bets. Use filters to narrow down results.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ParlayBuilder
