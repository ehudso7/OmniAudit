import PropTypes from 'prop-types';
import { useState } from 'react';

const GITHUB_APP_URL = 'https://github.com/apps/omniaudit/installations/new';

function GitHubConnect({ apiUrl, onConnect }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleConnect = async () => {
    setLoading(true);
    setError(null);

    try {
      // Check webhook status before redirecting
      const response = await fetch(`${apiUrl}/api/v1/webhooks/status`);
      if (response.ok) {
        onConnect?.();
      }
    } catch (err) {
      setError('Could not verify connection. Redirecting to GitHub...');
    }

    // Redirect to GitHub App installation regardless
    setTimeout(() => {
      window.location.href = GITHUB_APP_URL;
    }, 500);
  };

  return (
    <div className='github-connect'>
      <div className='connect-header'>
        <svg viewBox='0 0 24 24' width='48' height='48' fill='currentColor'>
          <path d='M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z' />
        </svg>
        <h2>Connect GitHub</h2>
      </div>

      <p className='connect-description'>
        Install the OmniAudit GitHub App to automatically review your pull requests with AI-powered code analysis.
      </p>

      <div className='features-list'>
        <div className='feature'>
          <span className='feature-icon'>🔍</span>
          <div>
            <strong>Automatic PR Reviews</strong>
            <p>Get instant feedback on every pull request</p>
          </div>
        </div>
        <div className='feature'>
          <span className='feature-icon'>🔴</span>
          <div>
            <strong>Security Scanning</strong>
            <p>Detect vulnerabilities before they reach production</p>
          </div>
        </div>
        <div className='feature'>
          <span className='feature-icon'>⚡</span>
          <div>
            <strong>Performance Analysis</strong>
            <p>Identify bottlenecks and optimization opportunities</p>
          </div>
        </div>
        <div className='feature'>
          <span className='feature-icon'>💡</span>
          <div>
            <strong>Code Quality</strong>
            <p>Suggestions for cleaner, more maintainable code</p>
          </div>
        </div>
      </div>

      <button type='button' className='btn btn-primary btn-large' onClick={handleConnect} disabled={loading}>
        {loading ? '⏳ Connecting...' : '🔗 Install GitHub App'}
      </button>

      {error && <div className='error-message'>{error}</div>}

      <div className='connect-footer'>
        <p>
          <small>
            OmniAudit only requests necessary permissions. We never store your code.
            <br />
            <a href='https://github.com/ehudso7/OmniAudit' target='_blank' rel='noopener noreferrer'>
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
