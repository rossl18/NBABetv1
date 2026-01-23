import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import './Navbar.css'

function Navbar() {
  const location = useLocation()
  
  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-brand">
          RLBet
        </Link>
        <div className="navbar-links">
          <Link 
            to="/" 
            className={location.pathname === '/' ? 'active' : ''}
          >
            Today's Bets
          </Link>
          <Link 
            to="/performance" 
            className={location.pathname === '/performance' ? 'active' : ''}
          >
            Performance
          </Link>
          <Link 
            to="/parlay" 
            className={location.pathname === '/parlay' ? 'active' : ''}
          >
            Parlay Builder
          </Link>
          <Link 
            to="/about" 
            className={location.pathname === '/about' ? 'active' : ''}
          >
            About
          </Link>
        </div>
      </div>
    </nav>
  )
}

export default Navbar
