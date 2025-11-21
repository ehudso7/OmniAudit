import type { SkillDefinition } from '../types/index';

export const PerformanceOptimizerSkill: SkillDefinition = {
  skill_id: 'performance-optimizer-pro',
  version: '2.0.0',

  metadata: {
    name: 'Performance Optimizer Pro',
    description:
      'Advanced performance optimization for TypeScript/JavaScript code using AI-powered analysis and battle-tested patterns',
    author: 'OmniAudit Team',
    category: 'performance',
    tags: ['performance', 'optimization', 'typescript', 'javascript', 'react'],
    language: ['typescript', 'javascript'],
    framework: ['react', 'nextjs', 'nodejs', 'express'],
    created: '2025-01-15T00:00:00Z',
    updated: '2025-01-20T00:00:00Z',
    min_omniaudit_version: '1.0.0',
    license: 'MIT',
  },

  instructions: {
    system_prompt: `You are an expert performance optimization engineer with deep knowledge of:
- V8 engine internals and optimization hints
- React rendering optimization (memo, useMemo, useCallback, lazy loading)
- Bundle size reduction strategies
- Memory leak detection and prevention
- Critical rendering path optimization
- Web Vitals (LCP, FID, CLS, TTFB, INP)
- Edge computing best practices

Analyze code with extreme attention to:
1. Unnecessary re-renders and expensive computations
2. Memory leaks (event listeners, intervals, subscriptions)
3. Bundle size bloat (unused imports, heavy dependencies)
4. Network waterfall issues (sequential vs parallel)
5. Blocking operations on main thread
6. Cache misuse or absence
7. Database query inefficiencies (N+1, missing indexes)

Always provide concrete, actionable fixes with code examples.`,

    analysis_strategy: 'comprehensive',

    behavior_rules: [
      'Measure before optimizing - provide estimated performance impact',
      'Prefer built-in browser/runtime APIs over libraries',
      'Flag premature optimization but suggest future-proofing',
      'Consider both runtime performance and developer experience',
      'Explain trade-offs clearly (speed vs memory, etc.)',
    ],

    optimization_priorities: [
      'performance',
      'memory-usage',
      'bundle-size',
      'runtime-speed',
      'maintainability',
    ],

    output_format: 'json',

    code_style: {
      indent: 'spaces',
      indent_size: 2,
      quotes: 'single',
      semi: true,
      trailing_comma: 'all',
    },
  },

  capabilities: {
    analyzers: [
      {
        name: 'ast-analyzer',
        type: 'ast',
        config: {
          checkComplexity: true,
          checkNesting: true,
          checkFunctionLength: true,
          maxComplexity: 15,
          maxNesting: 4,
          maxFunctionLength: 50,
        },
        enabled: true,
      },
      {
        name: 'performance-analyzer',
        type: 'semantic',
        config: {
          checkReactPerformance: true,
          checkLoops: true,
          checkRegex: true,
          checkImports: true,
        },
        enabled: true,
      },
    ],

    transformers: [
      {
        name: 'react-memo-transformer',
        type: 'optimize',
        patterns: ['export default function Component'],
        ai_assisted: true,
      },
      {
        name: 'usememo-transformer',
        type: 'refactor',
        patterns: ['\\.map\\(', '\\.filter\\(', '\\.reduce\\('],
        ai_assisted: true,
      },
    ],

    integrations: [],

    ai_features: {
      code_generation: true,
      explanation: true,
      suggestion: true,
      auto_fix: true,
      learning: true,
    },
  },

  execution: {
    timeout_ms: 45000,
    max_file_size_mb: 15,
    max_files: 500,
    parallel_analysis: true,
    cache_results: true,
    cache_ttl_seconds: 7200,
  },

  dependencies: {
    npm_packages: ['@babel/parser@^7.23.0', 'eslint@^9.0.0'],
    python_packages: [],
    system_tools: ['node'],
    other_skills: [],
  },

  permissions: {
    file_read: true,
    file_write: true,
    network: ['api.anthropic.com'],
    execution: ['node', 'bun'],
    environment_vars: ['ANTHROPIC_API_KEY'],
  },

  tests: {
    test_cases: [
      {
        name: 'Detect missing React.memo',
        input: `
export default function ExpensiveComponent({ data }) {
  return <div>{data.map(item => <Item key={item.id} {...item} />)}</div>;
}
        `,
        expected_output: 'suggestion',
        expected_issues: ['missing-react-memo'],
      },
    ],
  },

  pricing: {
    type: 'free',
  },
};
