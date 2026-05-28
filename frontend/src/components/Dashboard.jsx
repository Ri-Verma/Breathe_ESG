import React from 'react'

function Dashboard({ summary }) {
  if (!summary) {
    return <div className="dashboard-container"><p>Loading dashboard...</p></div>
  }

  const stats = [
    {
      icon: '📊',
      label: 'Total Records',
      value: summary.total_records || 0,
      color: '#3498db'
    },
    {
      icon: '⚠️',
      label: 'Needs Review',
      value: summary.by_status?.FLAGGED || 0,
      color: '#f39c12'
    },
    {
      icon: '✅',
      label: 'Approved',
      value: summary.by_status?.APPROVED || 0,
      color: '#27ae60'
    },
    {
      icon: '⏳',
      label: 'Pending',
      value: summary.by_status?.PENDING || 0,
      color: '#95a5a6'
    }
  ]

  return (
    <div className="dashboard-container">
      <h2>📈 Dashboard Overview</h2>
      <p className="subtitle">Quick summary of your emissions data</p>
      
      <div className="stats-grid">
        {stats.map((stat, idx) => (
          <div key={idx} className="stat-card" style={{ borderLeftColor: stat.color }}>
            <div className="stat-icon">{stat.icon}</div>
            <div className="stat-content">
              <h3>{stat.label}</h3>
              <p className="stat-value">{stat.value.toLocaleString()}</p>
            </div>
          </div>
        ))}
      </div>

      {summary.by_scope && (
        <div className="scope-breakdown">
          <h3>Emissions by Scope</h3>
          <div className="scope-bars">
            {Object.entries(summary.by_scope).map(([scope, count]) => (
              <div key={scope} className="scope-bar">
                <label>Scope {scope}</label>
                <div className="bar-background">
                  <div 
                    className="bar-fill"
                    style={{ width: `${(count / (summary.total_records || 1)) * 100}%` }}
                  >
                    {count}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard
