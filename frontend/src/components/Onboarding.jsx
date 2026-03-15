import { useState } from 'react';

const STEPS = [
  {
    id: 'welcome',
    title: 'Welcome to OmniAudit',
    description: 'AI-powered code and browser verification in one platform. Let\'s get you set up in under a minute.',
  },
  {
    id: 'connect',
    title: 'Connect a Repository',
    description: 'Link a GitHub repository to enable automated PR reviews and browser verification on deploys.',
  },
  {
    id: 'audit',
    title: 'Run Your First Browser Audit',
    description: 'Enter a URL and let OmniAudit check for console errors, network failures, accessibility issues, and more.',
  },
  {
    id: 'done',
    title: 'You\'re All Set!',
    description: 'Your account is configured. Explore the dashboard, set up release gates, or run another audit.',
  },
];

function Onboarding({ apiUrl, authToken, onComplete, onNavigate }) {
  const [step, setStep] = useState(0);
  const [repoUrl, setRepoUrl] = useState('');
  const [targetUrl, setTargetUrl] = useState('');
  const [connecting, setConnecting] = useState(false);
  const [connectResult, setConnectResult] = useState(null);

  const current = STEPS[step];

  const connectRepo = async () => {
    if (!repoUrl.trim()) return;
    setConnecting(true);
    setConnectResult(null);
    const headers = authToken
      ? { Authorization: `Bearer ${authToken}`, 'Content-Type': 'application/json' }
      : { 'Content-Type': 'application/json' };
    try {
      const res = await fetch(`${apiUrl}/api/v1/reviews/repos`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ repo_url: repoUrl }),
      });
      if (res.ok) {
        setConnectResult('success');
      } else {
        setConnectResult('error');
      }
    } catch {
      setConnectResult('error');
    } finally {
      setConnecting(false);
    }
  };

  const next = () => {
    if (step < STEPS.length - 1) setStep(step + 1);
  };

  const back = () => {
    if (step > 0) setStep(step - 1);
  };

  return (
    <div className='onboarding'>
      {/* Progress dots */}
      <div className='onboarding-progress'>
        {STEPS.map((s, i) => (
          <div key={s.id} className={`progress-dot ${i === step ? 'active' : ''} ${i < step ? 'completed' : ''}`} />
        ))}
      </div>

      <div className='onboarding-content'>
        <h2>{current.title}</h2>
        <p className='onboarding-description'>{current.description}</p>

        {/* Step-specific content */}
        {current.id === 'welcome' && (
          <div className='onboarding-features'>
            <div className='onboarding-feature'>
              <strong>Automated PR Reviews</strong>
              <span>AI analyzes every pull request for security, performance, and quality issues.</span>
            </div>
            <div className='onboarding-feature'>
              <strong>Browser Verification</strong>
              <span>Playwright-powered checks catch console errors, broken assets, and accessibility issues.</span>
            </div>
            <div className='onboarding-feature'>
              <strong>Release Gates</strong>
              <span>Block deployments that don't meet your quality thresholds.</span>
            </div>
          </div>
        )}

        {current.id === 'connect' && (
          <div className='onboarding-form'>
            <div className='form-group'>
              <label htmlFor='onboard-repo'>GitHub Repository URL</label>
              <input id='onboard-repo' type='url' className='url-input' placeholder='https://github.com/owner/repo'
                value={repoUrl} onChange={e => setRepoUrl(e.target.value)} />
            </div>
            <button type='button' className='btn btn-primary' onClick={connectRepo} disabled={connecting || !repoUrl.trim()}>
              {connecting ? 'Connecting...' : 'Connect Repository'}
            </button>
            {connectResult === 'success' && <p className='onboarding-success'>Repository connected!</p>}
            {connectResult === 'error' && <p className='onboarding-error'>Could not connect. You can add it later from the Connect tab.</p>}
            <button type='button' className='link-btn' onClick={next} style={{ marginTop: '0.5rem' }}>Skip for now</button>
          </div>
        )}

        {current.id === 'audit' && (
          <div className='onboarding-form'>
            <div className='form-group'>
              <label htmlFor='onboard-url'>Target URL to audit</label>
              <input id='onboard-url' type='url' className='url-input' placeholder='https://your-app.com'
                value={targetUrl} onChange={e => setTargetUrl(e.target.value)} />
            </div>
            <button type='button' className='btn btn-primary' onClick={() => { onNavigate('audit'); }}>
              Go to Browser Audit
            </button>
            <button type='button' className='link-btn' onClick={next} style={{ marginTop: '0.5rem' }}>Skip for now</button>
          </div>
        )}

        {current.id === 'done' && (
          <div className='onboarding-actions'>
            <button type='button' className='btn btn-primary' onClick={() => onNavigate('dashboard')}>
              Open Dashboard
            </button>
            <button type='button' className='btn btn-outline' onClick={() => onNavigate('audit')}>
              Run an Audit
            </button>
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className='onboarding-nav'>
        {step > 0 && current.id !== 'done' && (
          <button type='button' className='btn btn-small' onClick={back}>Back</button>
        )}
        <div style={{ flex: 1 }} />
        {current.id !== 'done' && current.id !== 'connect' && current.id !== 'audit' && (
          <button type='button' className='btn btn-primary' onClick={next}>Next</button>
        )}
        {current.id === 'connect' && connectResult === 'success' && (
          <button type='button' className='btn btn-primary' onClick={next}>Next</button>
        )}
        <button type='button' className='link-btn' onClick={onComplete} style={{ marginLeft: '1rem' }}>
          Skip onboarding
        </button>
      </div>
    </div>
  );
}

export default Onboarding;
