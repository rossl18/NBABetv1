import React, { useState, useEffect } from 'react'
import { getPerformanceData } from '../services/api'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import LoadingSpinner from '../components/LoadingSpinner'
import './PerformancePage.css'

function PerformancePage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadPerformance()
  }, [])

  const loadPerformance = async () => {
    setLoading(true)
    try {
      const performanceData = await getPerformanceData()
      // Always set data, even if empty - ensures page is always accessible
      setData(performanceData || {
        totalBets: 0,
        wins: 0,
        losses: 0,
        winRate: 0,
        totalProfit: 0,
        roi: 0,
        avgEV: 0,
        byProp: [],
        byOdds: [],
        probCalibration: [],
        expectedVsActual: {},
        overTime: []
      })
    } catch (error) {
      console.error('Error loading performance:', error)
      // Set empty structure instead of null to ensure page is accessible
      setData({
        totalBets: 0,
        wins: 0,
        losses: 0,
        winRate: 0,
        totalProfit: 0,
        roi: 0,
        avgEV: 0,
        byProp: [],
        byOdds: [],
        probCalibration: [],
        expectedVsActual: {},
        overTime: []
      })
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <LoadingSpinner />
  }

  // Always render the page, show empty state if no data
  if (!data || data.totalBets === 0) {
    return (
      <div className="performance-page">
        <div className="container">
          <h1>Model Performance</h1>
          <div className="empty-state">
            <div style={{ textAlign: 'center', padding: '4rem 2rem', color: '#666' }}>
              <div style={{ fontSize: '4rem', marginBottom: '1rem', opacity: 0.3 }}>📊</div>
              <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem', color: '#333' }}>
                No Performance Data Yet
              </h2>
              <p style={{ fontSize: '1.1rem', marginBottom: '0.5rem', lineHeight: '1.6' }}>
                Performance tracking will appear here once:
              </p>
              <ul style={{ 
                textAlign: 'left', 
                display: 'inline-block', 
                marginTop: '1rem',
                fontSize: '1rem',
                lineHeight: '1.8'
              }}>
                <li>Predictions have been generated</li>
                <li>Games have been played</li>
                <li>Outcomes have been recorded</li>
              </ul>
              <p style={{ 
                marginTop: '2rem', 
                fontSize: '0.9rem', 
                color: '#999',
                fontStyle: 'italic'
              }}>
                Check back after tonight's games!
              </p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="performance-page">
      <div className="container">
        <h1>Model Performance</h1>
        
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-value">{data.totalBets}</div>
            <div className="stat-label">Total Bets</div>
          </div>
          <div className="stat-card positive">
            <div className="stat-value">{data.wins}</div>
            <div className="stat-label">Wins</div>
          </div>
          <div className="stat-card negative">
            <div className="stat-value">{data.losses}</div>
            <div className="stat-label">Losses</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{data.winRate}%</div>
            <div className="stat-label">Win Rate</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{data.roi >= 0 ? '+' : ''}{data.roi}%</div>
            <div className="stat-label">ROI</div>
          </div>
          {data.avgEV !== undefined && (
            <div className="stat-card">
              <div className="stat-value">{data.avgEV >= 0 ? '+' : ''}{data.avgEV.toFixed(3)}</div>
              <div className="stat-label">Avg Expected Value</div>
            </div>
          )}
        </div>

        {/* Expected vs Actual Performance */}
        {data.expectedVsActual && Object.keys(data.expectedVsActual).length > 0 && (
          <div className="diagnostics-section">
            <h2>Model Calibration</h2>
            <div className="diagnostic-card">
              <div className="diagnostic-row">
                <span className="diagnostic-label">Expected Wins (from probabilities):</span>
                <span className="diagnostic-value">{data.expectedVsActual.expectedWins}</span>
              </div>
              <div className="diagnostic-row">
                <span className="diagnostic-label">Actual Wins:</span>
                <span className="diagnostic-value">{data.expectedVsActual.actualWins}</span>
              </div>
              <div className="diagnostic-row">
                <span className="diagnostic-label">Difference:</span>
                <span className={`diagnostic-value ${data.expectedVsActual.difference >= 0 ? 'positive' : 'negative'}`}>
                  {data.expectedVsActual.difference >= 0 ? '+' : ''}{data.expectedVsActual.difference}
                </span>
              </div>
              <p className="diagnostic-note">
                {data.expectedVsActual.difference > 0 
                  ? 'Model is performing better than expected!' 
                  : data.expectedVsActual.difference < 0 
                    ? 'Model is underperforming predictions' 
                    : 'Model is perfectly calibrated'}
              </p>
            </div>
          </div>
        )}

        {/* Probability Calibration Table */}
        {data.probCalibration && data.probCalibration.length > 0 && (
          <div className="diagnostics-section">
            <h2>Probability Calibration Analysis</h2>
            <div className="diagnostic-card">
              <p className="diagnostic-description">
                This shows how well your model's predicted probabilities match actual outcomes.
                Ideally, bets predicted at 70% should win ~70% of the time.
                <strong> Large positive differences indicate overconfidence (model predicted too high).</strong>
              </p>
              <table className="calibration-table">
                <thead>
                  <tr>
                    <th>Probability Range</th>
                    <th>Bets</th>
                    <th>Avg Predicted</th>
                    <th>Actual Win Rate</th>
                    <th>Difference</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.probCalibration.map((cal, idx) => {
                    // Flag severe overconfidence (predicted > 70% but actual < 50%)
                    const predicted = parseFloat(cal.predicted);
                    const actual = parseFloat(cal.actual);
                    const diff = parseFloat(cal.difference);
                    const isOverconfident = predicted > 70 && actual < 50;
                    const isPoor = diff > 15; // More than 15% off
                    
                    // Color logic: Large positive differences are BAD (overconfidence) = RED
                    // Small differences are GOOD (well calibrated) = GREEN
                    // Large negative differences are also concerning = YELLOW/ORANGE
                    let diffColorClass = '';
                    if (Math.abs(diff) < 5) {
                      diffColorClass = 'positive'; // Well calibrated = green
                    } else if (diff > 15) {
                      diffColorClass = 'negative'; // Severe overconfidence = red
                    } else if (diff < -15) {
                      diffColorClass = 'warning'; // Severe underconfidence = warning color
                    } else if (diff > 0) {
                      diffColorClass = 'negative'; // Moderate overconfidence = red
                    }
                    
                    return (
                      <tr key={idx} className={isOverconfident ? 'overconfident-row' : isPoor ? 'poor-calibration-row' : ''}>
                        <td><strong>{cal.range}</strong></td>
                        <td>{cal.count}</td>
                        <td>{cal.predicted}%</td>
                        <td>{cal.actual}%</td>
                        <td className={diffColorClass}>
                          {diff >= 0 ? '+' : ''}{cal.difference}%
                        </td>
                        <td>
                          {isOverconfident ? (
                            <span className="calibration-badge bad">⚠️ Overconfident</span>
                          ) : isPoor ? (
                            <span className="calibration-badge warning">⚠️ Poor Calibration</span>
                          ) : Math.abs(diff) < 5 ? (
                            <span className="calibration-badge good">✓ Well Calibrated</span>
                          ) : (
                            <span className="calibration-badge ok">~ Acceptable</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Performance by Odds Range */}
        {data.byOdds && data.byOdds.length > 0 && (
          <div className="diagnostics-section">
            <h2>Performance by Odds Range</h2>
            <div className="diagnostic-card">
              <table className="calibration-table">
                <thead>
                  <tr>
                    <th>Odds Category</th>
                    <th>Bets</th>
                    <th>Wins</th>
                    <th>Losses</th>
                    <th>Win Rate</th>
                    <th>Profit</th>
                  </tr>
                </thead>
                <tbody>
                  {data.byOdds.map((odds, idx) => (
                    <tr key={idx}>
                      <td>{odds.category}</td>
                      <td>{odds.count}</td>
                      <td>{odds.wins}</td>
                      <td>{odds.losses}</td>
                      <td>{odds.winRate}%</td>
                      <td className={odds.profit >= 0 ? 'positive' : 'negative'}>
                        ${odds.profit >= 0 ? '+' : ''}{odds.profit.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <div className="charts-section">
          <div className="chart-card">
            <h2>Cumulative Profit Over Time</h2>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={data.overTime}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="cumulative" stroke="#667eea" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-card">
            <h2>Performance by Prop Type</h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={data.byProp}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="prop" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="wins" fill="#10b981" />
                <Bar dataKey="losses" fill="#ef4444" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PerformancePage
