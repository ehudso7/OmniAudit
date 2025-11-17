import { useState } from 'react'

function ExportPanel({ apiUrl, auditResults }) {
  const [loading, setLoading] = useState(false)
  const [format, setFormat] = useState('csv')

  const exportData = async (exportFormat) => {
    if (!auditResults) {
      alert('No audit results available. Please run an audit first.')
      return
    }

    setLoading(true)

    try {
      const response = await fetch(`${apiUrl}/api/v1/export/${exportFormat}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          data: auditResults.results
        })
      })

      if (!response.ok) {
        throw new Error(`Export failed: ${response.status}`)
      }

      // Download file
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `audit_report.${exportFormat === 'markdown' ? 'md' : exportFormat}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      alert(`Export failed: ${err.message}`)
      console.error('Export failed:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="export-panel">
      <h2>Export Results</h2>

      {!auditResults && (
        <div className="info-message">
          ℹ️ No audit results available. Please run an audit first.
        </div>
      )}

      {auditResults && (
        <div className="export-options">
          <h3>Select Export Format</h3>

          <div className="format-cards">
            <div className="format-card">
              <h4>📊 CSV</h4>
              <p>Comma-separated values for spreadsheets</p>
              <button
                className="btn btn-secondary"
                onClick={() => exportData('csv')}
                disabled={loading}
              >
                Export CSV
              </button>
            </div>

            <div className="format-card">
              <h4>📝 Markdown</h4>
              <p>Human-readable formatted report</p>
              <button
                className="btn btn-secondary"
                onClick={() => exportData('markdown')}
                disabled={loading}
              >
                Export Markdown
              </button>
            </div>

            <div className="format-card">
              <h4>📦 JSON</h4>
              <p>Structured data for programmatic use</p>
              <button
                className="btn btn-secondary"
                onClick={() => exportData('json')}
                disabled={loading}
              >
                Export JSON
              </button>
            </div>
          </div>

          {loading && (
            <div className="loading-message">
              ⏳ Generating export...
            </div>
          )}

          <div className="audit-preview">
            <h3>Current Audit Results</h3>
            <div className="preview-stats">
              <p><strong>Audit ID:</strong> {auditResults.audit_id}</p>
              <p><strong>Status:</strong> {auditResults.success ? '✅ Success' : '❌ Failed'}</p>
              <p><strong>Collectors:</strong> {Object.keys(auditResults.results?.collectors || {}).length}</p>
              <p><strong>Analyzers:</strong> {Object.keys(auditResults.results?.analyzers || {}).length}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ExportPanel
