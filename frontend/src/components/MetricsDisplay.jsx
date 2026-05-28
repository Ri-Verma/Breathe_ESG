import React, { useState } from 'react'

function RecordsTable({ records, onRecordUpdate, onAuditClick }) {
  const [filters, setFilters] = useState({ status: '', scope: '', category: '' })
  const [sortBy, setSortBy] = useState('id')

  const filteredRecords = records.filter(r => {
    return (!filters.status || r.status === filters.status) &&
           (!filters.scope || r.scope === filters.scope) &&
           (!filters.category || r.category === filters.category)
  })

  const sortedRecords = [...filteredRecords].sort((a, b) => {
    if (sortBy === 'id') return b.id - a.id
    if (sortBy === 'status') return a.status.localeCompare(b.status)
    if (sortBy === 'value') return b.normalized_value - a.normalized_value
    return 0
  })

  const statusColors = {
    'PENDING': '#95a5a6',
    'FLAGGED': '#f39c12',
    'APPROVED': '#27ae60'
  }

  const scopeLabels = {
    '1': 'Scope 1 (Direct)',
    '2': 'Scope 2 (Indirect)',
    '3': 'Scope 3 (Value Chain)'
  }

  return (
    <div className="records-table-container">
      <h2> Emission Records</h2>
      <p className="subtitle">Review and manage your emissions data</p>

      <div className="filters-section">
        <h3>Filter Results</h3>
        <div className="filters-grid">
          <div className="filter-group">
            <label>Status:</label>
            <select value={filters.status} onChange={(e) => setFilters({...filters, status: e.target.value})}>
              <option value="">All Statuses</option>
              <option value="PENDING"> Pending Review</option>
              <option value="FLAGGED"> Needs Review</option>
              <option value="APPROVED"> Approved</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Scope:</label>
            <select value={filters.scope} onChange={(e) => setFilters({...filters, scope: e.target.value})}>
              <option value="">All Scopes</option>
              <option value="1">Scope 1 (Direct Emissions)</option>
              <option value="2">Scope 2 (Electricity)</option>
              <option value="3">Scope 3 (Travel)</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Category:</label>
            <select value={filters.category} onChange={(e) => setFilters({...filters, category: e.target.value})}>
              <option value="">All Categories</option>
              <option value="Fuel"> Fuel</option>
              <option value="Electricity"> Electricity</option>
              <option value="Travel">✈️ Travel</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Sort By:</label>
            <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
              <option value="id">Newest First</option>
              <option value="status">By Status</option>
              <option value="value">Highest Emissions</option>
            </select>
          </div>
        </div>
      </div>

      <div className="records-count">
        Showing {sortedRecords.length} of {records.length} records
      </div>

      <div className="table-wrapper">
        {sortedRecords.length > 0 ? (
          <table className="records-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Category</th>
                <th>Scope</th>
                <th>Original Value</th>
                <th>Emissions (kg CO2e)</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {sortedRecords.map(record => (
                <tr key={record.id} className={`row-${record.status.toLowerCase()}`}>
                  <td><strong>#{record.id}</strong></td>
                  <td>{record.category}</td>
                  <td>
                    <span className="scope-badge">Scope {record.scope}</span>
                  </td>
                  <td>
                    {record.original_value} {record.original_unit}
                  </td>
                  <td className="emissions-value">
                    {record.normalized_value.toFixed(2)}
                  </td>
                  <td>
                    <span 
                      className="status-badge" 
                      style={{ backgroundColor: statusColors[record.status] }}
                    >
                      {record.status}
                    </span>
                  </td>
                  <td className="actions-cell">
                    {record.status === 'FLAGGED' && (
                      <button 
                        className="btn btn-small btn-edit"
                        onClick={() => onRecordUpdate(record)}
                        title="Edit this record"
                      >
                         Fix
                      </button>
                    )}
                    {record.status === 'PENDING' && (
                      <button 
                        className="btn btn-small btn-approve"
                        onClick={() => onRecordUpdate(record)}
                        title="Approve this record"
                      >
                         Review
                      </button>
                    )}
                    <button 
                      className="btn btn-small btn-info"
                      onClick={() => onAuditClick(record)}
                      title="View audit history"
                    >
                       History
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="empty-state">
            <p>No records found. Try uploading a file to get started!</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default RecordsTable
