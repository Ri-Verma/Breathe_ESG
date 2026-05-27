import React, { useState } from 'react'

function FileUpload({ onUpload, loading }) {
  const [dragging, setDragging] = useState(false)

  const handleDragOver = (e) => {
    e.preventDefault()
    setDragging(true)
  }

  const handleDragLeave = () => {
    setDragging(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    
    const files = e.dataTransfer.files
    if (files.length > 0) {
      onUpload(files[0])
    }
  }

  const handleFileSelect = (e) => {
    const files = e.target.files
    if (files.length > 0) {
      onUpload(files[0])
    }
  }

  return (
    <div 
      className={`file-upload ${dragging ? 'dragging' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <h2>Upload ESG Data</h2>
      <p>Drag and drop your CSV, Excel, or JSON file here</p>
      <input 
        type="file" 
        id="fileInput" 
        onChange={handleFileSelect}
        disabled={loading}
        accept=".csv,.xlsx,.json"
      />
      <label htmlFor="fileInput">
        {loading ? 'Uploading...' : 'Select File'}
      </label>
    </div>
  )
}

export default FileUpload
