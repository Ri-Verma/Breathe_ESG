import React, { useState, useEffect } from 'react'
import axios from 'axios'
import './App.css'
import FileUpload from './components/FileUpload'
import Dashboard from './components/Dashboard'
import RecordsTable from './components/MetricsDisplay'
import EditRecord from './components/EditRecord'
import AuditTrail from './components/AuditTrail'

function App() {
  const [summary, setSummary] = useState(null)
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)
  const [notification, setNotification] = useState('')
  const [notificationType, setNotificationType] = useState('success')
  const [selectedRecord, setSelectedRecord] = useState(null)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showAuditModal, setShowAuditModal] = useState(false)
  const [selectedAuditRecord, setSelectedAuditRecord] = useState(null)

  useEffect(() => {
    fetchDashboardData()
    // Refresh dashboard every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      // Fetch summary stats
      const summaryResponse = await axios.get('/api/emissions/summary/')
      setSummary(summaryResponse.data)

      // Fetch all records
      const recordsResponse = await axios.get('/api/emissions/')
      setRecords(recordsResponse.data.results || recordsResponse.data)
      
      setNotification('')
    } catch (error) {
      console.error('Error fetching data:', error)
      // setNotification('Failed to load dashboard data')
      // setNotificationType('error')
    } finally {
      setLoading(false)
    }
  }

  const showNotification = (message, type = 'success') => {
    setNotification(message)
    setNotificationType(type)
    setTimeout(() => setNotification(''), 4000)
  }

  const handleUploadSuccess = (uploadData) => {
    showNotification(
      ` Successfully uploaded ${uploadData.filename}! ${uploadData.statistics?.successful || 0} records added.`,
      'success'
    )
    fetchDashboardData()
  }

  const handleUploadError = (error) => {
    showNotification(`❌ ${error}`, 'error')
  }

  const handleRecordUpdate = (record) => {
    setSelectedRecord(record)
    setShowEditModal(true)
  }

  const handleRecordSave = (updatedRecord) => {
    // Update the records list with the saved record
    setRecords(records.map(r => r.id === updatedRecord.id ? updatedRecord : r))
    showNotification('Record updated successfully!', 'success')
    fetchDashboardData()
    setShowEditModal(false)
  }

  const handleAuditClick = (record) => {
    setSelectedAuditRecord(record)
    setShowAuditModal(true)
  }

  return (
    <div className="App">
      <header className="header">
        <div className="header-content">
          <div className="logo-section">
            <h1>🌍 Breadth ESG Dashboard</h1>
            <p>Environmental, Social & Governance Emissions Management</p>
          </div>
          <div className="header-stats">
            {summary && (
              <div className="mini-stats">
                <span className="mini-stat">
                  <strong>{summary.total_records || 0}</strong> Records
                </span>
                <span className="mini-stat flagged">
                  <strong>{summary.by_status?.FLAGGED || 0}</strong> Need Review
                </span>
                <span className="mini-stat approved">
                  <strong>{summary.by_status?.APPROVED || 0}</strong> Approved
                </span>
              </div>
            )}
          </div>
        </div>
      </header>

      {notification && (
        <div className={`notification notification-${notificationType}`}>
          <div className="notification-content">
            {notification}
          </div>
          <button 
            className="close-notification"
            onClick={() => setNotification('')}
          >
            ✕
          </button>
        </div>
      )}

      <main className="container">
        <section className="section upload-section">
          <FileUpload 
            onUploadSuccess={handleUploadSuccess}
            onError={handleUploadError}
          />
        </section>

        <section className="section dashboard-section">
          {loading ? (
            <div className="loading-spinner">
              <p>Loading dashboard...</p>
            </div>
          ) : (
            <Dashboard summary={summary} />
          )}
        </section>

        <section className="section records-section">
          {loading ? (
            <div className="loading-spinner">
              <p>Loading records...</p>
            </div>
          ) : (
            <RecordsTable 
              records={records}
              onRecordUpdate={handleRecordUpdate}
              onAuditClick={handleAuditClick}
            />
          )}
        </section>
      </main>

      {showEditModal && selectedRecord && (
        <EditRecord 
          record={selectedRecord}
          onClose={() => setShowEditModal(false)}
          onSave={handleRecordSave}
        />
      )}

      {showAuditModal && selectedAuditRecord && (
        <AuditTrail 
          record={selectedAuditRecord}
          onClose={() => setShowAuditModal(false)}
        />
      )}

      <footer className="footer">
        <p>Breadth ESG Dashboard • Track, Analyze, Report Emissions Data</p>
      </footer>
    </div>
  )
}

export default App
