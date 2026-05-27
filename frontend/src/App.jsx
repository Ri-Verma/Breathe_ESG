import React, { useState, useEffect } from 'react'
import './App.css'
import FileUpload from './components/FileUpload'
import MetricsDisplay from './components/MetricsDisplay'
import Dashboard from './components/Dashboard'

function App() {
  const [files, setFiles] = useState([])
  const [metrics, setMetrics] = useState([])
  const [loading, setLoading] = useState(false)

  const handleFileUpload = async (file) => {
    setLoading(true)
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      const response = await fetch('/api/files/upload/', {
        method: 'POST',
        body: formData,
      })
      
      if (response.ok) {
        const data = await response.json()
        setFiles([...files, data])
        fetchMetrics()
      }
    } catch (error) {
      console.error('Error uploading file:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchMetrics = async () => {
    try {
      const response = await fetch('/api/metrics/')
      if (response.ok) {
        const data = await response.json()
        setMetrics(data.results || data)
      }
    } catch (error) {
      console.error('Error fetching metrics:', error)
    }
  }

  useEffect(() => {
    fetchMetrics()
  }, [])

  return (
    <div className="App">
      <header className="header">
        <h1>Breadth ESG Dashboard</h1>
        <p>Environmental, Social & Governance Metrics Management</p>
      </header>
      
      <main className="container">
        <div className="section">
          <FileUpload onUpload={handleFileUpload} loading={loading} />
        </div>
        
        <div className="section">
          <Dashboard metrics={metrics} />
        </div>
        
        <div className="section">
          <MetricsDisplay metrics={metrics} />
        </div>
      </main>
    </div>
  )
}

export default App
