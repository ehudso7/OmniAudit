import PropTypes from 'prop-types';
import { useCallback, useEffect, useState } from 'react';

function PRReviews({ apiUrl }) {
  const [reviews, setReviews] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all');
  const [selectedReview, setSelectedReview] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch reviews and stats in parallel
      const [reviewsRes, statsRes] = await Promise.all([
        fetch(`${apiUrl}/api/v1/reviews`),
        fetch(`${apiUrl}/api/v1/reviews/stats`)
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
      case 'security': return '#ef4444';
      case 'performance': return '#f59e0b';
      case 'quality': return '#8b5cf6';
      default: return '#3b82f6';
    }
  };

  if (loading && reviews.length === 0) {
    return (
      <div className='pr-reviews'>
        <div className='loading'>
          <div className='spinner'></div>
          <p>Loading reviews...</p>
        </div>
      </div>
    );
  }

  if (error && reviews.length === 0) {
    return (
      <div className='pr-reviews'>
        <div className='error'>
          <h2>Failed to load reviews</h2>
          <p>{error}</p>
          <button type='button' className='btn btn-primary' onClick={fetchData}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className='pr-reviews'>
      <div className='reviews-header'>
        <div className='reviews-header-content'>
          <h2>🔍 PR Reviews</h2>
          <p>Automated code reviews powered by AI</p>
        </div>
        <button type='button' className='btn btn-secondary btn-small' onClick={fetchData} disabled={loading}>
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
          With Issues ({reviews.filter(r => r.issues_found > 0).length})
        </button>
        <button
          type='button'
          className={filter === 'security' ? 'active' : ''}
          onClick={() => setFilter('security')}
        >
          🔴 Security ({reviews.filter(r => r.security_issues > 0).length})
        </button>
        <button
          type='button'
          className={filter === 'approved' ? 'active' : ''}
          onClick={() => setFilter('approved')}
        >
          ✓ Approved ({reviews.filter(r => r.action === 'APPROVE').length})
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
            onKeyDown={(e) => e.key === 'Enter' && setSelectedReview(selectedReview?.id === review.id ? null : review)}
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
                        style={{ backgroundColor: getSeverityColor(comment.type) + '20', color: getSeverityColor(comment.type) }}
                      >
                        {comment.type}
                      </span>
                      <span className='comment-location'>{comment.file}:{comment.line}</span>
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
