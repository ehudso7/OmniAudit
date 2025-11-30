import PropTypes from 'prop-types';
import { useCallback, useEffect, useState } from 'react';

function Dashboard({ apiUrl, auditResults }) {
  const [dashboardData, setDashboardData] = useState(null);
  const [skills, setSkills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [dashboardRes, skillsRes] = await Promise.all([
        fetch(`${apiUrl}/api/v1/dashboard/stats`),
        fetch(`${apiUrl}/api/skills`)
      ]);

      if (dashboardRes.ok) {
        const data = await dashboardRes.json();
        setDashboardData(data);
      }

      if (skillsRes.ok) {
        const data = await skillsRes.json();
        setSkills(data.skills || []);
      }
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [apiUrl]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, [fetchData]);

  const stats = dashboardData?.stats || {};
  const activity = dashboardData?.activity || [];
  const issuesBreakdown = dashboardData?.issues_breakdown || {};
  const topRepos = dashboardData?.top_repositories || [];
  const recentReviews = dashboardData?.recent_reviews || [];

  // Calculate max for chart scaling
  const maxActivity = Math.max(...activity.map(a => a.reviews), 1);
  const maxIssue = Math.max(...Object.values(issuesBreakdown), 1);

  if (loading && !dashboardData) {
    return (
      <div className='dashboard'>
        <div className='loading'>
          <div className='spinner'></div>
          <p>Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className='dashboard'>
      <div className='dashboard-header'>
        <h2>📊 Dashboard</h2>
        <button type='button' className='btn btn-secondary btn-small' onClick={fetchData} disabled={loading}>
          {loading ? '⟳' : '↻'} Refresh
        </button>
      </div>

      {error && (
        <div className='error-message'>
          ⚠️ {error}
        </div>
      )}

      {/* Key Metrics */}
      <div className='stats-grid'>
        <div className='stat-card'>
          <div className='stat-icon'>📝</div>
          <div className='stat-content'>
            <h3>Total Reviews</h3>
            <p className='stat-value'>{stats.total_reviews || 0}</p>
          </div>
        </div>

        <div className='stat-card'>
          <div className='stat-icon'>🐛</div>
          <div className='stat-content'>
            <h3>Issues Found</h3>
            <p className='stat-value'>{stats.issues_found || 0}</p>
          </div>
        </div>

        <div className='stat-card'>
          <div className='stat-icon'>🔐</div>
          <div className='stat-content'>
            <h3>Security Blocked</h3>
            <p className='stat-value' style={{ color: '#ef4444' }}>{stats.security_blocked || 0}</p>
          </div>
        </div>

        <div className='stat-card'>
          <div className='stat-icon'>✅</div>
          <div className='stat-content'>
            <h3>Approval Rate</h3>
            <p className='stat-value'>{stats.approval_rate || 0}%</p>
          </div>
        </div>

        <div className='stat-card'>
          <div className='stat-icon'>📅</div>
          <div className='stat-content'>
            <h3>This Week</h3>
            <p className='stat-value'>{stats.this_week || 0}</p>
          </div>
        </div>

        <div className='stat-card'>
          <div className='stat-icon'>📦</div>
          <div className='stat-content'>
            <h3>Repositories</h3>
            <p className='stat-value'>{stats.repos_connected || 0}</p>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className='charts-grid'>
        {/* Activity Chart */}
        <div className='chart-card'>
          <h3>📈 Review Activity (Last 7 Days)</h3>
          <div className='bar-chart'>
            {activity.map((day, idx) => (
              <div key={idx} className='bar-item'>
                <div className='bar-container'>
                  <div
                    className='bar'
                    style={{ height: `${(day.reviews / maxActivity) * 100}%` }}
                    title={`${day.reviews} reviews`}
                  >
                    {day.reviews > 0 && <span className='bar-value'>{day.reviews}</span>}
                  </div>
                </div>
                <span className='bar-label'>{day.day}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Issues Breakdown */}
        <div className='chart-card'>
          <h3>🔍 Issues Breakdown</h3>
          <div className='horizontal-bar-chart'>
            {Object.entries(issuesBreakdown).map(([type, count]) => (
              <div key={type} className='h-bar-item'>
                <span className='h-bar-label'>{type.charAt(0).toUpperCase() + type.slice(1)}</span>
                <div className='h-bar-container'>
                  <div
                    className={`h-bar h-bar-${type}`}
                    style={{ width: `${(count / maxIssue) * 100}%` }}
                  >
                    <span className='h-bar-value'>{count}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top Repositories and Recent Activity */}
      <div className='dashboard-grid'>
        {/* Top Repositories */}
        <div className='section'>
          <h3>🏆 Top Repositories</h3>
          <div className='top-repos-list'>
            {topRepos.length > 0 ? (
              topRepos.map((repo, idx) => (
                <div key={idx} className='repo-item'>
                  <span className='repo-rank'>#{idx + 1}</span>
                  <span className='repo-name'>{repo.name}</span>
                  <span className='repo-reviews'>{repo.reviews} reviews</span>
                </div>
              ))
            ) : (
              <p className='empty-text'>No repositories yet</p>
            )}
          </div>
        </div>

        {/* Recent Reviews */}
        <div className='section'>
          <h3>🕐 Recent Reviews</h3>
          <div className='recent-reviews-list'>
            {recentReviews.length > 0 ? (
              recentReviews.slice(0, 5).map((review, idx) => (
                <div key={idx} className='recent-review-item'>
                  <div className='review-info'>
                    <span className='review-repo-small'>{review.repo}</span>
                    <span className='review-pr'>#{review.pr_number}</span>
                  </div>
                  <span className={`review-action-badge ${review.action.toLowerCase()}`}>
                    {review.action === 'APPROVE' ? '✓' : review.action === 'REQUEST_CHANGES' ? '⚠' : '💬'}
                  </span>
                </div>
              ))
            ) : (
              <p className='empty-text'>No recent reviews</p>
            )}
          </div>
        </div>
      </div>

      {/* Available Skills */}
      <div className='section'>
        <h3>🎯 Available Analysis Skills ({skills.length})</h3>
        <div className='skills-grid'>
          {skills.map((skill, idx) => (
            <div key={idx} className='skill-card'>
              <div className='skill-header'>
                <span className='skill-name'>{skill.name}</span>
                <span className='skill-category'>{skill.category}</span>
              </div>
              <p className='skill-description'>{skill.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Latest Audit Results */}
      {auditResults && (
        <div className='section'>
          <h3>📋 Latest Analysis Results</h3>
          <div className='audit-results-card'>
            <div className='audit-score'>
              <div className='score-circle' style={{
                background: `conic-gradient(${auditResults.score >= 80 ? '#22c55e' : auditResults.score >= 50 ? '#f59e0b' : '#ef4444'} ${auditResults.score * 3.6}deg, #1e293b 0deg)`
              }}>
                <span className='score-value'>{auditResults.score}</span>
              </div>
              <span className='score-label'>Health Score</span>
            </div>

            <div className='audit-findings'>
              <h4>Findings Summary</h4>
              <div className='findings-grid'>
                <div className='finding-stat'>
                  <span className='finding-count'>{auditResults.summary?.security || 0}</span>
                  <span className='finding-label'>Security</span>
                </div>
                <div className='finding-stat'>
                  <span className='finding-count'>{auditResults.summary?.performance || 0}</span>
                  <span className='finding-label'>Performance</span>
                </div>
                <div className='finding-stat'>
                  <span className='finding-count'>{auditResults.summary?.quality || 0}</span>
                  <span className='finding-label'>Quality</span>
                </div>
                <div className='finding-stat'>
                  <span className='finding-count'>{auditResults.summary?.total_issues || 0}</span>
                  <span className='finding-label'>Total</span>
                </div>
              </div>

              {auditResults.findings && auditResults.findings.length > 0 && (
                <div className='findings-list'>
                  <h5>Issues Found:</h5>
                  {auditResults.findings.slice(0, 5).map((finding, idx) => (
                    <div key={idx} className={`finding-item severity-${finding.severity}`}>
                      <span className='finding-type'>{finding.type}</span>
                      <span className='finding-title'>{finding.title}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
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
