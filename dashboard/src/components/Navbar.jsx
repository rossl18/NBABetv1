import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import './Navbar.css'

function Navbar() {
  const location = useLocation()
  
  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-brand">
          NBA Betting Dashboard
        </Link>
        <div className="navbar-links">
          <Link 
            to="/" 
            className={location.pathname === '/' ? 'active' : ''}
          >
            Best Bets
          </Link>
          <Link 
            to="/performance" 
            className={location.pathname === '/performance' ? 'active' : ''}
          >
            Performance
          </Link>
        </div>
      </div>
    </nav>
  )
}

export default Navbar
