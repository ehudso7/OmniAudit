import type { VercelRequest, VercelResponse } from '@vercel/node';

interface Finding {
  type: string;
  severity: string;
  title: string;
  description: string;
  line: number;
  code: string;
  fix: string;
}

interface AnalysisResult {
  success: boolean;
  score: number;
  language: string;
  skills_applied: string[];
  summary: {
    security: number;
    performance: number;
    quality: number;
    total_issues: number;
  };
  findings: Finding[];
  timestamp: string;
}

// Security patterns to detect
const SECURITY_PATTERNS = [
  {
    pattern: /eval\s*\(/gi,
    title: 'Dangerous eval() usage',
    description: 'eval() can execute arbitrary code and is a security risk',
    severity: 'critical',
    fix: 'Avoid using eval(). Use safer alternatives like JSON.parse() for data parsing.',
  },
  {
    pattern: /innerHTML\s*=/gi,
    title: 'innerHTML assignment detected',
    description: 'Direct innerHTML assignment can lead to XSS vulnerabilities',
    severity: 'high',
    fix: 'Use textContent for text or sanitize HTML input before using innerHTML.',
  },
  {
    pattern: /document\.write\s*\(/gi,
    title: 'document.write() usage',
    description: 'document.write() can overwrite the entire document and is vulnerable to injection',
    severity: 'medium',
    fix: 'Use DOM manipulation methods like appendChild() or innerHTML with proper sanitization.',
  },
  {
    pattern: /password\s*=\s*["'][^"']+["']/gi,
    title: 'Hardcoded password detected',
    description: 'Passwords should never be hardcoded in source code',
    severity: 'critical',
    fix: 'Use environment variables or a secure secrets manager for sensitive credentials.',
  },
  {
    pattern: /api[_-]?key\s*=\s*["'][^"']+["']/gi,
    title: 'Hardcoded API key detected',
    description: 'API keys should not be hardcoded in source code',
    severity: 'high',
    fix: 'Store API keys in environment variables or secure vault.',
  },
  {
    pattern: /SELECT\s+\*?\s+FROM\s+.*\+\s*['"]/gi,
    title: 'Potential SQL injection',
    description: 'String concatenation in SQL queries can lead to SQL injection attacks',
    severity: 'critical',
    fix: 'Use parameterized queries or prepared statements instead of string concatenation.',
  },
  {
    pattern: /exec\s*\(\s*[^)]*\+/gi,
    title: 'Command injection risk',
    description: 'Dynamic command execution with string concatenation is dangerous',
    severity: 'critical',
    fix: 'Validate and sanitize all inputs, use allowlists for permitted commands.',
  },
];

// Performance patterns to detect
const PERFORMANCE_PATTERNS = [
  {
    pattern: /for\s*\([^)]*\.length/gi,
    title: 'Array length in loop condition',
    description: 'Accessing .length in every iteration can be inefficient for large arrays',
    severity: 'low',
    fix: 'Cache the array length in a variable before the loop.',
  },
  {
    pattern: /console\.(log|debug|info|warn|error)\s*\(/gi,
    title: 'Console statement in code',
    description: 'Console statements should be removed in production code',
    severity: 'low',
    fix: 'Remove console statements or use a proper logging library with log levels.',
  },
  {
    pattern: /setTimeout\s*\([^,]+,\s*0\s*\)/gi,
    title: 'setTimeout with 0 delay',
    description: 'Using setTimeout with 0ms delay for async behavior is an anti-pattern',
    severity: 'low',
    fix: 'Use requestAnimationFrame, queueMicrotask, or proper async/await patterns.',
  },
  {
    pattern: /\.forEach\s*\([^)]*=>\s*{[^}]*await/gi,
    title: 'Await inside forEach',
    description: 'Using await inside forEach does not wait for each iteration',
    severity: 'medium',
    fix: 'Use for...of loop or Promise.all() with map() for parallel execution.',
  },
];

// Quality patterns to detect
const QUALITY_PATTERNS = [
  {
    pattern: /var\s+/g,
    title: 'Usage of var keyword',
    description: 'var has function scope which can lead to unexpected behavior',
    severity: 'low',
    fix: 'Use let or const instead of var for block-scoped variables.',
  },
  {
    pattern: /==(?!=)/g,
    title: 'Loose equality operator',
    description: 'Loose equality (==) can lead to unexpected type coercion',
    severity: 'low',
    fix: 'Use strict equality (===) for predictable comparisons.',
  },
  {
    pattern: /catch\s*\(\s*\w+\s*\)\s*{\s*}/g,
    title: 'Empty catch block',
    description: 'Empty catch blocks silently swallow errors',
    severity: 'medium',
    fix: 'Handle errors properly or at least log them for debugging.',
  },
  {
    pattern: /TODO|FIXME|HACK|XXX/gi,
    title: 'Unresolved code comment',
    description: 'Code contains TODO/FIXME markers that should be addressed',
    severity: 'low',
    fix: 'Address the TODO/FIXME or create a tracked issue for it.',
  },
];

function findLineNumber(code: string, match: RegExpMatchArray): number {
  if (match.index == null) return 0;
  const beforeMatch = code.substring(0, match.index);
  return (beforeMatch.match(/\n/g) || []).length + 1;
}

function detectLanguage(code: string): string {
  if (code.includes('interface ') || code.includes(': string') || code.includes(': number') || code.includes('<T>')) {
    return 'typescript';
  }
  if (code.includes('def ') || code.includes('import ') && code.includes(':') && !code.includes('from \'')) {
    return 'python';
  }
  if (code.includes('func ') || code.includes('package ')) {
    return 'go';
  }
  return 'javascript';
}

function analyzeCode(code: string, skills: string[]): AnalysisResult {
  const findings: Finding[] = [];
  const summary = {
    security: 0,
    performance: 0,
    quality: 0,
    total_issues: 0,
  };

  // Run security analysis
  if (skills.some(s => s.toLowerCase().includes('security'))) {
    for (const pattern of SECURITY_PATTERNS) {
      const matches = code.matchAll(pattern.pattern);
      for (const match of matches) {
        findings.push({
          type: 'security',
          severity: pattern.severity,
          title: pattern.title,
          description: pattern.description,
          line: findLineNumber(code, match),
          code: match[0],
          fix: pattern.fix,
        });
        summary.security++;
        summary.total_issues++;
      }
    }
  }

  // Run performance analysis
  if (skills.some(s => s.toLowerCase().includes('performance'))) {
    for (const pattern of PERFORMANCE_PATTERNS) {
      const matches = code.matchAll(pattern.pattern);
      for (const match of matches) {
        findings.push({
          type: 'performance',
          severity: pattern.severity,
          title: pattern.title,
          description: pattern.description,
          line: findLineNumber(code, match),
          code: match[0],
          fix: pattern.fix,
        });
        summary.performance++;
        summary.total_issues++;
      }
    }
  }

  // Run quality analysis
  if (skills.some(s => s.toLowerCase().includes('quality') || s.toLowerCase().includes('code'))) {
    for (const pattern of QUALITY_PATTERNS) {
      const matches = code.matchAll(pattern.pattern);
      for (const match of matches) {
        findings.push({
          type: 'quality',
          severity: pattern.severity,
          title: pattern.title,
          description: pattern.description,
          line: findLineNumber(code, match),
          code: match[0],
          fix: pattern.fix,
        });
        summary.quality++;
        summary.total_issues++;
      }
    }
  }

  // Calculate score
  let score = 100;
  for (const finding of findings) {
    switch (finding.severity) {
      case 'critical':
        score -= 15;
        break;
      case 'high':
        score -= 10;
        break;
      case 'medium':
        score -= 5;
        break;
      case 'low':
        score -= 2;
        break;
    }
  }
  score = Math.max(0, score);

  return {
    success: true,
    score,
    language: detectLanguage(code),
    skills_applied: skills,
    summary,
    findings,
    timestamp: new Date().toISOString(),
  };
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With');

  // Handle OPTIONS for CORS preflight
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  // Only allow POST
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { code, language, skills = [] } = req.body;

    // Validate required fields
    if (!code) {
      return res.status(400).json({
        success: false,
        error: 'Missing required field: code',
      });
    }

    // Default skills if none provided
    const activeSkills = skills.length > 0 ? skills : ['security-auditor', 'performance-optimizer-pro', 'code-quality'];

    // Run analysis
    const result = analyzeCode(code, activeSkills);

    // Override language if explicitly provided
    if (language) {
      result.language = language;
    }

    return res.status(200).json(result);
  } catch (error) {
    console.error('Analysis failed:', error);
    return res.status(500).json({
      success: false,
      error: 'An error occurred during analysis',
      score: 0,
      summary: { security: 0, performance: 0, quality: 0, total_issues: 0 },
      findings: [],
      timestamp: new Date().toISOString(),
    });
  }
}
