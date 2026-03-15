import { useCallback, useEffect, useState } from 'react';
import './App.css';
import AuditRunner from './components/AuditRunner';
import BrowserAuditRunner from './components/BrowserAuditRunner';
import Dashboard from './components/Dashboard';
import ExportPanel from './components/ExportPanel';
import GitHubConnect from './components/GitHubConnect';
import PRReviews from './components/PRReviews';
import Pricing from './components/Pricing';
import Settings from './components/Settings';
import Onboarding from './components/Onboarding';

const API_URL = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '');

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [apiStatus, setApiStatus] = useState(null);
  const [auditResults, setAuditResults] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [auditMode, setAuditMode] = useState('code');

  // Auth state
  const [user, setUser] = useState(null);
  const [authToken, setAuthToken] = useState(() => localStorage.getItem('omniaudit_token'));
  const [showAuth, setShowAuth] = useState(false);
  const [authMode, setAuthMode] = useState('login');
  const [authEmail, setAuthEmail] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authError, setAuthError] = useState('');
  const [authLoading, setAuthLoading] = useState(false);

  // Notifications
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showNotifications, setShowNotifications] = useState(false);

  // Onboarding
  const [showOnboarding, setShowOnboarding] = useState(false);

  useEffect(() => {
    fetch(`${API_URL}/api/health`)
      .then((res) => res.json())
      .then((data) => setApiStatus(data))
      .catch(() => setApiStatus({ status: 'unavailable' }));
  }, []);

  // Load user from token
  useEffect(() => {
    if (!authToken) return;
    fetch(`${API_URL}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${authToken}` },
    })
      .then(res => {
        if (!res.ok) throw new Error('Invalid token');
        return res.json();
      })
      .then(data => setUser(data.user))
      .catch(() => {
        localStorage.removeItem('omniaudit_token');
        setAuthToken(null);
      });
  }, [authToken]);

  // Load notifications
  const loadNotifications = useCallback(() => {
    const headers = authToken ? { Authorization: `Bearer ${authToken}` } : {};
    fetch(`${API_URL}/api/v1/notifications?limit=10`, { headers })
      .then(res => res.ok ? res.json() : null)
      .then(data => {
        if (data) {
          setNotifications(data.notifications || []);
          setUnreadCount(data.unread || 0);
        }
      })
      .catch(() => {});
  }, [authToken]);

  useEffect(() => {
    loadNotifications();
    const interval = setInterval(loadNotifications, 30000);
    return () => clearInterval(interval);
  }, [loadNotifications]);

  // Check if first-time user (server-side flag takes precedence, fallback to localStorage)
  useEffect(() => {
    if (user && !user.onboarding_completed && !localStorage.getItem('omniaudit_onboarded')) {
      setShowOnboarding(true);
    }
  }, [user]);

  const handleAuth = async (e) => {
    e.preventDefault();
    setAuthLoading(true);
    setAuthError('');

    const endpoint = authMode === 'login' ? '/api/v1/auth/login' : '/api/v1/auth/register';
    try {
      const res = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: authEmail, password: authPassword }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Authentication failed');

      localStorage.setItem('omniaudit_token', data.token);
      setAuthToken(data.token);
      setUser(data.user);
      setShowAuth(false);
      setAuthEmail('');
      setAuthPassword('');
    } catch (err) {
      setAuthError(err.message);
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('omniaudit_token');
    setAuthToken(null);
    setUser(null);
  };

  const handleSelectPlan = (planId) => {
    console.log('Selected plan:', planId);
  };

  const markNotificationRead = async (id) => {
    await fetch(`${API_URL}/api/v1/notifications/${id}/read`, { method: 'POST' }).catch(() => {});
    loadNotifications();
  };

  const completeOnboarding = () => {
    localStorage.setItem('omniaudit_onboarded', 'true');
    setShowOnboarding(false);
  };

  // Auth modal
  if (showAuth) {
    return (
      <div className='app'>
        <div className='auth-overlay'>
          <div className='auth-modal'>
            <h2>{authMode === 'login' ? 'Sign In' : 'Create Account'}</h2>
            <form onSubmit={handleAuth}>
              <div className='form-group'>
                <label htmlFor='auth-email'>Email</label>
                <input id='auth-email' type='email' value={authEmail} onChange={e => setAuthEmail(e.target.value)} required autoComplete='email' />
              </div>
              <div className='form-group'>
                <label htmlFor='auth-password'>Password</label>
                <input id='auth-password' type='password' value={authPassword} onChange={e => setAuthPassword(e.target.value)} required minLength={8} autoComplete={authMode === 'login' ? 'current-password' : 'new-password'} />
              </div>
              {authError && <div className='error-message'><p>{authError}</p></div>}
              <button type='submit' className='btn btn-primary btn-large' disabled={authLoading}>
                {authLoading ? 'Processing...' : authMode === 'login' ? 'Sign In' : 'Create Account'}
              </button>
            </form>
            <p style={{ marginTop: '1rem', textAlign: 'center', fontSize: '0.85rem' }}>
              {authMode === 'login' ? (
                <>No account? <button type='button' className='link-btn' onClick={() => { setAuthMode('register'); setAuthError(''); }}>Create one</button></>
              ) : (
                <>Have an account? <button type='button' className='link-btn' onClick={() => { setAuthMode('login'); setAuthError(''); }}>Sign in</button></>
              )}
            </p>
            <button type='button' className='link-btn' style={{ marginTop: '0.5rem', display: 'block', textAlign: 'center', width: '100%' }} onClick={() => setShowAuth(false)}>
              Continue without signing in
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Onboarding
  if (showOnboarding) {
    return (
      <div className='app'>
        <Onboarding
          apiUrl={API_URL}
          authToken={authToken}
          onComplete={completeOnboarding}
          onNavigate={(tab) => { completeOnboarding(); setActiveTab(tab); }}
        />
      </div>
    );
  }

  return (
    <div className='app'>
      <header className='app-header'>
        <div className='header-brand'>
          <h1>OmniAudit</h1>
          <span className='header-tagline'>AI-Powered Code & Browser Verification</span>
        </div>
        <div className='header-actions'>
          <div className='api-status' role='status' aria-live='polite'>
            {apiStatus?.status === 'unavailable' ? (
              <span className='status-badge status-offline' aria-label='API unavailable'>Demo Mode</span>
            ) : apiStatus ? (
              <span className='status-badge status-healthy' aria-label='API status healthy'>Connected</span>
            ) : (
              <span className='status-badge status-unknown' aria-label='Checking API status'>Connecting...</span>
            )}
          </div>

          {/* Notifications bell */}
          <div className='notifications-wrapper'>
            <button type='button' className='btn btn-small notification-btn' onClick={() => setShowNotifications(!showNotifications)}>
              Notifications {unreadCount > 0 && <span className='notification-badge'>{unreadCount}</span>}
            </button>
            {showNotifications && (
              <div className='notifications-dropdown'>
                <div className='notifications-header'>
                  <strong>Notifications</strong>
                  {unreadCount > 0 && (
                    <button type='button' className='link-btn' onClick={() => {
                      fetch(`${API_URL}/api/v1/notifications/read-all`, { method: 'POST' }).then(loadNotifications);
                    }}>Mark all read</button>
                  )}
                </div>
                {notifications.length === 0 ? (
                  <p className='notifications-empty'>No notifications yet</p>
                ) : (
                  notifications.map(n => (
                    <div key={n.id} className={`notification-item ${n.read ? '' : 'unread'} severity-${n.severity}`}
                      onClick={() => markNotificationRead(n.id)}>
                      <div className='notification-title'>{n.title}</div>
                      <div className='notification-message'>{n.message}</div>
                      <div className='notification-time'>{n.created_at ? new Date(n.created_at).toLocaleString() : ''}</div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          {user ? (
            <div className='user-menu'>
              <span className='user-name'>{user.display_name || user.email}</span>
              <button type='button' className='btn btn-small' onClick={handleLogout}>Sign Out</button>
            </div>
          ) : (
            <button type='button' className='btn btn-small' onClick={() => setShowAuth(true)}>Sign In</button>
          )}
        </div>
      </header>

      <nav className='app-nav' aria-label='Main navigation'>
        {['dashboard', 'reviews', 'audit', 'connect', 'settings', 'pricing'].map(tab => (
          <button
            key={tab}
            type='button'
            className={activeTab === tab ? 'active' : ''}
            onClick={() => setActiveTab(tab)}
            aria-current={activeTab === tab ? 'page' : undefined}
          >
            {tab === 'reviews' ? 'PR Reviews' : tab === 'audit' ? 'Run Audit' : tab === 'connect' ? (isConnected ? 'Connected' : 'Connect') : tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </nav>

      <main className='app-main' aria-label='Main content'>
        {activeTab === 'dashboard' && <Dashboard apiUrl={API_URL} auditResults={auditResults} />}
        {activeTab === 'reviews' && <PRReviews apiUrl={API_URL} />}
        {activeTab === 'audit' && (
          <div className='audit-container'>
            <div className='audit-mode-tabs'>
              <button type='button' className={`mode-tab ${auditMode === 'code' ? 'active' : ''}`} onClick={() => setAuditMode('code')}>Code Analysis</button>
              <button type='button' className={`mode-tab ${auditMode === 'browser' ? 'active' : ''}`} onClick={() => setAuditMode('browser')}>Browser Verification</button>
            </div>
            {auditMode === 'code' ? (
              <AuditRunner apiUrl={API_URL} onComplete={setAuditResults} />
            ) : (
              <BrowserAuditRunner apiUrl={API_URL} onComplete={setAuditResults} />
            )}
          </div>
        )}
        {activeTab === 'connect' && (
          <GitHubConnect apiUrl={API_URL} onConnect={() => setIsConnected(true)} />
        )}
        {activeTab === 'settings' && <Settings apiUrl={API_URL} authToken={authToken} user={user} />}
        {activeTab === 'pricing' && <Pricing onSelectPlan={handleSelectPlan} />}
      </main>

      <footer className='app-footer' role='contentinfo'>
        <div className='footer-main'>
          <p><strong>OmniAudit</strong> - AI-Powered Code & Browser Verification Platform</p>
          <p style={{ fontSize: '0.85rem', marginTop: '0.5rem', opacity: 0.8 }}>
            Catch bugs, security issues, and performance problems before they reach production.
          </p>
        </div>
        <div className='footer-links'>
          <a href='https://github.com/ehudso7/OmniAudit' target='_blank' rel='noopener noreferrer'>GitHub</a>
          <a href='#docs'>Documentation</a>
          <a href='#api'>API</a>
          <a href='#support'>Support</a>
        </div>
        <div className='footer-copyright'>
          <p>&copy; 2026 OmniAudit. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
