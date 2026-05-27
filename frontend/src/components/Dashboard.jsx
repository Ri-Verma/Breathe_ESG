import React from 'react'

function Dashboard({ metrics }) {
  const stats = {
    total: metrics.length,
    environmental: metrics.filter(m => m.category === 'environmental').length,
    social: metrics.filter(m => m.category === 'social').length,
    governance: metrics.filter(m => m.category === 'governance').length,
  }

  return (
    <div className="dashboard">
      <h2>Dashboard Summary</h2>
      <div className="stats-grid">
        <div className="stat-card total">
          <div className="stat-value">{stats.total}</div>
          <div className="stat-label">Total Metrics</div>
        </div>
        <div className="stat-card environmental">
          <div className="stat-value">{stats.environmental}</div>
          <div className="stat-label">Environmental</div>
        </div>
        <div className="stat-card social">
          <div className="stat-value">{stats.social}</div>
          <div className="stat-label">Social</div>
        </div>
        <div className="stat-card governance">
          <div className="stat-value">{stats.governance}</div>
          <div className="stat-label">Governance</div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
