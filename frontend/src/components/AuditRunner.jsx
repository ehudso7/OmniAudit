import PropTypes from 'prop-types';
import { useState } from 'react';

function AuditRunner({ apiUrl, onComplete }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [code, setCode] = useState(`function calculateTotal(items) {
  let total = 0;
  for (let i = 0; i < items.length; i++) {
    total += items[i].price * items[i].quantity;
  }
  return total;
}`);
  const [selectedSkills, setSelectedSkills] = useState(['performance-optimizer-pro']);

  const runAnalysis = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiUrl}/api/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          code: code,
          skills: selectedSkills,
          language: 'javascript',
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      onComplete(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Analysis failed:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className='audit-runner'>
      <h2>Run Code Analysis</h2>

      <div className='form'>
        <div className='form-group'>
          <label htmlFor='code'>Code to Analyze</label>
          <textarea
            id='code'
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder='Paste your code here...'
            rows={12}
            style={{ fontFamily: 'monospace', width: '100%', padding: '0.75rem' }}
          />
          <small>Enter JavaScript/TypeScript code to analyze</small>
        </div>

        <div className='form-group'>
          <label>Skills to Apply</label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.5rem' }}>
            {[
              { id: 'performance-optimizer-pro', name: 'Performance' },
              { id: 'security-auditor', name: 'Security' },
              { id: 'react-best-practices', name: 'React Best Practices' },
              { id: 'typescript-expert', name: 'TypeScript Expert' },
              { id: 'architecture-advisor', name: 'Architecture' },
            ].map((skill) => (
              <label key={skill.id} style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <input
                  type='checkbox'
                  checked={selectedSkills.includes(skill.id)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedSkills([...selectedSkills, skill.id]);
                    } else {
                      setSelectedSkills(selectedSkills.filter((s) => s !== skill.id));
                    }
                  }}
                />
                <span>{skill.name}</span>
              </label>
            ))}
          </div>
        </div>

        <button
          type="button"
          className='btn btn-primary'
          onClick={runAnalysis}
          disabled={loading || !code.trim()}
        >
          {loading ? '🔄 Analyzing...' : '🚀 Analyze Code'}
        </button>

        {error && <div className='error-message'>❌ Error: {error}</div>}

        {!error && !loading && (
          <div className='info-message'>
            💡 Tip: This uses Claude AI to analyze your code for quality, performance, and security
            issues.
          </div>
        )}
      </div>
    </div>
  );
}

AuditRunner.propTypes = {
  apiUrl: PropTypes.string.isRequired,
  onComplete: PropTypes.func.isRequired,
};

export default AuditRunner;
