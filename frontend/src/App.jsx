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
      <header className="app-header" role="banner">
        <h1>🔍 OmniAudit Dashboard</h1>
        <div className="api-status" role="status" aria-live="polite">
          {apiStatus ? (
            <span className="status-badge status-healthy" aria-label="API status healthy">
              ✓ API Healthy
            </span>
          ) : (
            <span className="status-badge status-unknown" aria-label="Checking API status">
              ⏳ Checking...
            </span>
          )}
        </div>
      </header>

      <nav className="app-nav" role="navigation" aria-label="Main navigation">
        <button
          className={activeTab === 'dashboard' ? 'active' : ''}
          onClick={() => setActiveTab('dashboard')}
          aria-label="Dashboard"
          aria-current={activeTab === 'dashboard' ? 'page' : undefined}
        >
          📊 Dashboard
        </button>
        <button
          className={activeTab === 'audit' ? 'active' : ''}
          onClick={() => setActiveTab('audit')}
          aria-label="Run code analysis"
          aria-current={activeTab === 'audit' ? 'page' : undefined}
        >
          🚀 Run Audit
        </button>
        <button
          className={activeTab === 'skills' ? 'active' : ''}
          onClick={() => setActiveTab('skills')}
          aria-label="Browse skills"
          aria-current={activeTab === 'skills' ? 'page' : undefined}
        >
          🎯 Skills
        </button>
      </nav>

      <main className="app-main" role="main" aria-label="Main content">
        {activeTab === 'dashboard' && (
          <Dashboard apiUrl={API_URL} auditResults={auditResults} />
        )}
        {activeTab === 'audit' && (
          <AuditRunner apiUrl={API_URL} onComplete={setAuditResults} />
        )}
        {activeTab === 'skills' && (
          <ExportPanel apiUrl={API_URL} />
        )}
      </main>

      <footer className="app-footer" role="contentinfo">
        <p>OmniAudit v0.3.0 | Universal AI Code Analysis & Optimization</p>
        <p style={{ fontSize: '0.85rem', marginTop: '0.5rem', opacity: 0.8 }}>
          Powered by Claude Sonnet 4.5 | <a href="https://github.com/ehudso7/OmniAudit" target="_blank" rel="noopener noreferrer" style={{ color: 'inherit' }}>GitHub</a>
        </p>
      </footer>
    </div>
  )
}

export default App
