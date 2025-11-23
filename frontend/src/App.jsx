import { useState, useEffect } from 'react'
import './App.css'
import Dashboard from './components/Dashboard'
import AuditRunner from './components/AuditRunner'
import ExportPanel from './components/ExportPanel'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000'

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [apiStatus, setApiStatus] = useState(null)
  const [auditResults, setAuditResults] = useState(null)

  useEffect(() => {
    // Check API health - TypeScript serverless function endpoint
    fetch(`${API_URL}/api/health`)
      .then(res => res.json())
      .then(data => setApiStatus(data))
      .catch(err => console.error('API health check failed:', err))
  }, [])

  return (
    <div className="app">
      <header className="app-header">
        <h1>🔍 OmniAudit Dashboard</h1>
        <div className="api-status">
          {apiStatus ? (
            <span className="status-badge status-healthy">
              ✓ API Healthy
            </span>
          ) : (
            <span className="status-badge status-unknown">
              ⚠ Checking...
            </span>
          )}
        </div>
      </header>

      <nav className="app-nav">
        <button
          className={activeTab === 'dashboard' ? 'active' : ''}
          onClick={() => setActiveTab('dashboard')}
        >
          📊 Dashboard
        </button>
        <button
          className={activeTab === 'audit' ? 'active' : ''}
          onClick={() => setActiveTab('audit')}
        >
          🚀 Run Audit
        </button>
        <button
          className={activeTab === 'skills' ? 'active' : ''}
          onClick={() => setActiveTab('skills')}
        >
          🎯 Skills
        </button>
      </nav>

      <main className="app-main">
        {activeTab === 'dashboard' && (
          <Dashboard apiUrl={API_URL} auditResults={auditResults} />
        )}
        {activeTab === 'audit' && (
          <AuditRunner apiUrl={API_URL} onComplete={setAuditResults} />
        )}
        {activeTab === 'skills' && (
          <ExportPanel apiUrl={API_URL} auditResults={auditResults} />
        )}
      </main>

      <footer className="app-footer">
        <p>OmniAudit v0.3.0 | Universal Project Auditing & Monitoring</p>
      </footer>
    </div>
  )
}

export default App
