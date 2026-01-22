import React, { useState, useEffect } from 'react'
import { getLatestBets, reloadBets } from '../services/api'
import BetCard from '../components/BetCard'
import EVMeter from '../components/EVMeter'
import LoadingSpinner from '../components/LoadingSpinner'
import './BetsPage.css'

// All-star players list (update as needed)
const ALL_STAR_PLAYERS = [
  'LeBron James', 'Stephen Curry', 'Kevin Durant', 'Giannis Antetokounmpo',
  'Luka Doncic', 'Jayson Tatum', 'Joel Embiid', 'Nikola Jokic',
  'Devin Booker', 'Damian Lillard', 'Anthony Davis', 'Kawhi Leonard',
  'Jimmy Butler', 'Paul George', 'Kyrie Irving', 'Donovan Mitchell',
  'Jaylen Brown', 'Pascal Siakam', 'Bam Adebayo', 'DeMar DeRozan',
  'Zach LaVine', 'Karl-Anthony Towns', 'Anthony Edwards', 'Ja Morant',
  'Trae Young', 'De\'Aaron Fox', 'Shai Gilgeous-Alexander', 'Tyrese Haliburton'
]

function BetsPage() {
  const [bets, setBets] = useState([])
  const [loading, setLoading] = useState(true)
  const [reloading, setReloading] = useState(false)
  const [filter, setFilter] = useState('all') // all, positive, high-value
  const [allStarFilter, setAllStarFilter] = useState('all') // all, all-star, non-all-star
  const [propTypeFilter, setPropTypeFilter] = useState('all') // all, Points, Rebounds, etc.
  const [sortBy, setSortBy] = useState('ev') // ev, confidence, kelly
  
  // Check if admin mode is enabled via URL parameter
  const isAdmin = new URLSearchParams(window.location.search).get('admin') === 'true'

  useEffect(() => {
    loadBets()
  }, [])

  const loadBets = async () => {
    // Don't block UI - show empty state immediately
    setBets([])
    setLoading(true)
    console.log('Starting to load bets...')
    const startTime = Date.now()
    
    // Safety timeout - force stop loading after 3 seconds no matter what
    const safetyTimeout = setTimeout(() => {
      console.error('SAFETY TIMEOUT: Force stopping load after 3 seconds')
      setLoading(false)
      if (bets.length === 0) {
        setBets([]) // Ensure empty state is shown
      }
    }, 3000)
    
    try {
      const data = await getLatestBets()
      clearTimeout(safetyTimeout)
      
      const loadTime = Date.now() - startTime
      console.log(`Bets loaded in ${loadTime}ms`)
      
      if (Array.isArray(data) && data.length > 0) {
        setBets(data)
        console.log(`Successfully set ${data.length} bets`)
      } else {
        console.warn('Invalid data format or empty:', data)
        setBets([])
      }
    } catch (error) {
      clearTimeout(safetyTimeout)
      const loadTime = Date.now() - startTime
      console.error(`Error loading bets after ${loadTime}ms:`, error)
      setBets([])
    } finally {
      setLoading(false)
      console.log('Loading complete')
    }
  }

  const handleReload = async () => {
    // Password protection - only admin can reload
    const password = prompt('Enter admin password to reload bets:')
    if (password !== 'admin123') { // Change this password!
      alert('Access denied. Only admin can reload bets.')
      return
    }
    
    setReloading(true)
    try {
      await reloadBets()
      await loadBets()
      alert('Bets reloaded successfully!')
    } catch (error) {
      console.error('Error reloading bets:', error)
      alert('Error reloading bets. Check console for details.')
    } finally {
      setReloading(false)
    }
  }

  // Get unique prop types from bets (data is now normalized)
  const propTypes = [...new Set(bets.map(bet => bet.prop))].filter(Boolean).sort()

  const filteredBets = bets.filter(bet => {
    // EV filter (data is now normalized to lowercase)
    if (filter === 'positive' && (bet.expected_value || 0) <= 0) return false
    if (filter === 'high-value' && (bet.expected_value || 0) <= 0.10) return false
    
    // All-star filter
    const playerName = bet.player || ''
    if (allStarFilter === 'all-star') {
      if (!ALL_STAR_PLAYERS.some(star => playerName.includes(star) || star.includes(playerName))) return false
    }
    if (allStarFilter === 'non-all-star') {
      if (ALL_STAR_PLAYERS.some(star => playerName.includes(star) || star.includes(playerName))) return false
    }
    
    // Prop type filter
    const propType = bet.prop || ''
    if (propTypeFilter !== 'all' && propType !== propTypeFilter) return false
    
    return true
  })

  const sortedBets = [...filteredBets].sort((a, b) => {
    if (sortBy === 'ev') {
      // Use Kelly-adjusted EV if available (from backend), otherwise use raw EV
      const aScore = (a.kelly_adjusted_ev !== undefined) 
        ? (a.kelly_adjusted_ev || 0) 
        : ((a.expected_value || 0) * (a.kelly_fraction || 0))
      const bScore = (b.kelly_adjusted_ev !== undefined)
        ? (b.kelly_adjusted_ev || 0)
        : ((b.expected_value || 0) * (b.kelly_fraction || 0))
      return bScore - aScore
    }
    if (sortBy === 'confidence') return (b.confidence_score || 0) - (a.confidence_score || 0)
    if (sortBy === 'kelly') return (b.kelly_fraction || 0) - (a.kelly_fraction || 0)
    return 0
  })

  const stats = {
    total: bets.length,
    positiveEV: bets.filter(b => b.expected_value > 0).length,
    highValue: bets.filter(b => b.expected_value > 0.10).length,
    avgEV: bets.length > 0 
      ? (bets.reduce((sum, b) => sum + (b.expected_value || 0), 0) / bets.length).toFixed(3)
      : 0
  }

  // Never block the UI - always show content, just indicate loading state
  // Show spinner only if we have no data AND are loading
  const showSpinner = loading && bets.length === 0

  return (
    <div className="bets-page">
      <div className="container">
        {showSpinner && <LoadingSpinner />}
        <div className="page-header">
          <div>
            <h1>Best Bets</h1>
            {loading && <p style={{color: '#666', fontSize: '0.9rem'}}>Loading...</p>}
            <p className="props-count">Showing {filteredBets.length} of {bets.length} props</p>
          </div>
          {isAdmin && (
            <button 
              className="reload-btn admin-only" 
              onClick={handleReload}
              disabled={reloading}
              title="Admin only - requires password"
            >
              {reloading ? 'Reloading...' : '🔄 Reload Bets'}
            </button>
          )}
        </div>

        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-value">{stats.total}</div>
            <div className="stat-label">Total Props</div>
          </div>
          <div className="stat-card positive">
            <div className="stat-value">{stats.positiveEV}</div>
            <div className="stat-label">Positive EV</div>
          </div>
          <div className="stat-card high-value">
            <div className="stat-value">{stats.highValue}</div>
            <div className="stat-label">High Value (10%+)</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.avgEV > 0 ? `+${stats.avgEV}` : stats.avgEV}%</div>
            <div className="stat-label">Average EV</div>
          </div>
        </div>

        <div className="controls">
          <div className="filter-group">
            <label>EV Filter:</label>
            <select value={filter} onChange={(e) => setFilter(e.target.value)}>
              <option value="all">All Bets</option>
              <option value="positive">Positive EV Only</option>
              <option value="high-value">High Value (10%+)</option>
            </select>
          </div>
          <div className="filter-group">
            <label>Player Type:</label>
            <select value={allStarFilter} onChange={(e) => setAllStarFilter(e.target.value)}>
              <option value="all">All Players</option>
              <option value="all-star">All-Stars Only</option>
              <option value="non-all-star">Non-All-Stars</option>
            </select>
          </div>
          <div className="filter-group">
            <label>Prop Type:</label>
            <select value={propTypeFilter} onChange={(e) => setPropTypeFilter(e.target.value)}>
              <option value="all">All Props</option>
              {propTypes.map(prop => (
                <option key={prop} value={prop}>{prop}</option>
              ))}
            </select>
          </div>
          <div className="sort-group">
            <label>Sort By:</label>
            <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
              <option value="ev">EV (Risk-Adjusted)</option>
              <option value="confidence">Confidence Score</option>
              <option value="kelly">Kelly Fraction</option>
            </select>
          </div>
        </div>

        <div className="bets-grid">
          {sortedBets.length > 0 ? (
            sortedBets.map((bet, index) => (
              <BetCard key={index} bet={bet} />
            ))
          ) : (
            <div className="no-bets">
              <p>No bets found. Try reloading or check your filters.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default BetsPage
