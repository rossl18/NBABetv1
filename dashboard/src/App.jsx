import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import BetsPage from './pages/BetsPage'
import PerformancePage from './pages/PerformancePage'
import AboutPage from './pages/AboutPage'
import ParlayPage from './pages/ParlayPage'
import Navbar from './components/Navbar'
import './App.css'

function App() {
  // Use basename only in production (GitHub Pages), not in local dev
  const basename = import.meta.env.PROD ? '/NBABetv1' : '/'
  
  console.log('App rendering, basename:', basename)
  console.log('Environment:', import.meta.env.MODE)
  
  return (
    <BrowserRouter basename={basename}>
      <div className="app">
        <Navbar />
        <Routes>
          <Route path="/" element={<BetsPage />} />
          <Route path="/performance" element={<PerformancePage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/parlay" element={<ParlayPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

export default App
