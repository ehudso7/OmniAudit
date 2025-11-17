import { useState } from 'react'

function AuditRunner({ apiUrl, onComplete }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [config, setConfig] = useState({
    repoPath: '.',
    maxCommits: 50
  })

  const runAudit = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${apiUrl}/api/v1/audit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          collectors: {
            git_collector: {
              repo_path: config.repoPath,
              max_commits: parseInt(config.maxCommits)
            }
          }
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      onComplete(data)
      setError(null)
    } catch (err) {
      setError(err.message)
      console.error('Audit failed:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="audit-runner">
      <h2>Run Audit</h2>

      <div className="form">
        <div className="form-group">
          <label htmlFor="repoPath">Repository Path</label>
          <input
            id="repoPath"
            type="text"
            value={config.repoPath}
            onChange={(e) => setConfig({ ...config, repoPath: e.target.value })}
            placeholder="."
            disabled
          />
          <small>Note: In the deployed API, this should be a valid repository path</small>
        </div>

        <div className="form-group">
          <label htmlFor="maxCommits">Max Commits</label>
          <input
            id="maxCommits"
            type="number"
            value={config.maxCommits}
            onChange={(e) => setConfig({ ...config, maxCommits: e.target.value })}
            min="1"
            max="1000"
          />
        </div>

        <button
          className="btn btn-primary"
          onClick={runAudit}
          disabled={loading}
        >
          {loading ? '🔄 Running Audit...' : '🚀 Run Audit'}
        </button>

        {error && (
          <div className="error-message">
            ❌ Error: {error}
          </div>
        )}

        {!error && !loading && (
          <div className="info-message">
            💡 Tip: This will run a Git audit on the repository configured in the API.
            For local testing, ensure the API has access to a valid Git repository.
          </div>
        )}
      </div>
    </div>
  )
}

export default AuditRunner
