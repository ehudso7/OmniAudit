import type { SkillDefinition } from '../types/index';

export const TypeScriptExpertSkill: SkillDefinition = {
  skill_id: 'typescript-expert',
  version: '1.0.0',

  metadata: {
    name: 'TypeScript Expert',
    description: 'Advanced TypeScript type safety, patterns, and best practices',
    author: 'OmniAudit Team',
    category: 'quality',
    tags: ['typescript', 'types', 'generics', 'type-safety', 'static-analysis'],
    language: ['typescript'],
    created: '2025-01-21T00:00:00Z',
    updated: '2025-01-21T00:00:00Z',
    min_omniaudit_version: '1.0.0',
    license: 'MIT',
  },

  instructions: {
    system_prompt: `You are a TypeScript expert specializing in:
- Advanced type system features (generics, conditional types, mapped types)
- Type narrowing and guards
- Strict mode best practices
- Utility types and custom type helpers
- Type inference optimization
- Module resolution and declaration files
- Performance implications of type complexity
- Migration from JavaScript to TypeScript

Focus on:
1. Eliminating 'any' types
2. Proper generic constraints
3. Type narrowing techniques
4. Discriminated unions
5. Branded types for domain modeling
6. Type-level programming
7. Declaration file best practices
8. Strict configuration enforcement`,

    analysis_strategy: 'comprehensive',

    behavior_rules: [
      'Always prefer strict mode',
      'Avoid "any" - use "unknown" for truly unknown types',
      'Use const assertions for literal types',
      'Leverage type inference when possible',
      'Document complex types with JSDoc comments',
    ],

    optimization_priorities: ['maintainability', 'readability', 'security', 'testability'],

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
          checkTypeAnnotations: true,
          checkGenerics: true,
        },
        enabled: true,
      },
    ],

    transformers: [],

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
    npm_packages: ['typescript@^5.7.0', '@babel/parser@^7.23.0'],
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

  pricing: {
    type: 'free',
  },
};
