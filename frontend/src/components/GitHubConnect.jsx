import PropTypes from 'prop-types';
import { useEffect, useState } from 'react';

const GITHUB_APP_URL = 'https://github.com/apps/omniaudit/installations/new';

function GitHubConnect({ apiUrl, onConnect }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [repositories, setRepositories] = useState([]);
  const [webhookStatus, setWebhookStatus] = useState(null);
  const [manualOwner, setManualOwner] = useState('');
  const [manualRepo, setManualRepo] = useState('');
  const [connectingManual, setConnectingManual] = useState(false);

  useEffect(() => {
    // Load connected repositories
    fetch(`${apiUrl}/api/v1/repositories`)
      .then(res => res.ok ? res.json() : null)
      .then(data => { if (data) setRepositories(data.repositories || []); })
      .catch(() => {});

    // Check webhook status
    fetch(`${apiUrl}/api/v1/webhooks/status`)
      .then(res => res.ok ? res.json() : null)
      .then(data => { if (data) setWebhookStatus(data); })
      .catch(() => {});
  }, [apiUrl]);

  const handleInstallApp = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiUrl}/api/v1/webhooks/status`);
      if (response.ok) {
        onConnect?.();
      }
    } catch (_err) {
      // Continue to redirect regardless
    }

    window.location.href = GITHUB_APP_URL;
  };

  const handleManualConnect = async () => {
    if (!manualOwner.trim() || !manualRepo.trim()) {
      setError('Please enter both owner and repository name');
      return;
    }

    setConnectingManual(true);
    setError(null);

    try {
      const res = await fetch(`${apiUrl}/api/v1/repositories/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ owner: manualOwner.trim(), repo: manualRepo.trim() }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to connect repository');
      }

      const data = await res.json();
      setRepositories(prev => [...prev, data.repository]);
      setManualOwner('');
      setManualRepo('');
      onConnect?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setConnectingManual(false);
    }
  };

  const handleDisconnect = async (repoId) => {
    try {
      const res = await fetch(`${apiUrl}/api/v1/repositories/${repoId}`, { method: 'DELETE' });
      if (res.ok) {
        setRepositories(prev => prev.filter(r => r.id !== repoId));
      }
    } catch (_err) {
      // Silently fail
    }
  };

  return (
    <div className='github-connect'>
      <div className='connect-header'>
        <h2>Connect Repositories</h2>
        <p className='connect-description'>
          Connect your GitHub repositories for automated PR reviews, browser verification, and release gating.
        </p>
      </div>

      {/* Webhook Status */}
      {webhookStatus && (
        <div className='webhook-status-section' style={{ margin: '1rem 0', padding: '0.75rem 1rem', border: '1px solid var(--border-color)', borderRadius: '8px', background: 'var(--bg-elevated)' }}>
          <h4 style={{ marginBottom: '0.5rem' }}>Integration Status</h4>
          <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.85rem' }}>
            <span>
              GitHub Webhook: {webhookStatus.github_webhook_configured ?
                <strong style={{ color: '#22c55e' }}>Configured</strong> :
                <strong style={{ color: '#f59e0b' }}>Not configured</strong>
              }
            </span>
            <span>
              Slack: {webhookStatus.slack_webhook_configured ?
                <strong style={{ color: '#22c55e' }}>Configured</strong> :
                <strong style={{ color: '#6b7280' }}>Not configured</strong>
              }
            </span>
          </div>
        </div>
      )}

      {/* GitHub App Install */}
      <div className='connect-section' style={{ marginBottom: '1.5rem' }}>
        <h3>GitHub App (Recommended)</h3>
        <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
          Install the OmniAudit GitHub App for automatic PR reviews and webhook-driven audits.
        </p>
        <button
          type='button'
          className='btn btn-primary'
          onClick={handleInstallApp}
          disabled={loading}
        >
          {loading ? 'Redirecting...' : 'Install GitHub App'}
        </button>
      </div>

      {/* Manual Connect */}
      <div className='connect-section' style={{ marginBottom: '1.5rem' }}>
        <h3>Manual Repository Connection</h3>
        <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
          Connect a repository manually for tracking and browser verification runs.
        </p>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-end' }}>
          <div className='form-group' style={{ flex: 1 }}>
            <label htmlFor='owner'>Owner</label>
            <input
              id='owner'
              type='text'
              value={manualOwner}
              onChange={e => setManualOwner(e.target.value)}
              placeholder='e.g. acme'
              style={{ width: '100%', padding: '0.5rem', border: '1px solid var(--border-color)', borderRadius: '6px', background: 'var(--bg-elevated)', color: 'var(--text-primary)' }}
            />
          </div>
          <span style={{ padding: '0.5rem 0', fontSize: '1.2rem' }}>/</span>
          <div className='form-group' style={{ flex: 1 }}>
            <label htmlFor='repo'>Repository</label>
            <input
              id='repo'
              type='text'
              value={manualRepo}
              onChange={e => setManualRepo(e.target.value)}
              placeholder='e.g. web-app'
              style={{ width: '100%', padding: '0.5rem', border: '1px solid var(--border-color)', borderRadius: '6px', background: 'var(--bg-elevated)', color: 'var(--text-primary)' }}
            />
          </div>
          <button
            type='button'
            className='btn btn-secondary'
            onClick={handleManualConnect}
            disabled={connectingManual}
            style={{ whiteSpace: 'nowrap' }}
          >
            {connectingManual ? 'Connecting...' : 'Connect'}
          </button>
        </div>
      </div>

      {error && <div className='error-message' style={{ marginBottom: '1rem' }}>{error}</div>}

      {/* Connected Repositories */}
      <div className='connected-repos-section'>
        <h3>Connected Repositories ({repositories.length})</h3>
        {repositories.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.75rem' }}>
            {repositories.map(repo => (
              <div key={repo.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 1rem', border: '1px solid var(--border-color)', borderRadius: '8px', background: 'var(--bg-elevated)' }}>
                <div>
                  <strong>{repo.full_name}</strong>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginLeft: '0.75rem' }}>
                    {repo.status}
                  </span>
                </div>
                <button
                  type='button'
                  className='btn btn-small'
                  onClick={() => handleDisconnect(repo.id)}
                  style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                >
                  Disconnect
                </button>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
            No repositories connected yet. Install the GitHub App or connect manually above.
          </p>
        )}
      </div>

      <div className='connect-footer' style={{ marginTop: '2rem' }}>
        <p>
          <small>
            OmniAudit only requests necessary permissions. We never store your source code.
            <br />
            <a
              href='https://github.com/ehudso7/OmniAudit'
              target='_blank'
              rel='noopener noreferrer'
            >
              View source code
            </a>
          </small>
        </p>
      </div>
    </div>
  );
}

GitHubConnect.propTypes = {
  apiUrl: PropTypes.string.isRequired,
  onConnect: PropTypes.func,
};

export default GitHubConnect;
