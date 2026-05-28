import React, { useState, useEffect } from 'react'
import axios from 'axios'

function AuditTrail({ record, onClose }) {
  const [auditLogs, setAuditLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchAuditLogs()
  }, [record.id])

  const fetchAuditLogs = async () => {
    try {
      const response = await axios.get(`/api/emissions/${record.id}/audit_history/`)
      setAuditLogs(response.data.results || response.data)
      setError('')
    } catch (err) {
      setError('Failed to load audit history')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString()
  }

  const getActionLabel = (action) => {
    const actions = {
      'CREATE': '➕ Created',
      'UPDATE': '✏️ Updated',
      'APPROVE': '✅ Approved',
      'FLAG': '⚠️ Flagged',
      'REJECT': '❌ Rejected'
    }
    return actions[action] || action
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>📜 Audit Trail - Record #{record.id}</h2>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body audit-body">
          {error && <div className="error-message">{error}</div>}

          {loading ? (
            <div className="loading">Loading audit history...</div>
          ) : auditLogs.length > 0 ? (
            <div className="audit-timeline">
              {auditLogs.map((log, idx) => (
                <div key={log.id} className="timeline-item">
                  <div className="timeline-marker"></div>
                  <div className="timeline-content">
                    <div className="timeline-header">
                      <h4>{getActionLabel(log.action)}</h4>
                      <span className="timeline-date">{formatDate(log.timestamp)}</span>
                    </div>
                    
                    <p className="timeline-user">By: <strong>{log.user_name || 'System'}</strong></p>

                    {log.previous_state && (
                      <div className="state-comparison">
                        <details>
                          <summary>📊 View Changes</summary>
                          <div className="state-box">
                            <h5>Previous State:</h5>
                            <pre>{JSON.stringify(log.previous_state, null, 2)}</pre>
                          </div>
                          <div className="state-box">
                            <h5>New State:</h5>
                            <pre>{JSON.stringify(log.new_state, null, 2)}</pre>
                          </div>
                        </details>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <p>No audit history available for this record</p>
            </div>
          )}

          <div className="modal-footer">
            <button className="btn btn-secondary" onClick={onClose}>
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AuditTrail
