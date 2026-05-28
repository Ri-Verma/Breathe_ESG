import React, { useState } from 'react'
import axios from 'axios'

function EditRecord({ record, onClose, onSave }) {
  const [formData, setFormData] = useState({
    normalized_value: record.normalized_value,
    status: record.status,
    notes: record.notes || ''
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData({
      ...formData,
      [name]: name === 'normalized_value' ? parseFloat(value) || 0 : value
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')

    try {
      const response = await axios.patch(`/api/emissions/${record.id}/`, formData)
      onSave(response.data)
      onClose()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save record')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>✏️ Review Emission Record</h2>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          <div className="record-info">
            <div className="info-group">
              <label>Record ID:</label>
              <p>#{record.id}</p>
            </div>
            <div className="info-group">
              <label>Category:</label>
              <p>{record.category}</p>
            </div>
            <div className="info-group">
              <label>Scope:</label>
              <p>Scope {record.scope}</p>
            </div>
            <div className="info-group">
              <label>Original Value:</label>
              <p>{record.original_value} {record.original_unit}</p>
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}

          <form onSubmit={handleSubmit} className="edit-form">
            <div className="form-group">
              <label htmlFor="normalized_value">
                Emissions (kg CO2e) <span className="required">*</span>
              </label>
              <input
                type="number"
                id="normalized_value"
                name="normalized_value"
                value={formData.normalized_value}
                onChange={handleChange}
                step="0.01"
                required
                placeholder="Enter emissions value"
              />
              <p className="helper-text">Current normalized value in kg CO2e</p>
            </div>

            <div className="form-group">
              <label htmlFor="status">
                Status <span className="required">*</span>
              </label>
              <select
                id="status"
                name="status"
                value={formData.status}
                onChange={handleChange}
              >
                <option value="PENDING">⏳ Pending Review</option>
                <option value="FLAGGED">⚠️ Needs Review</option>
                <option value="APPROVED">✅ Approved</option>
              </select>
              <p className="helper-text">
                {formData.status === 'APPROVED' ? '🔒 Approved records cannot be edited later' : ''}
              </p>
            </div>

            <div className="form-group">
              <label htmlFor="notes">
                Notes (Optional)
              </label>
              <textarea
                id="notes"
                name="notes"
                value={formData.notes}
                onChange={handleChange}
                placeholder="Add notes about this record..."
                rows={3}
              />
              <p className="helper-text">Internal notes for your team</p>
            </div>

            <div className="form-actions">
              <button type="button" className="btn btn-secondary" onClick={onClose}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary" disabled={saving}>
                {saving ? '💾 Saving...' : '💾 Save Changes'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default EditRecord
