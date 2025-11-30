import type { VercelRequest, VercelResponse } from '@vercel/node';

interface ReviewComment {
  type: string;
  line: number;
  file: string;
  message: string;
}

interface Review {
  id: string;
  repo: string;
  owner: string;
  repo_name: string;
  pr_number: number;
  title: string;
  author: string;
  status: string;
  issues_found: number;
  security_issues: number;
  performance_issues: number;
  quality_issues: number;
  suggestions: number;
  reviewed_at: string;
  action: string;
  comments: ReviewComment[];
}

// Generate demo reviews with relative timestamps
function generateDemoReviews(): Review[] {
  const now = new Date();

  return [
    {
      id: 'rev-001',
      repo: 'acme/frontend',
      owner: 'acme',
      repo_name: 'frontend',
      pr_number: 142,
      title: 'Add user authentication flow',
      author: 'johndoe',
      status: 'reviewed',
      issues_found: 3,
      security_issues: 1,
      performance_issues: 1,
      quality_issues: 0,
      suggestions: 1,
      reviewed_at: new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString(),
      action: 'REQUEST_CHANGES',
      comments: [
        { type: 'security', line: 45, file: 'auth.js', message: 'Potential XSS vulnerability in user input handling' },
        { type: 'performance', line: 128, file: 'login.js', message: 'Consider memoizing this expensive computation' },
        { type: 'suggestion', line: 67, file: 'auth.js', message: 'Add error handling for network failures' }
      ]
    },
    {
      id: 'rev-002',
      repo: 'acme/api-server',
      owner: 'acme',
      repo_name: 'api-server',
      pr_number: 89,
      title: 'Optimize database queries',
      author: 'janedoe',
      status: 'reviewed',
      issues_found: 0,
      security_issues: 0,
      performance_issues: 0,
      quality_issues: 0,
      suggestions: 0,
      reviewed_at: new Date(now.getTime() - 5 * 60 * 60 * 1000).toISOString(),
      action: 'APPROVE',
      comments: []
    },
    {
      id: 'rev-003',
      repo: 'acme/frontend',
      owner: 'acme',
      repo_name: 'frontend',
      pr_number: 141,
      title: 'Update dependencies',
      author: 'bobsmith',
      status: 'reviewed',
      issues_found: 5,
      security_issues: 2,
      performance_issues: 0,
      quality_issues: 1,
      suggestions: 2,
      reviewed_at: new Date(now.getTime() - 12 * 60 * 60 * 1000).toISOString(),
      action: 'REQUEST_CHANGES',
      comments: [
        { type: 'security', line: 1, file: 'package.json', message: 'lodash 4.17.15 has known vulnerabilities - update to 4.17.21' },
        { type: 'security', line: 12, file: 'package.json', message: 'axios 0.19.0 is vulnerable to SSRF attacks' },
        { type: 'quality', line: 45, file: 'utils.js', message: 'Unused import detected' }
      ]
    },
    {
      id: 'rev-004',
      repo: 'acme/mobile-app',
      owner: 'acme',
      repo_name: 'mobile-app',
      pr_number: 56,
      title: 'Implement push notifications',
      author: 'alicew',
      status: 'reviewed',
      issues_found: 1,
      security_issues: 0,
      performance_issues: 1,
      quality_issues: 0,
      suggestions: 0,
      reviewed_at: new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString(),
      action: 'COMMENT',
      comments: [
        { type: 'performance', line: 89, file: 'notifications.ts', message: 'Large payload may cause delays on slow networks' }
      ]
    },
    {
      id: 'rev-005',
      repo: 'acme/backend',
      owner: 'acme',
      repo_name: 'backend',
      pr_number: 234,
      title: 'Add rate limiting middleware',
      author: 'techops',
      status: 'reviewed',
      issues_found: 0,
      security_issues: 0,
      performance_issues: 0,
      quality_issues: 0,
      suggestions: 0,
      reviewed_at: new Date(now.getTime() - 30 * 60 * 60 * 1000).toISOString(),
      action: 'APPROVE',
      comments: []
    },
    {
      id: 'rev-006',
      repo: 'acme/frontend',
      owner: 'acme',
      repo_name: 'frontend',
      pr_number: 140,
      title: 'Fix responsive layout issues',
      author: 'designteam',
      status: 'reviewed',
      issues_found: 2,
      security_issues: 0,
      performance_issues: 1,
      quality_issues: 1,
      suggestions: 0,
      reviewed_at: new Date(now.getTime() - 48 * 60 * 60 * 1000).toISOString(),
      action: 'APPROVE',
      comments: [
        { type: 'performance', line: 23, file: 'styles.css', message: 'Consider using CSS containment for better rendering' },
        { type: 'quality', line: 156, file: 'Layout.tsx', message: 'Magic number - consider using a constant' }
      ]
    }
  ];
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
    const { repo, action, limit = '50', offset = '0' } = req.query;

    let reviews = generateDemoReviews();

    // Apply filters
    if (repo && typeof repo === 'string') {
      reviews = reviews.filter(r => r.repo === repo);
    }
    if (action && typeof action === 'string') {
      reviews = reviews.filter(r => r.action.toLowerCase() === action.toLowerCase());
    }

    // Sort by reviewed_at descending
    reviews.sort((a, b) => new Date(b.reviewed_at).getTime() - new Date(a.reviewed_at).getTime());

    // Calculate total before pagination
    const total = reviews.length;

    // Apply pagination
    const limitNum = Math.min(parseInt(limit as string, 10) || 50, 100);
    const offsetNum = parseInt(offset as string, 10) || 0;
    reviews = reviews.slice(offsetNum, offsetNum + limitNum);

    return res.status(200).json({
      reviews,
      total,
      limit: limitNum,
      offset: offsetNum
    });
  } catch (error) {
    console.error('Failed to fetch reviews:', error);
    return res.status(500).json({
      error: 'Failed to fetch reviews',
      reviews: [],
      total: 0
    });
  }
}
