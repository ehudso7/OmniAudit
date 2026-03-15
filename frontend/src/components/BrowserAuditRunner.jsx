import PropTypes from 'prop-types';
import { useCallback, useEffect, useState } from 'react';

const PRESET_JOURNEYS = [
  { id: 'page_load', name: 'Page Load', description: 'Verify page loads and responds correctly' },
  { id: 'console_errors', name: 'Console Errors', description: 'Check for JavaScript errors' },
  { id: 'network_check', name: 'Network Check', description: 'Detect failed network requests' },
  { id: 'accessibility', name: 'Accessibility', description: 'WCAG and a11y validation' },
  { id: 'screenshot', name: 'Screenshots', description: 'Capture visual evidence' },
];

const VIEWPORT_PRESETS = [
  { label: 'Desktop (1280x720)', width: 1280, height: 720 },
  { label: 'Laptop (1024x768)', width: 1024, height: 768 },
  { label: 'Tablet (768x1024)', width: 768, height: 1024 },
  { label: 'Mobile (375x812)', width: 375, height: 812 },
];

const ENVIRONMENTS = ['preview', 'staging', 'production', 'local'];

function BrowserAuditRunner({ apiUrl, onComplete }) {
  const [targetUrl, setTargetUrl] = useState('');
  const [environment, setEnvironment] = useState('preview');
  const [selectedJourneys, setSelectedJourneys] = useState(['page_load', 'console_errors', 'network_check', 'accessibility', 'screenshot']);
  const [viewport, setViewport] = useState(VIEWPORT_PRESETS[0]);
  const [releaseGate, setReleaseGate] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentRun, setCurrentRun] = useState(null);
  const [runResult, setRunResult] = useState(null);
  const [pollingId, setPollingId] = useState(null);
  const [recentRuns, setRecentRuns] = useState([]);

  // Load recent runs
  useEffect(() => {
    fetch(`${apiUrl}/api/v1/browser-runs?limit=5`)
      .then(res => res.ok ? res.json() : null)
      .then(data => { if (data) setRecentRuns(data.runs || []); })
      .catch(() => {});
  }, [apiUrl, runResult]);

  // Poll for run completion
  const pollRun = useCallback(async (runId) => {
    try {
      const res = await fetch(`${apiUrl}/api/v1/browser-runs/${runId}`);
      if (!res.ok) return;
      const data = await res.json();
      const run = data.run;

      if (run.status === 'completed' || run.status === 'failed') {
        setRunResult({ run, checks: data.checks || [] });
        setCurrentRun(null);
        setLoading(false);
        if (onComplete) onComplete(run);
        return true;
      }
      return false;
    } catch {
      return false;
    }
  }, [apiUrl, onComplete]);

  useEffect(() => {
    if (!currentRun) return;
    const interval = setInterval(async () => {
      const done = await pollRun(currentRun.id);
      if (done) clearInterval(interval);
    }, 2000);
    setPollingId(interval);
    return () => clearInterval(interval);
  }, [currentRun, pollRun]);

  const startRun = async () => {
    if (!targetUrl.trim()) {
      setError('Please enter a target URL');
      return;
    }

    setLoading(true);
    setError(null);
    setRunResult(null);

    const journeys = selectedJourneys.map(id => {
      const preset = PRESET_JOURNEYS.find(j => j.id === id);
      return {
        name: id,
        description: preset?.description || id,
        steps: [{ action: id === 'screenshot' ? 'screenshot' : id === 'accessibility' ? 'check_a11y' : id === 'console_errors' ? 'check_console' : id === 'network_check' ? 'check_network' : 'navigate', url: '{target_url}' }],
      };
    });

    try {
      const res = await fetch(`${apiUrl}/api/v1/browser-runs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_url: targetUrl,
          environment,
          viewport_width: viewport.width,
          viewport_height: viewport.height,
          journeys,
          release_gate: releaseGate,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Request failed (${res.status})`);
      }

      const data = await res.json();
      setCurrentRun(data.run);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const toggleJourney = (id) => {
    setSelectedJourneys(prev =>
      prev.includes(id) ? prev.filter(j => j !== id) : [...prev, id]
    );
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return '#dc2626';
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#3b82f6';
      default: return '#6b7280';
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return '#22c55e';
    if (score >= 50) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <div className="browser-audit">
      {/* Configuration */}
      {!runResult && (
        <div className="browser-audit-config">
          <div className="form-group">
            <label htmlFor="target-url">Target URL</label>
            <input
              id="target-url"
              type="url"
              value={targetUrl}
              onChange={(e) => setTargetUrl(e.target.value)}
              placeholder="https://your-app.vercel.app"
              className="url-input"
              disabled={loading}
            />
          </div>

          <div className="config-row">
            <div className="form-group">
              <label htmlFor="environment">Environment</label>
              <select
                id="environment"
                value={environment}
                onChange={(e) => setEnvironment(e.target.value)}
                disabled={loading}
              >
                {ENVIRONMENTS.map(env => (
                  <option key={env} value={env}>{env.charAt(0).toUpperCase() + env.slice(1)}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="viewport">Viewport</label>
              <select
                id="viewport"
                value={`${viewport.width}x${viewport.height}`}
                onChange={(e) => {
                  const preset = VIEWPORT_PRESETS.find(v => `${v.width}x${v.height}` === e.target.value);
                  if (preset) setViewport(preset);
                }}
                disabled={loading}
              >
                {VIEWPORT_PRESETS.map(v => (
                  <option key={`${v.width}x${v.height}`} value={`${v.width}x${v.height}`}>{v.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Verification Checks</label>
            <div className="journey-selection">
              {PRESET_JOURNEYS.map(j => (
                <button
                  key={j.id}
                  type="button"
                  className={`journey-toggle ${selectedJourneys.includes(j.id) ? 'selected' : ''}`}
                  onClick={() => toggleJourney(j.id)}
                  disabled={loading}
                >
                  <span className="journey-name">{j.name}</span>
                  <span className="journey-desc">{j.description}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="form-group">
            <label className="toggle-label">
              <input
                type="checkbox"
                checked={releaseGate}
                onChange={(e) => setReleaseGate(e.target.checked)}
                disabled={loading}
              />
              <span>Release Gate - Block deployment if critical issues found</span>
            </label>
          </div>

          <button
            type="button"
            className="btn btn-primary btn-large"
            onClick={startRun}
            disabled={loading || !targetUrl.trim() || selectedJourneys.length === 0}
          >
            {loading ? (
              <><span className="spinner-small" /> Running verification...</>
            ) : (
              <>Run Browser Verification</>
            )}
          </button>

          {error && (
            <div className="error-message">
              <span className="error-icon">!</span>
              <div>
                <strong>Verification Failed</strong>
                <p>{error}</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Running State */}
      {loading && currentRun && (
        <div className="run-progress">
          <div className="spinner" />
          <h3>Browser Verification Running</h3>
          <p>Executing checks against {targetUrl}</p>
          <div className="run-meta">
            <span>Environment: {environment}</span>
            <span>Viewport: {viewport.width}x{viewport.height}</span>
            <span>Checks: {selectedJourneys.length}</span>
          </div>
        </div>
      )}

      {/* Results */}
      {runResult && (
        <div className="browser-results">
          <div className="results-header">
            <h3>Browser Verification Results</h3>
            <div className="results-actions">
              <button type="button" className="btn btn-secondary btn-small" onClick={() => setRunResult(null)}>
                New Run
              </button>
            </div>
          </div>

          {/* Score */}
          <div className="score-section">
            <div className="score-display">
              <div
                className="score-ring"
                style={{
                  background: `conic-gradient(
                    ${getScoreColor(runResult.run.score || 0)} ${(runResult.run.score || 0) * 3.6}deg,
                    #1e293b ${(runResult.run.score || 0) * 3.6}deg
                  )`,
                }}
              >
                <div className="score-inner">
                  <span className="score-number">{runResult.run.score || 0}</span>
                  <span className="score-label">Score</span>
                </div>
              </div>
            </div>
            <div className="score-details">
              <p className="score-summary">{runResult.run.summary}</p>
              {runResult.run.blocking_verdict && (
                <div className={`verdict-badge verdict-${runResult.run.blocking_verdict}`}>
                  {runResult.run.blocking_verdict === 'blocked' ? 'Release Blocked' : 'Release Approved'}
                </div>
              )}
              <div className="score-meta">
                <span>Duration: {runResult.run.duration_ms ? `${(runResult.run.duration_ms / 1000).toFixed(1)}s` : 'N/A'}</span>
                <span>Status: {runResult.run.status}</span>
              </div>
            </div>
          </div>

          {/* Findings Summary */}
          <div className="findings-summary-grid">
            <div className="finding-stat-card">
              <span className="stat-number" style={{ color: '#ef4444' }}>{runResult.run.security_findings || 0}</span>
              <span className="stat-label">Security</span>
            </div>
            <div className="finding-stat-card">
              <span className="stat-number" style={{ color: '#f59e0b' }}>{runResult.run.performance_findings || 0}</span>
              <span className="stat-label">Performance</span>
            </div>
            <div className="finding-stat-card">
              <span className="stat-number" style={{ color: '#8b5cf6' }}>{runResult.run.accessibility_findings || 0}</span>
              <span className="stat-label">Accessibility</span>
            </div>
            <div className="finding-stat-card">
              <span className="stat-number" style={{ color: '#dc2626' }}>{runResult.run.console_errors || 0}</span>
              <span className="stat-label">Console Errors</span>
            </div>
            <div className="finding-stat-card">
              <span className="stat-number" style={{ color: '#dc2626' }}>{runResult.run.network_failures || 0}</span>
              <span className="stat-label">Network Failures</span>
            </div>
            <div className="finding-stat-card">
              <span className="stat-number">{runResult.run.findings_count || 0}</span>
              <span className="stat-label">Total Findings</span>
            </div>
          </div>

          {/* Checks Detail */}
          {runResult.checks && runResult.checks.length > 0 && (
            <div className="checks-section">
              <h4>Verification Checks ({runResult.checks.length})</h4>
              <div className="checks-list">
                {runResult.checks.map((check, idx) => (
                  <div key={idx} className={`check-item check-${check.status}`}>
                    <div className="check-status-icon">
                      {check.status === 'passed' ? '✓' : check.status === 'failed' ? '✗' : '?'}
                    </div>
                    <div className="check-content">
                      <div className="check-header-row">
                        <span className="check-journey">{check.journey}</span>
                        <span className="check-type">{check.check_type}</span>
                        {check.severity && (
                          <span className="check-severity" style={{ color: getSeverityColor(check.severity) }}>
                            {check.severity}
                          </span>
                        )}
                      </div>
                      <p className="check-message">{check.message}</p>
                      {check.selector && <span className="check-selector">{check.selector}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Recent Runs */}
      {!loading && !runResult && recentRuns.length > 0 && (
        <div className="recent-runs">
          <h4>Recent Browser Runs</h4>
          <div className="recent-runs-list">
            {recentRuns.map(run => (
              <div key={run.id} className={`recent-run-item run-${run.status}`}>
                <div className="run-url">{run.target_url}</div>
                <div className="run-details">
                  <span className={`run-status status-${run.status}`}>{run.status}</span>
                  {run.score !== null && <span className="run-score" style={{ color: getScoreColor(run.score) }}>{run.score}/100</span>}
                  <span className="run-env">{run.environment}</span>
                  {run.created_at && <span className="run-time">{new Date(run.created_at).toLocaleString()}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

BrowserAuditRunner.propTypes = {
  apiUrl: PropTypes.string.isRequired,
  onComplete: PropTypes.func,
};

export default BrowserAuditRunner;
