import { useState, useEffect } from 'react'

function Dashboard({ apiUrl, auditResults }) {
  const [collectors, setCollectors] = useState([])

  useEffect(() => {
    // Fetch available collectors
    fetch(`${apiUrl}/api/v1/collectors`)
      .then(res => res.json())
      .then(data => setCollectors(data.collectors || []))
      .catch(err => console.error('Failed to fetch collectors:', err))
  }, [apiUrl])

  return (
    <div className="dashboard">
      <h2>Dashboard Overview</h2>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">📦</div>
          <div className="stat-content">
            <h3>Available Collectors</h3>
            <p className="stat-value">{collectors.length}</p>
          </div>
        </div>

        {auditResults && (
          <>
            <div className="stat-card">
              <div className="stat-icon">✅</div>
              <div className="stat-content">
                <h3>Last Audit</h3>
                <p className="stat-value">Success</p>
              </div>
            </div>

            {auditResults.results?.collectors?.git_collector && (
              <>
                <div className="stat-card">
                  <div className="stat-icon">💻</div>
                  <div className="stat-content">
                    <h3>Total Commits</h3>
                    <p className="stat-value">
                      {auditResults.results.collectors.git_collector.data?.commits_count || 0}
                    </p>
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-icon">👥</div>
                  <div className="stat-content">
                    <h3>Contributors</h3>
                    <p className="stat-value">
                      {auditResults.results.collectors.git_collector.data?.contributors_count || 0}
                    </p>
                  </div>
                </div>
              </>
            )}
          </>
        )}
      </div>

      <div className="section">
        <h3>Available Collectors</h3>
        <div className="collector-list">
          {collectors.map((collector, idx) => (
            <div key={idx} className="collector-card">
              <div className="collector-name">{collector.name}</div>
              <div className="collector-version">v{collector.version}</div>
            </div>
          ))}
        </div>
      </div>

      {auditResults && auditResults.results?.collectors?.git_collector && (
        <div className="section">
          <h3>Latest Audit Results</h3>
          <div className="audit-summary">
            <h4>Git Repository Analysis</h4>
            <pre>{JSON.stringify(auditResults.results.collectors.git_collector.data, null, 2)}</pre>
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard
