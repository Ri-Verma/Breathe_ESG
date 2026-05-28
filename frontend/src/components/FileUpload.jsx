import React, { useState } from 'react'
import axios from 'axios'

function FileUpload({ onUploadSuccess, onError }) {
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [fileName, setFileName] = useState('')
  const [sourceType, setSourceType] = useState('SAP')

  const handleDragOver = (e) => {
    e.preventDefault()
    setDragging(true)
  }

  const handleDragLeave = () => {
    setDragging(false)
  }

  const uploadFile = async (file) => {
    setUploading(true)
    setFileName(file.name)
    
    const formData = new FormData()
    formData.append('file', file)
    formData.append('source_type', sourceType)

    try {
      const response = await axios.post('/api/upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      
      onUploadSuccess(response.data)
      setSourceType('SAP')
      setFileName('')
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Upload failed. Please try again.'
      onError(errorMsg)
      console.error('Upload error:', error)
    } finally {
      setUploading(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    
    const files = e.dataTransfer.files
    if (files.length > 0) {
      uploadFile(files[0])
    }
  }

  const handleFileSelect = (e) => {
    const files = e.target.files
    if (files.length > 0) {
      uploadFile(files[0])
    }
  }

  return (
    <div className="file-upload-container">
      <h2>📤 Upload ESG Data</h2>
      <p className="subtitle">Help us track your emissions with accurate data</p>
      
      <div className="source-selector">
        <label>Data Source Type:</label>
        <div className="radio-group">
          <label className="radio-label">
            <input 
              type="radio" 
              value="SAP" 
              checked={sourceType === 'SAP'}
              onChange={(e) => setSourceType(e.target.value)}
              disabled={uploading}
            />
            <span>🏭 SAP (Fuel & Equipment)</span>
          </label>
          <label className="radio-label">
            <input 
              type="radio" 
              value="UTILITY" 
              checked={sourceType === 'UTILITY'}
              onChange={(e) => setSourceType(e.target.value)}
              disabled={uploading}
            />
            <span>💡 Utility Bills (Electricity)</span>
          </label>
          <label className="radio-label">
            <input 
              type="radio" 
              value="TRAVEL" 
              checked={sourceType === 'TRAVEL'}
              onChange={(e) => setSourceType(e.target.value)}
              disabled={uploading}
            />
            <span>✈️ Travel Data (Business Trips)</span>
          </label>
        </div>
      </div>

      <div 
        className={`drop-zone ${dragging ? 'dragging' : ''} ${uploading ? 'uploading' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {uploading ? (
          <div className="upload-progress">
            <div className="spinner"></div>
            <p>Uploading <strong>{fileName}</strong>...</p>
            <p className="small-text">Please wait while we process your data</p>
          </div>
        ) : (
          <>
            <div className="drop-icon">📁</div>
            <h3>Drag your file here</h3>
            <p>or click to browse</p>
            <p className="file-types">Supports CSV and JSON files</p>
          </>
        )}
        <input 
          type="file" 
          id="fileInput" 
          onChange={handleFileSelect}
          disabled={uploading}
          accept=".csv,.json"
          style={{ display: 'none' }}
        />
      </div>

      <label htmlFor="fileInput" className="browse-button">
        {uploading ? 'Uploading...' : '📂 Browse Files'}
      </label>
    </div>
  )
}

export default FileUpload
