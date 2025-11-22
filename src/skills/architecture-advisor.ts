import type { SkillDefinition } from '../types/index';

export const ArchitectureAdvisorSkill: SkillDefinition = {
  skill_id: 'architecture-advisor',
  version: '1.0.0',

  metadata: {
    name: 'Architecture Advisor',
    description: 'Software architecture patterns, SOLID principles, and system design best practices',
    author: 'OmniAudit Team',
    category: 'architecture',
    tags: ['architecture', 'design-patterns', 'solid', 'clean-code', 'refactoring'],
    language: ['typescript', 'javascript', 'python', 'java', 'rust', 'go'],
    created: '2025-01-21T00:00:00Z',
    updated: '2025-01-21T00:00:00Z',
    min_omniaudit_version: '1.0.0',
    license: 'MIT',
  },

  instructions: {
    system_prompt: `You are a software architect with expertise in:
- SOLID principles and design patterns
- Domain-Driven Design (DDD)
- Clean Architecture / Hexagonal Architecture
- Microservices and distributed systems
- Event-driven architecture
- CQRS and Event Sourcing
- API design (REST, GraphQL, gRPC)
- Database design and normalization
- Code organization and module boundaries

Focus on:
1. Single Responsibility Principle violations
2. Tight coupling and poor dependency management
3. Missing abstractions or over-abstraction
4. God classes and anemic domain models
5. Circular dependencies
6. Inappropriate intimacy between modules
7. Feature envy and data clumps
8. Violation of Law of Demeter`,

    analysis_strategy: 'comprehensive',

    behavior_rules: [
      'Favor composition over inheritance',
      'Depend on abstractions, not concretions',
      'Keep modules loosely coupled and highly cohesive',
      'Separate concerns and responsibilities',
      'Make dependencies explicit',
      'Follow the principle of least surprise',
    ],

    optimization_priorities: [
      'maintainability',
      'readability',
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
          checkComplexity: true,
          checkCoupling: true,
          checkCohesion: true,
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
      auto_fix: false, // Architecture changes require careful planning
      learning: true,
    },
  },

  execution: {
    timeout_ms: 60000,
    max_file_size_mb: 20,
    max_files: 5000,
    parallel_analysis: true,
    cache_results: true,
    cache_ttl_seconds: 7200,
  },

  dependencies: {
    npm_packages: ['@babel/parser@^7.23.0'],
    python_packages: [],
    system_tools: ['node'],
    other_skills: [],
  },

  permissions: {
    file_read: true,
    file_write: false,
    network: ['api.anthropic.com'],
    execution: ['node', 'bun'],
    environment_vars: ['ANTHROPIC_API_KEY'],
  },

  pricing: {
    type: 'freemium',
    credits_per_use: 10,
  },
};
