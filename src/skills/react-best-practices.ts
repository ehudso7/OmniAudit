import type { SkillDefinition } from '../types/index';

export const ReactBestPracticesSkill: SkillDefinition = {
  skill_id: 'react-best-practices',
  version: '1.0.0',

  metadata: {
    name: 'React Best Practices',
    description: 'Enforce React best practices, hooks rules, and modern patterns',
    author: 'OmniAudit Team',
    category: 'quality',
    tags: ['react', 'hooks', 'best-practices', 'patterns', 'jsx'],
    language: ['typescript', 'javascript'],
    framework: ['react', 'nextjs'],
    created: '2025-01-21T00:00:00Z',
    updated: '2025-01-21T00:00:00Z',
    min_omniaudit_version: '1.0.0',
    license: 'MIT',
  },

  instructions: {
    system_prompt: `You are a React expert specializing in:
- React Hooks best practices and rules
- Component composition patterns
- State management strategies
- Performance optimization (memo, useMemo, useCallback)
- Accessibility (a11y) best practices
- Testing patterns (React Testing Library)
- TypeScript integration with React
- Modern React patterns (Server Components, Suspense, etc.)

Focus on:
1. Proper hooks usage (dependencies, custom hooks)
2. Component architecture and composition
3. Props drilling and state lifting
4. Accessibility issues
5. Key prop usage in lists
6. Event handler optimization
7. Ref usage and DOM access
8. Context API best practices`,

    analysis_strategy: 'targeted',

    behavior_rules: [
      'Follow official React documentation and Dan Abramov guidelines',
      'Emphasize accessibility in all suggestions',
      'Prefer composition over inheritance',
      'Suggest custom hooks for reusable logic',
      'Recommend TypeScript for type safety',
    ],

    optimization_priorities: [
      'maintainability',
      'readability',
      'performance',
      'testability',
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
          checkReactPatterns: true,
          checkHooksRules: true,
          checkA11y: true,
        },
        enabled: true,
      },
      {
        name: 'performance-analyzer',
        type: 'semantic',
        config: {
          checkReactPerformance: true,
        },
        enabled: true,
      },
    ],

    transformers: [
      {
        name: 'react-memo-transformer',
        type: 'optimize',
        patterns: ['React.memo', 'useMemo', 'useCallback'],
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
    timeout_ms: 30000,
    max_file_size_mb: 10,
    max_files: 1000,
    parallel_analysis: true,
    cache_results: true,
    cache_ttl_seconds: 3600,
  },

  dependencies: {
    npm_packages: ['@babel/parser@^7.23.0'],
    python_packages: [],
    system_tools: ['node'],
    other_skills: ['performance-optimizer-pro'],
  },

  permissions: {
    file_read: true,
    file_write: true,
    network: ['api.anthropic.com'],
    execution: ['node', 'bun'],
    environment_vars: ['ANTHROPIC_API_KEY'],
  },

  pricing: {
    type: 'free',
  },
};
