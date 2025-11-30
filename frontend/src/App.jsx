import { useEffect, useState } from 'react';
import './App.css';
import AuditRunner from './components/AuditRunner';
import Dashboard from './components/Dashboard';
import ExportPanel from './components/ExportPanel';
import GitHubConnect from './components/GitHubConnect';
import PRReviews from './components/PRReviews';
import Pricing from './components/Pricing';

// Use relative URLs in production, localhost only for development
const API_URL = import.meta.env.VITE_API_URL || '';

function App() {
  const [activeTab, setActiveTab] = useState('reviews');
  const [apiStatus, setApiStatus] = useState(null);
  const [auditResults, setAuditResults] = useState(null);
  const [isConnected, setIsConnected] = useState(true); // Demo: assume connected

  useEffect(() => {
    // Check API health
    fetch(`${API_URL}/api/health`)
      .then((res) => res.json())
      .then((data) => setApiStatus(data))
      .catch((err) => console.error('API health check failed:', err));
  }, []);

  const handleSelectPlan = (planId) => {
    console.log('Selected plan:', planId);
    // Future: Implement Stripe checkout
    alert(`Starting checkout for ${planId} plan...`);
  };

  return (
    <div className='app'>
      <header className='app-header' role='banner'>
        <div className='header-brand'>
          <h1>🔍 OmniAudit</h1>
          <span className='header-tagline'>AI-Powered Code Review</span>
        </div>
        <div className='header-actions'>
          <div className='api-status' role='status' aria-live='polite'>
            {apiStatus ? (
              <span className='status-badge status-healthy' aria-label='API status healthy'>
                ✓ Connected
              </span>
            ) : (
              <span className='status-badge status-unknown' aria-label='Checking API status'>
                ⏳ Connecting...
              </span>
            )}
          </div>
          <button type='button' className='btn btn-small' onClick={() => setActiveTab('pricing')}>
            Upgrade
          </button>
        </div>
      </header>

      <nav className='app-nav' role='navigation' aria-label='Main navigation'>
        <button
          type='button'
          className={activeTab === 'reviews' ? 'active' : ''}
          onClick={() => setActiveTab('reviews')}
          aria-current={activeTab === 'reviews' ? 'page' : undefined}
        >
          🔍 PR Reviews
        </button>
        <button
          type='button'
          className={activeTab === 'dashboard' ? 'active' : ''}
          onClick={() => setActiveTab('dashboard')}
          aria-current={activeTab === 'dashboard' ? 'page' : undefined}
        >
          📊 Dashboard
        </button>
        <button
          type='button'
          className={activeTab === 'audit' ? 'active' : ''}
          onClick={() => setActiveTab('audit')}
          aria-current={activeTab === 'audit' ? 'page' : undefined}
        >
          🚀 Run Audit
        </button>
        <button
          type='button'
          className={activeTab === 'connect' ? 'active' : ''}
          onClick={() => setActiveTab('connect')}
          aria-current={activeTab === 'connect' ? 'page' : undefined}
        >
          🔗 Connect
        </button>
        <button
          type='button'
          className={activeTab === 'skills' ? 'active' : ''}
          onClick={() => setActiveTab('skills')}
          aria-current={activeTab === 'skills' ? 'page' : undefined}
        >
          🎯 Skills
        </button>
        <button
          type='button'
          className={activeTab === 'pricing' ? 'active' : ''}
          onClick={() => setActiveTab('pricing')}
          aria-current={activeTab === 'pricing' ? 'page' : undefined}
        >
          💎 Pricing
        </button>
      </nav>

      <main className='app-main' role='main' aria-label='Main content'>
        {activeTab === 'reviews' && <PRReviews apiUrl={API_URL} />}
        {activeTab === 'dashboard' && <Dashboard apiUrl={API_URL} auditResults={auditResults} />}
        {activeTab === 'audit' && <AuditRunner apiUrl={API_URL} onComplete={setAuditResults} />}
        {activeTab === 'connect' && (
          <GitHubConnect apiUrl={API_URL} onConnect={() => setIsConnected(true)} />
        )}
        {activeTab === 'skills' && <ExportPanel apiUrl={API_URL} />}
        {activeTab === 'pricing' && <Pricing onSelectPlan={handleSelectPlan} />}
      </main>

      <footer className='app-footer' role='contentinfo'>
        <div className='footer-main'>
          <p>
            <strong>OmniAudit</strong> - AI-Powered Code Review Platform
          </p>
          <p style={{ fontSize: '0.85rem', marginTop: '0.5rem', opacity: 0.8 }}>
            Catch bugs, security issues, and performance problems before they reach production.
          </p>
        </div>
        <div className='footer-links'>
          <a href='https://github.com/ehudso7/OmniAudit' target='_blank' rel='noopener noreferrer'>
            GitHub
          </a>
          <a href='#docs'>Documentation</a>
          <a href='#api'>API</a>
          <a href='#support'>Support</a>
        </div>
        <div className='footer-copyright'>
          <p>© 2025 OmniAudit. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
