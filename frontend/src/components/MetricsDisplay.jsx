import React from 'react'

function MetricsDisplay({ metrics }) {
  const groupedMetrics = {
    environmental: metrics.filter(m => m.category === 'environmental'),
    social: metrics.filter(m => m.category === 'social'),
    governance: metrics.filter(m => m.category === 'governance'),
  }

  const renderCategory = (category, label) => (
    <div key={category} className="metrics-category">
      <h3>{label}</h3>
      {groupedMetrics[category].length > 0 ? (
        <div className="metrics-grid">
          {groupedMetrics[category].map((metric) => (
            <div key={metric.id} className="metric-card">
              <div className="metric-name">{metric.metric_name}</div>
              <div className="metric-value">
                {metric.value} {metric.unit}
              </div>
              <div className="metric-date">
                {new Date(metric.date).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="no-data">No {label.toLowerCase()} metrics yet</p>
      )}
    </div>
  )

  return (
    <div className="metrics-display">
      <h2>ESG Metrics</h2>
      {metrics.length > 0 ? (
        <div>
          {renderCategory('environmental', 'Environmental')}
          {renderCategory('social', 'Social')}
          {renderCategory('governance', 'Governance')}
        </div>
      ) : (
        <p className="no-data">No metrics available. Upload a file to get started.</p>
      )}
    </div>
  )
}

export default MetricsDisplay
