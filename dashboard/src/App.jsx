import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import BetsPage from './pages/BetsPage'
import PerformancePage from './pages/PerformancePage'
import Navbar from './components/Navbar'
import './App.css'

function App() {
  return (
    <BrowserRouter basename="/NBABetv1">
      <div className="app">
        <Navbar />
        <Routes>
          <Route path="/" element={<BetsPage />} />
          <Route path="/performance" element={<PerformancePage />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

export default App
