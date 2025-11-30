import PropTypes from 'prop-types';
import { useState } from 'react';

const AVAILABLE_SKILLS = [
  { id: 'security-auditor', name: 'Security', icon: '🔐', description: 'Detect vulnerabilities' },
  { id: 'performance-optimizer-pro', name: 'Performance', icon: '⚡', description: 'Find bottlenecks' },
  { id: 'code-quality', name: 'Quality', icon: '📋', description: 'Code smells & patterns' },
  { id: 'react-best-practices', name: 'React', icon: '⚛️', description: 'React patterns' },
  { id: 'typescript-expert', name: 'TypeScript', icon: '📘', description: 'Type checking' },
  { id: 'architecture-advisor', name: 'Architecture', icon: '🏗️', description: 'Structure review' },
];

const EXAMPLE_CODES = {
  vulnerable: `// Example with security issues
const password = "admin123";
function login(user, pass) {
  const query = "SELECT * FROM users WHERE user='" + user + "' AND pass='" + pass + "'";
  return db.execute(query);
}

function processData(input) {
  return eval(input);
}`,
  performance: `function calculateTotal(items) {
  let total = 0;
  for (let i = 0; i < items.length; i++) {
    total += items[i].price * items[i].quantity;
    console.log("Processing item " + i);
  }
  return total;
}

function fetchAllData() {
  const users = fetchUsers();
  const orders = fetchOrders();
  const products = fetchProducts();
  return { users, orders, products };
}`,
  clean: `/**
 * Calculate the total price of items in cart
 * @param {Array} items - Cart items with price and quantity
 * @returns {number} Total price
 */
function calculateTotal(items) {
  return items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
}

export { calculateTotal };`,
};

function AuditRunner({ apiUrl, onComplete }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);
  const [code, setCode] = useState(EXAMPLE_CODES.performance);
  const [selectedSkills, setSelectedSkills] = useState(['security-auditor', 'performance-optimizer-pro']);
  const [progress, setProgress] = useState(0);

  const runAnalysis = async () => {
    if (!code.trim()) {
      setError('Please enter some code to analyze');
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);
    setProgress(0);

    // Simulate progress
    const progressInterval = setInterval(() => {
      setProgress(prev => Math.min(prev + 10, 90));
    }, 200);

    try {
      const response = await fetch(`${apiUrl}/api/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          code: code,
          skills: selectedSkills,
          language: detectLanguage(code),
        }),
      });

      clearInterval(progressInterval);
      setProgress(100);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || errorData.detail || `Analysis failed (${response.status})`);
      }

      const data = await response.json();
      setResults(data);
      onComplete(data);
    } catch (err) {
      clearInterval(progressInterval);
      setError(err.message);
      console.error('Analysis failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const detectLanguage = (code) => {
    if (code.includes('interface ') || code.includes(': string') || code.includes(': number')) {
      return 'typescript';
    }
    if (code.includes('def ') || code.includes('import ') && code.includes(':')) {
      return 'python';
    }
    return 'javascript';
  };

  const toggleSkill = (skillId) => {
    setSelectedSkills(prev =>
      prev.includes(skillId)
        ? prev.filter(s => s !== skillId)
        : [...prev, skillId]
    );
  };

  const loadExample = (type) => {
    setCode(EXAMPLE_CODES[type]);
    setResults(null);
    setError(null);
  };

  const getSeverityClass = (severity) => {
    switch (severity) {
      case 'critical':
      case 'high': return 'severity-high';
      case 'medium': return 'severity-medium';
      case 'low': return 'severity-low';
      default: return 'severity-info';
    }
  };

  return (
    <div className='audit-runner'>
      <div className='audit-header'>
        <h2>🚀 Run Code Analysis</h2>
        <p>Paste your code and select analysis skills to check for issues</p>
      </div>

      <div className='audit-layout'>
        <div className='audit-input-section'>
          {/* Example Buttons */}
          <div className='example-buttons'>
            <span>Load example:</span>
            <button type='button' onClick={() => loadExample('vulnerable')} className='btn btn-small'>
              🔓 Vulnerable Code
            </button>
            <button type='button' onClick={() => loadExample('performance')} className='btn btn-small'>
              🐢 Performance Issues
            </button>
            <button type='button' onClick={() => loadExample('clean')} className='btn btn-small'>
              ✨ Clean Code
            </button>
          </div>

          {/* Code Input */}
          <div className='form-group'>
            <label htmlFor='code'>Code to Analyze</label>
            <textarea
              id='code'
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder='Paste your code here...'
              rows={16}
              className='code-input'
              spellCheck='false'
            />
            <div className='input-meta'>
              <span>{code.split('\n').length} lines</span>
              <span>{code.length} characters</span>
              <span>Language: {detectLanguage(code)}</span>
            </div>
          </div>

          {/* Skills Selection */}
          <div className='form-group'>
            <label>Analysis Skills</label>
            <div className='skills-selection'>
              {AVAILABLE_SKILLS.map((skill) => (
                <button
                  key={skill.id}
                  type='button'
                  className={`skill-toggle ${selectedSkills.includes(skill.id) ? 'selected' : ''}`}
                  onClick={() => toggleSkill(skill.id)}
                >
                  <span className='skill-icon'>{skill.icon}</span>
                  <span className='skill-name'>{skill.name}</span>
                </button>
              ))}
            </div>
            <small>{selectedSkills.length} skills selected</small>
          </div>

          {/* Analyze Button */}
          <button
            type='button'
            className='btn btn-primary btn-large'
            onClick={runAnalysis}
            disabled={loading || !code.trim() || selectedSkills.length === 0}
          >
            {loading ? (
              <>
                <span className='spinner-small'></span>
                Analyzing... {progress}%
              </>
            ) : (
              <>🔍 Analyze Code</>
            )}
          </button>

          {/* Progress Bar */}
          {loading && (
            <div className='progress-bar'>
              <div className='progress-fill' style={{ width: `${progress}%` }}></div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className='error-message'>
              <span className='error-icon'>❌</span>
              <div>
                <strong>Analysis Failed</strong>
                <p>{error}</p>
              </div>
            </div>
          )}
        </div>

        {/* Results Section */}
        <div className='audit-results-section'>
          {!results && !loading && !error && (
            <div className='results-placeholder'>
              <div className='placeholder-icon'>📊</div>
              <h3>Analysis Results</h3>
              <p>Results will appear here after you run the analysis</p>
            </div>
          )}

          {results && (
            <div className='results-content'>
              {/* Score */}
              <div className='score-section'>
                <div className='score-display'>
                  <div
                    className='score-ring'
                    style={{
                      background: `conic-gradient(
                        ${results.score >= 80 ? '#22c55e' : results.score >= 50 ? '#f59e0b' : '#ef4444'} ${results.score * 3.6}deg,
                        #1e293b ${results.score * 3.6}deg
                      )`
                    }}
                  >
                    <div className='score-inner'>
                      <span className='score-number'>{results.score}</span>
                      <span className='score-label'>Score</span>
                    </div>
                  </div>
                </div>
                <div className='score-verdict'>
                  {results.score >= 80 ? (
                    <span className='verdict-good'>✓ Looking good!</span>
                  ) : results.score >= 50 ? (
                    <span className='verdict-warn'>⚠ Needs attention</span>
                  ) : (
                    <span className='verdict-bad'>❌ Critical issues found</span>
                  )}
                </div>
              </div>

              {/* Summary Stats */}
              <div className='results-summary'>
                <div className='summary-item'>
                  <span className='summary-count'>{results.summary?.security || 0}</span>
                  <span className='summary-label'>Security</span>
                </div>
                <div className='summary-item'>
                  <span className='summary-count'>{results.summary?.performance || 0}</span>
                  <span className='summary-label'>Performance</span>
                </div>
                <div className='summary-item'>
                  <span className='summary-count'>{results.summary?.quality || 0}</span>
                  <span className='summary-label'>Quality</span>
                </div>
                <div className='summary-item'>
                  <span className='summary-count'>{results.summary?.total_issues || 0}</span>
                  <span className='summary-label'>Total</span>
                </div>
              </div>

              {/* Findings List */}
              {results.findings && results.findings.length > 0 ? (
                <div className='findings-section'>
                  <h4>Issues Found ({results.findings.length})</h4>
                  <div className='findings-list'>
                    {results.findings.map((finding, idx) => (
                      <div key={idx} className={`finding-card ${getSeverityClass(finding.severity)}`}>
                        <div className='finding-header'>
                          <span className={`finding-type type-${finding.type}`}>{finding.type}</span>
                          <span className='finding-severity'>{finding.severity}</span>
                        </div>
                        <h5 className='finding-title'>{finding.title}</h5>
                        <p className='finding-description'>{finding.description}</p>
                        {finding.line > 0 && (
                          <span className='finding-location'>Line {finding.line}</span>
                        )}
                        {finding.fix && (
                          <div className='finding-fix'>
                            <strong>💡 Fix:</strong> {finding.fix}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className='no-findings'>
                  <span className='no-findings-icon'>🎉</span>
                  <h4>No issues found!</h4>
                  <p>Your code passed all selected checks</p>
                </div>
              )}

              {/* Analysis Meta */}
              <div className='analysis-meta'>
                <span>Analyzed at: {new Date(results.timestamp).toLocaleString()}</span>
                <span>Language: {results.language}</span>
                <span>Skills: {results.skills_applied?.join(', ') || 'N/A'}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

AuditRunner.propTypes = {
  apiUrl: PropTypes.string.isRequired,
  onComplete: PropTypes.func.isRequired,
};

export default AuditRunner;
