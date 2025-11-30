import PropTypes from 'prop-types';
import { useEffect, useState } from 'react';

function PRReviews({ apiUrl }) {
  const [reviews, setReviews] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    fetchReviews();
    fetchStats();
  }, [apiUrl]);

  const fetchReviews = async () => {
    try {
      // In production, this would fetch from your API
      // For now, show demo data
      setReviews([
        {
          id: 1,
          repo: 'acme/frontend',
          pr_number: 142,
          title: 'Add user authentication flow',
          status: 'reviewed',
          issues_found: 3,
          security_issues: 1,
          performance_issues: 1,
          suggestions: 1,
          reviewed_at: '2025-01-20T14:30:00Z',
          action: 'REQUEST_CHANGES',
        },
        {
          id: 2,
          repo: 'acme/api-server',
          pr_number: 89,
          title: 'Optimize database queries',
          status: 'reviewed',
          issues_found: 0,
          security_issues: 0,
          performance_issues: 0,
          suggestions: 0,
          reviewed_at: '2025-01-20T12:15:00Z',
          action: 'APPROVE',
        },
        {
          id: 3,
          repo: 'acme/frontend',
          pr_number: 141,
          title: 'Update dependencies',
          status: 'reviewed',
          issues_found: 5,
          security_issues: 2,
          performance_issues: 0,
          suggestions: 3,
          reviewed_at: '2025-01-20T10:00:00Z',
          action: 'REQUEST_CHANGES',
        },
        {
          id: 4,
          repo: 'acme/mobile-app',
          pr_number: 56,
          title: 'Implement push notifications',
          status: 'reviewed',
          issues_found: 1,
          security_issues: 0,
          performance_issues: 1,
          suggestions: 0,
          reviewed_at: '2025-01-19T16:45:00Z',
          action: 'COMMENT',
        },
      ]);
      setLoading(false);
    } catch (err) {
      console.error('Failed to fetch reviews:', err);
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    // Demo stats
    setStats({
      total_reviews: 127,
      issues_found: 342,
      security_blocked: 23,
      repos_connected: 5,
      this_week: 18,
    });
  };

  const getStatusBadge = (review) => {
    if (review.action === 'APPROVE') {
      return <span className='badge badge-success'>✓ Approved</span>;
    } else if (review.action === 'REQUEST_CHANGES') {
      return <span className='badge badge-danger'>⚠ Changes Requested</span>;
    }
    return <span className='badge badge-info'>💬 Commented</span>;
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    const hours = Math.floor(diff / (1000 * 60 * 60));

    if (hours < 1) return 'Just now';
    if (hours < 24) return `${hours}h ago`;
    if (hours < 48) return 'Yesterday';
    return date.toLocaleDateString();
  };

  const filteredReviews = reviews.filter((r) => {
    if (filter === 'all') return true;
    if (filter === 'issues') return r.issues_found > 0;
    if (filter === 'security') return r.security_issues > 0;
    if (filter === 'approved') return r.action === 'APPROVE';
    return true;
  });

  return (
    <div className='pr-reviews'>
      <div className='reviews-header'>
        <h2>🔍 PR Reviews</h2>
        <p>Automated code reviews powered by AI</p>
      </div>

      {stats && (
        <div className='stats-grid'>
          <div className='stat-card'>
            <div className='stat-value'>{stats.total_reviews}</div>
            <div className='stat-label'>Total Reviews</div>
          </div>
          <div className='stat-card'>
            <div className='stat-value'>{stats.issues_found}</div>
            <div className='stat-label'>Issues Found</div>
          </div>
          <div className='stat-card highlight-red'>
            <div className='stat-value'>{stats.security_blocked}</div>
            <div className='stat-label'>Security Blocked</div>
          </div>
          <div className='stat-card'>
            <div className='stat-value'>{stats.this_week}</div>
            <div className='stat-label'>This Week</div>
          </div>
        </div>
      )}

      <div className='reviews-filters'>
        <button
          type='button'
          className={filter === 'all' ? 'active' : ''}
          onClick={() => setFilter('all')}
        >
          All
        </button>
        <button
          type='button'
          className={filter === 'issues' ? 'active' : ''}
          onClick={() => setFilter('issues')}
        >
          With Issues
        </button>
        <button
          type='button'
          className={filter === 'security' ? 'active' : ''}
          onClick={() => setFilter('security')}
        >
          🔴 Security
        </button>
        <button
          type='button'
          className={filter === 'approved' ? 'active' : ''}
          onClick={() => setFilter('approved')}
        >
          ✓ Approved
        </button>
      </div>

      {loading ? (
        <div className='loading'>Loading reviews...</div>
      ) : (
        <div className='reviews-list'>
          {filteredReviews.map((review) => (
            <div key={review.id} className='review-card'>
              <div className='review-main'>
                <div className='review-repo'>{review.repo}</div>
                <div className='review-title'>
                  <a
                    href={`https://github.com/${review.repo}/pull/${review.pr_number}`}
                    target='_blank'
                    rel='noopener noreferrer'
                  >
                    #{review.pr_number}: {review.title}
                  </a>
                </div>
                <div className='review-meta'>
                  {getStatusBadge(review)}
                  <span className='review-time'>{formatDate(review.reviewed_at)}</span>
                </div>
              </div>
              <div className='review-stats'>
                {review.security_issues > 0 && (
                  <span className='issue-badge security'>🔴 {review.security_issues}</span>
                )}
                {review.performance_issues > 0 && (
                  <span className='issue-badge performance'>⚡ {review.performance_issues}</span>
                )}
                {review.suggestions > 0 && (
                  <span className='issue-badge suggestion'>💡 {review.suggestions}</span>
                )}
                {review.issues_found === 0 && <span className='issue-badge clean'>✓ Clean</span>}
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && filteredReviews.length === 0 && (
        <div className='empty-state'>
          <p>No reviews match this filter.</p>
        </div>
      )}
    </div>
  );
}

PRReviews.propTypes = {
  apiUrl: PropTypes.string.isRequired,
};

export default PRReviews;
