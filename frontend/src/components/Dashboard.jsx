import PropTypes from 'prop-types';
import { useEffect, useState } from 'react';

function Dashboard({ apiUrl, auditResults }) {
  const [skills, setSkills] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch available skills from TypeScript API
    fetch(`${apiUrl}/api/skills`)
      .then((res) => res.json())
      .then((data) => {
        setSkills(data.skills || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to fetch skills:', err);
        setLoading(false);
      });
  }, [apiUrl]);

  return (
    <div className='dashboard'>
      <h2>Dashboard Overview</h2>

      <div className='stats-grid'>
        <div className='stat-card'>
          <div className='stat-icon'>🎯</div>
          <div className='stat-content'>
            <h3>Available Skills</h3>
            <p className='stat-value'>{loading ? '...' : skills.length}</p>
          </div>
        </div>

        {auditResults && (
          <div className='stat-card'>
            <div className='stat-icon'>✅</div>
            <div className='stat-content'>
              <h3>Last Analysis</h3>
              <p className='stat-value'>Success</p>
            </div>
          </div>
        )}

        <div className='stat-card'>
          <div className='stat-icon'>🤖</div>
          <div className='stat-content'>
            <h3>AI Engine</h3>
            <p className='stat-value'>Claude 4.5</p>
          </div>
        </div>
      </div>

      <div className='section'>
        <h3>Available Skills</h3>
        {loading ? (
          <p>Loading skills...</p>
        ) : (
          <div className='collector-list'>
            {skills.map((skill, idx) => (
              <div key={idx} className='collector-card'>
                <div className='collector-name'>{skill.name}</div>
                <div className='collector-version'>{skill.category}</div>
                <div style={{ fontSize: '0.85em', marginTop: '0.5rem', color: '#666' }}>
                  {skill.description}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {auditResults && (
        <div className='section'>
          <h3>Latest Analysis Results</h3>
          <div className='audit-summary'>
            <pre>{JSON.stringify(auditResults, null, 2)}</pre>
          </div>
        </div>
      )}
    </div>
  );
}

Dashboard.propTypes = {
  apiUrl: PropTypes.string.isRequired,
  auditResults: PropTypes.object,
};

export default Dashboard;
