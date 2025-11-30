import type { VercelRequest, VercelResponse } from '@vercel/node';

interface Skill {
  id: string;
  name: string;
  description: string;
  category: string;
  version: string;
  tags: string[];
  languages: string[];
  frameworks: string[];
}

// Built-in skills for OmniAudit
const BUILTIN_SKILLS: Skill[] = [
  {
    id: 'security-auditor',
    name: 'Security Auditor',
    description: 'Detects vulnerabilities, SQL injection, XSS, hardcoded secrets, and security misconfigurations',
    category: 'Security',
    version: '1.0.0',
    tags: ['security', 'vulnerabilities', 'owasp'],
    languages: ['javascript', 'typescript', 'python', 'java'],
    frameworks: ['react', 'node', 'express', 'django'],
  },
  {
    id: 'performance-optimizer-pro',
    name: 'Performance Optimizer',
    description: 'Identifies performance bottlenecks, memory leaks, and optimization opportunities',
    category: 'Performance',
    version: '1.0.0',
    tags: ['performance', 'optimization', 'speed'],
    languages: ['javascript', 'typescript', 'python'],
    frameworks: ['react', 'vue', 'angular', 'node'],
  },
  {
    id: 'code-quality',
    name: 'Code Quality',
    description: 'Checks for code smells, complexity issues, maintainability, and best practices',
    category: 'Quality',
    version: '1.0.0',
    tags: ['quality', 'maintainability', 'clean-code'],
    languages: ['javascript', 'typescript', 'python', 'java', 'go'],
    frameworks: ['all'],
  },
  {
    id: 'react-best-practices',
    name: 'React Best Practices',
    description: 'Reviews React patterns, hooks usage, component structure, and performance optimizations',
    category: 'React',
    version: '1.0.0',
    tags: ['react', 'hooks', 'components'],
    languages: ['javascript', 'typescript'],
    frameworks: ['react', 'next'],
  },
  {
    id: 'typescript-expert',
    name: 'TypeScript Expert',
    description: 'Validates types, generics, type guards, and TypeScript patterns',
    category: 'TypeScript',
    version: '1.0.0',
    tags: ['typescript', 'types', 'generics'],
    languages: ['typescript'],
    frameworks: ['all'],
  },
  {
    id: 'architecture-advisor',
    name: 'Architecture Advisor',
    description: 'Reviews code structure, design patterns, and suggests architectural improvements',
    category: 'Architecture',
    version: '1.0.0',
    tags: ['architecture', 'design-patterns', 'structure'],
    languages: ['javascript', 'typescript', 'python', 'java'],
    frameworks: ['all'],
  },
  {
    id: 'api-design',
    name: 'API Design',
    description: 'Reviews REST/GraphQL endpoints, data contracts, and API best practices',
    category: 'API',
    version: '1.0.0',
    tags: ['api', 'rest', 'graphql'],
    languages: ['javascript', 'typescript', 'python'],
    frameworks: ['express', 'fastapi', 'django'],
  },
  {
    id: 'test-coverage',
    name: 'Test Coverage',
    description: 'Analyzes test coverage, test quality, and suggests missing test cases',
    category: 'Testing',
    version: '1.0.0',
    tags: ['testing', 'coverage', 'quality'],
    languages: ['javascript', 'typescript', 'python'],
    frameworks: ['jest', 'mocha', 'pytest'],
  },
  {
    id: 'documentation',
    name: 'Documentation',
    description: 'Checks for missing documentation, JSDoc comments, and README quality',
    category: 'Docs',
    version: '1.0.0',
    tags: ['documentation', 'jsdoc', 'readme'],
    languages: ['javascript', 'typescript', 'python'],
    frameworks: ['all'],
  },
  {
    id: 'accessibility',
    name: 'Accessibility',
    description: 'Validates WCAG compliance, ARIA usage, and accessibility patterns',
    category: 'A11y',
    version: '1.0.0',
    tags: ['accessibility', 'wcag', 'aria'],
    languages: ['javascript', 'typescript'],
    frameworks: ['react', 'vue', 'angular'],
  },
  {
    id: 'dependency-scanner',
    name: 'Dependency Scanner',
    description: 'Scans for vulnerable dependencies, outdated packages, and license issues',
    category: 'Dependencies',
    version: '1.0.0',
    tags: ['dependencies', 'vulnerabilities', 'npm'],
    languages: ['javascript', 'typescript', 'python'],
    frameworks: ['all'],
  },
  {
    id: 'error-handling',
    name: 'Error Handling',
    description: 'Checks for proper error handling, edge cases, and exception management',
    category: 'Reliability',
    version: '1.0.0',
    tags: ['errors', 'exceptions', 'reliability'],
    languages: ['javascript', 'typescript', 'python', 'java'],
    frameworks: ['all'],
  },
];

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    let { id } = req.query;

    // Handle array case - take first value
    if (Array.isArray(id)) {
      id = id[0];
    }

    // If ID provided, return specific skill
    if (id && typeof id === 'string') {
      const skill = BUILTIN_SKILLS.find(s => s.id === id);

      if (!skill) {
        return res.status(404).json({
          success: false,
          error: 'Skill not found',
        });
      }

      return res.status(200).json({
        success: true,
        skill,
      });
    }

    // Otherwise return all skills
    return res.status(200).json({
      success: true,
      skills: BUILTIN_SKILLS,
      count: BUILTIN_SKILLS.length,
    });
  } catch (error) {
    console.error('Failed to fetch skills:', error);
    return res.status(500).json({
      success: false,
      error: 'An error occurred while fetching skills',
    });
  }
}
