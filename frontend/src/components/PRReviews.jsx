import PropTypes from 'prop-types';
import { useCallback, useEffect, useState } from 'react';

// Demo data for when backend is unavailable
const DEMO_REVIEWS = [
  {
    id: 'demo-1',
    repo: 'acme/web-app',
    pr_number: 42,
    title: 'Add user authentication flow',
    author: 'developer',
    action: 'REQUEST_CHANGES',
    reviewed_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    issues_found: 3,
    security_issues: 1,
    performance_issues: 1,
    quality_issues: 1,
    suggestions: 2,
    comments: [
      { type: 'security', file: 'src/auth.js', line: 45, message: 'Potential SQL injection vulnerability in user input handling' },
      { type: 'performance', file: 'src/api.js', line: 128, message: 'Consider caching this API response to reduce latency' },
      { type: 'quality', file: 'src/utils.js', line: 23, message: 'Function complexity exceeds recommended threshold' },
    ],
  },
  {
    id: 'demo-2',
    repo: 'acme/api-service',
    pr_number: 108,
    title: 'Optimize database queries',
    author: 'backend-dev',
    action: 'APPROVE',
    reviewed_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
    issues_found: 0,
    security_issues: 0,
    performance_issues: 0,
    quality_issues: 0,
    suggestions: 1,
    comments: [],
  },
  {
    id: 'demo-3',
    repo: 'acme/mobile-app',
    pr_number: 256,
    title: 'Update dependencies and fix security vulnerabilities',
    author: 'security-team',
    action: 'COMMENT',
    reviewed_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    issues_found: 2,
    security_issues: 2,
    performance_issues: 0,
    quality_issues: 0,
    suggestions: 0,
    comments: [
      { type: 'security', file: 'package.json', line: 15, message: 'Outdated dependency with known CVE-2024-1234' },
      { type: 'security', file: 'package.json', line: 22, message: 'Dependency has critical security advisory' },
    ],
  },
];

const DEMO_STATS = {
  total_reviews: 47,
  issues_found: 123,
  security_blocked: 8,
  this_week: 12,
  approval_rate: 72,
  repos_connected: 5,
};

function PRReviews({ apiUrl }) {
  const [reviews, setReviews] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all');
  const [selectedReview, setSelectedReview] = useState(null);
  const [demoMode, setDemoMode] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch reviews and stats in parallel
      const [reviewsRes, statsRes] = await Promise.all([
        fetch(`${apiUrl}/api/v1/reviews`),
        fetch(`${apiUrl}/api/v1/reviews/stats`),
      ]);

      if (!reviewsRes.ok || !statsRes.ok) {
        throw new Error('Failed to fetch data');
      }

      const reviewsData = await reviewsRes.json();
      const statsData = await statsRes.json();

      setReviews(reviewsData.reviews || []);
      setStats(statsData);
    } catch (err) {
      console.error('Failed to fetch reviews:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [apiUrl]);

  useEffect(() => {
    fetchData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const getStatusBadge = (review) => {
    if (review.action === 'APPROVE') {
      return <span className='badge badge-success'>✓ Approved</span>;
    }
    if (review.action === 'REQUEST_CHANGES') {
      return <span className='badge badge-danger'>⚠ Changes Requested</span>;
    }
    return <span className='badge badge-info'>💬 Commented</span>;
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor(diff / (1000 * 60));

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
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

  const getSeverityColor = (type) => {
    switch (type) {
      case 'security':
        return '#ef4444';
      case 'performance':
        return '#f59e0b';
      case 'quality':
        return '#8b5cf6';
      default:
        return '#3b82f6';
    }
  };

  if (loading && reviews.length === 0) {
    return (
      <div className='pr-reviews'>
        <div className='loading'>
          <div className='spinner' />
          <p>Loading reviews...</p>
        </div>
      </div>
    );
  }

  const loadDemoData = () => {
    setDemoMode(true);
    setReviews(DEMO_REVIEWS);
    setStats(DEMO_STATS);
    setError(null);
    setLoading(false);
  };

  if (error && reviews.length === 0 && !demoMode) {
    return (
      <div className='pr-reviews'>
        <div className='error'>
          <h2>Backend API Unavailable</h2>
          <p style={{ marginBottom: '1rem' }}>
            The OmniAudit API server is not running or not accessible.
          </p>
          <p style={{ fontSize: '0.9rem', color: '#666', marginBottom: '1.5rem' }}>
            To use the full application, start the backend server with:<br />
            <code style={{ background: '#f0f0f0', padding: '0.25rem 0.5rem', borderRadius: '4px' }}>
              cd python-app && uvicorn omniaudit.api.main:app --reload
            </code>
          </p>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
            <button type='button' className='btn btn-primary' onClick={fetchData}>
              Retry Connection
            </button>
            <button type='button' className='btn btn-secondary' onClick={loadDemoData}>
              View Demo
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className='pr-reviews'>
      {demoMode && (
        <div className='demo-banner' style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          padding: '0.75rem 1rem',
          borderRadius: '8px',
          marginBottom: '1rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <span>
            <strong>Demo Mode</strong> — Viewing sample data. Connect to the API for live reviews.
          </span>
          <button
            type='button'
            onClick={() => {
              setDemoMode(false);
              fetchData();
            }}
            style={{
              background: 'rgba(255,255,255,0.2)',
              border: 'none',
              color: 'white',
              padding: '0.5rem 1rem',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            Connect to API
          </button>
        </div>
      )}
      <div className='reviews-header'>
        <div className='reviews-header-content'>
          <h2>🔍 PR Reviews</h2>
          <p>Automated code reviews powered by AI</p>
        </div>
        <button type='button' className='btn btn-secondary btn-small' onClick={demoMode ? loadDemoData : fetchData} disabled={loading}>
        <button
          type='button'
          className='btn btn-secondary btn-small'
          onClick={fetchData}
          disabled={loading}
        >
          {loading ? '⟳' : '↻'} Refresh
        </button>
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
          <div className='stat-card'>
            <div className='stat-value'>{stats.approval_rate}%</div>
            <div className='stat-label'>Approval Rate</div>
          </div>
          <div className='stat-card'>
            <div className='stat-value'>{stats.repos_connected}</div>
            <div className='stat-label'>Repositories</div>
          </div>
        </div>
      )}

      <div className='reviews-filters'>
        <button
          type='button'
          className={filter === 'all' ? 'active' : ''}
          onClick={() => setFilter('all')}
        >
          All ({reviews.length})
        </button>
        <button
          type='button'
          className={filter === 'issues' ? 'active' : ''}
          onClick={() => setFilter('issues')}
        >
          With Issues ({reviews.filter((r) => r.issues_found > 0).length})
        </button>
        <button
          type='button'
          className={filter === 'security' ? 'active' : ''}
          onClick={() => setFilter('security')}
        >
          🔴 Security ({reviews.filter((r) => r.security_issues > 0).length})
        </button>
        <button
          type='button'
          className={filter === 'approved' ? 'active' : ''}
          onClick={() => setFilter('approved')}
        >
          ✓ Approved ({reviews.filter((r) => r.action === 'APPROVE').length})
        </button>
      </div>

      <div className='reviews-list'>
        {filteredReviews.map((review) => (
          <div
            key={review.id}
            className={`review-card ${selectedReview?.id === review.id ? 'selected' : ''}`}
            onClick={() => setSelectedReview(selectedReview?.id === review.id ? null : review)}
            role='button'
            tabIndex={0}
            onKeyDown={(e) =>
              e.key === 'Enter' &&
              setSelectedReview(selectedReview?.id === review.id ? null : review)
            }
          >
            <div className='review-main'>
              <div className='review-repo'>{review.repo}</div>
              <div className='review-title'>
                <a
                  href={`https://github.com/${review.repo}/pull/${review.pr_number}`}
                  target='_blank'
                  rel='noopener noreferrer'
                  onClick={(e) => e.stopPropagation()}
                >
                  #{review.pr_number}: {review.title}
                </a>
              </div>
              <div className='review-author'>by {review.author}</div>
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
              {review.quality_issues > 0 && (
                <span className='issue-badge quality'>📋 {review.quality_issues}</span>
              )}
              {review.suggestions > 0 && (
                <span className='issue-badge suggestion'>💡 {review.suggestions}</span>
              )}
              {review.issues_found === 0 && <span className='issue-badge clean'>✓ Clean</span>}
            </div>

            {/* Expanded details */}
            {selectedReview?.id === review.id && review.comments && review.comments.length > 0 && (
              <div className='review-details' onClick={(e) => e.stopPropagation()}>
                <h4>Review Comments</h4>
                <div className='comments-list'>
                  {review.comments.map((comment, idx) => (
                    <div key={idx} className='comment-item'>
                      <span
                        className='comment-type'
                        style={{
                          backgroundColor: `${getSeverityColor(comment.type)}20`,
                          color: getSeverityColor(comment.type),
                        }}
                      >
                        {comment.type}
                      </span>
                      <span className='comment-location'>
                        {comment.file}:{comment.line}
                      </span>
                      <p className='comment-message'>{comment.message}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {!loading && filteredReviews.length === 0 && (
        <div className='empty-state'>
          <p>No reviews match this filter.</p>
          <button type='button' className='btn btn-secondary' onClick={() => setFilter('all')}>
            Show All Reviews
          </button>
        </div>
      )}
    </div>
  );
}

PRReviews.propTypes = {
  apiUrl: PropTypes.string.isRequired,
};

export default PRReviews;
