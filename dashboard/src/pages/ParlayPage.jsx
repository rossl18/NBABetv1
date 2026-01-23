import React, { useState, useEffect } from 'react'
import { getLatestBets } from '../services/api'
import ParlayBuilder from '../components/ParlayBuilder'
import LoadingSpinner from '../components/LoadingSpinner'
import './ParlayPage.css'

function ParlayPage() {
  const [bets, setBets] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadBets()
  }, [])

  const loadBets = async () => {
    setLoading(true)
    try {
      const data = await getLatestBets()
      if (Array.isArray(data) && data.length > 0) {
        setBets(data)
      } else {
        setBets([])
      }
    } catch (error) {
      console.error('Error loading bets:', error)
      setBets([])
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="parlay-page">
        <LoadingSpinner />
      </div>
    )
  }

  return (
    <div className="parlay-page">
      <ParlayBuilder bets={bets} />
    </div>
  )
}

export default ParlayPage
