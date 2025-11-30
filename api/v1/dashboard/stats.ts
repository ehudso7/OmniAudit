import type { VercelRequest, VercelResponse } from '@vercel/node';

interface DayActivity {
  day: string;
  reviews: number;
}

interface RecentReview {
  id: string;
  repo: string;
  pr_number: number;
  title: string;
  author: string;
  action: string;
  reviewed_at: string;
}

interface TopRepository {
  name: string;
  reviews: number;
}

interface DashboardStats {
  stats: {
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
  };
  activity: DayActivity[];
  issues_breakdown: {
    security: number;
    performance: number;
    quality: number;
    suggestions: number;
  };
  top_repositories: TopRepository[];
  recent_reviews: RecentReview[];
}

// Generate activity data for the last 7 days
function generateActivityData(): DayActivity[] {
  const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const now = new Date();
  const activity: DayActivity[] = [];

  // Demo activity data - simulates realistic usage patterns
  const demoReviewCounts = [1, 1, 0, 1, 1, 1, 1]; // Reviews per day (total: 6)

  for (let i = 6; i >= 0; i--) {
    const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
    const dayName = days[date.getDay()];
    activity.push({
      day: dayName,
      reviews: demoReviewCounts[6 - i]
    });
  }

  return activity;
}

// Generate recent reviews for the dashboard
function generateRecentReviews(): RecentReview[] {
  const now = new Date();

  return [
    {
      id: 'rev-001',
      repo: 'acme/frontend',
      pr_number: 142,
      title: 'Add user authentication flow',
      author: 'johndoe',
      action: 'REQUEST_CHANGES',
      reviewed_at: new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString()
    },
    {
      id: 'rev-002',
      repo: 'acme/api-server',
      pr_number: 89,
      title: 'Optimize database queries',
      author: 'janedoe',
      action: 'APPROVE',
      reviewed_at: new Date(now.getTime() - 5 * 60 * 60 * 1000).toISOString()
    },
    {
      id: 'rev-003',
      repo: 'acme/frontend',
      pr_number: 141,
      title: 'Update dependencies',
      author: 'bobsmith',
      action: 'REQUEST_CHANGES',
      reviewed_at: new Date(now.getTime() - 12 * 60 * 60 * 1000).toISOString()
    },
    {
      id: 'rev-004',
      repo: 'acme/mobile-app',
      pr_number: 56,
      title: 'Implement push notifications',
      author: 'alicew',
      action: 'COMMENT',
      reviewed_at: new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString()
    },
    {
      id: 'rev-005',
      repo: 'acme/backend',
      pr_number: 234,
      title: 'Add rate limiting middleware',
      author: 'techops',
      action: 'APPROVE',
      reviewed_at: new Date(now.getTime() - 30 * 60 * 60 * 1000).toISOString()
    }
  ];
}

function generateDashboardStats(): DashboardStats {
  const totalReviews = 6;
  const issuesFound = 11;
  const securityIssues = 3;
  const performanceIssues = 3;
  const qualityIssues = 2;
  const suggestions = 3;
  const securityBlocked = 2;
  const approved = 3;

  return {
    stats: {
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
    },
    activity: generateActivityData(),
    issues_breakdown: {
      security: securityIssues,
      performance: performanceIssues,
      quality: qualityIssues,
      suggestions: suggestions
    },
    top_repositories: [
      { name: 'acme/frontend', reviews: 3 },
      { name: 'acme/api-server', reviews: 1 },
      { name: 'acme/mobile-app', reviews: 1 },
      { name: 'acme/backend', reviews: 1 }
    ],
    recent_reviews: generateRecentReviews()
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
    const dashboardStats = generateDashboardStats();
    return res.status(200).json(dashboardStats);
  } catch (error) {
    console.error('Failed to fetch dashboard stats:', error);
    return res.status(500).json({
      error: 'Failed to fetch dashboard statistics',
      stats: {
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
      },
      activity: [],
      issues_breakdown: { security: 0, performance: 0, quality: 0, suggestions: 0 },
      top_repositories: [],
      recent_reviews: []
    });
  }
}
