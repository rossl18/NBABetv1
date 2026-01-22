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
      // Only set data if it has actual bets (totalBets > 0)
      if (performanceData && performanceData.totalBets > 0) {
        setData(performanceData)
      } else {
        setData(null) // Show empty state
      }
    } catch (error) {
      console.error('Error loading performance:', error)
      setData(null) // Show empty state instead of sample data
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <LoadingSpinner />
  }

  if (!data || data.totalBets === 0) {
    return (
      <div className="performance-page">
        <div className="container">
          <h1>Model Performance</h1>
          <div style={{ textAlign: 'center', padding: '3rem', color: '#666' }}>
            <p style={{ fontSize: '1.2rem', marginBottom: '1rem' }}>No performance data available yet.</p>
            <p>Performance tracking will appear here once predictions have been made and outcomes have been recorded.</p>
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
