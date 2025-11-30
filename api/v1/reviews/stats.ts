import type { VercelRequest, VercelResponse } from '@vercel/node';

interface ReviewStats {
  total_reviews: number;
  issues_found: number;
  security_issues: number;
  performance_issues: number;
  security_blocked: number;
  this_week: number;
  this_month: number;
  approval_rate: number;
  repos_connected: number;
  avg_issues_per_pr: number;
}

// Generate consistent demo stats
function generateDemoStats(): ReviewStats {
  // These would normally come from a database
  const totalReviews = 6;
  const issuesFound = 11;
  const securityIssues = 3;
  const performanceIssues = 3;
  const securityBlocked = 2;
  const approved = 3;

  return {
    total_reviews: totalReviews,
    issues_found: issuesFound,
    security_issues: securityIssues,
    performance_issues: performanceIssues,
    security_blocked: securityBlocked,
    this_week: 5,
    this_month: 6,
    approval_rate: Math.round((approved / totalReviews) * 100 * 10) / 10,
    repos_connected: 4,
    avg_issues_per_pr: Math.round((issuesFound / totalReviews) * 10) / 10
  };
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const stats = generateDemoStats();
    return res.status(200).json(stats);
  } catch (error) {
    console.error('Failed to fetch review stats:', error);
    return res.status(500).json({
      error: 'Failed to fetch statistics',
      total_reviews: 0,
      issues_found: 0,
      security_issues: 0,
      performance_issues: 0,
      security_blocked: 0,
      this_week: 0,
      this_month: 0,
      approval_rate: 0,
      repos_connected: 0,
      avg_issues_per_pr: 0
    });
  }
}
