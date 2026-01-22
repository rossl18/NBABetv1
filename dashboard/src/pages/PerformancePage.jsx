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
        byProp: [],
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
        byProp: [],
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
            <div className="stat-value">{data.roi}%</div>
            <div className="stat-label">ROI</div>
          </div>
        </div>

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
