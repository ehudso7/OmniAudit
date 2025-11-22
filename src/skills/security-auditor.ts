import type { SkillDefinition } from '../types/index';

export const SecurityAuditorSkill: SkillDefinition = {
  skill_id: 'security-auditor-enterprise',
  version: '3.1.0',

  metadata: {
    name: 'Security Auditor Enterprise',
    description:
      'Military-grade security analysis using AI, OWASP Top 10, and zero-trust principles',
    author: 'OmniAudit Security Team',
    category: 'security',
    tags: ['security', 'owasp', 'vulnerability', 'xss', 'sql-injection', 'csrf'],
    language: ['typescript', 'javascript', 'python', 'rust', 'go'],
    framework: ['any'],
    created: '2025-01-10T00:00:00Z',
    updated: '2025-01-21T00:00:00Z',
    min_omniaudit_version: '1.0.0',
    license: 'Commercial',
  },

  instructions: {
    system_prompt: `You are a world-class security researcher and penetration tester with expertise in:
- OWASP Top 10 vulnerabilities (2023)
- Zero-trust security architecture
- Cryptography and secure key management
- Authentication/Authorization flaws (OAuth, JWT, session management)
- Injection attacks (SQL, NoSQL, Command, XSS, XXE)
- Sensitive data exposure and PII handling
- Secure coding practices per language/framework
- Supply chain security (dependency vulnerabilities)
- API security (rate limiting, input validation, CORS)
- Container and serverless security

Approach every line of code with attacker mindset. Ask:
1. What data flows through this code?
2. What trust assumptions are being made?
3. How could this be exploited?
4. What's the blast radius of a breach here?
5. Are security controls bypassed in edge cases?

Report vulnerabilities with CVE references when applicable.
Rate severity using CVSS 3.1 scoring.
Provide exploitability assessment (high/medium/low).`,

    analysis_strategy: 'comprehensive',

    behavior_rules: [
      'NEVER suggest rolling your own crypto',
      'Always recommend principle of least privilege',
      'Flag any hardcoded secrets, keys, or credentials',
      'Assume all user input is malicious',
      'Validate security at EVERY trust boundary',
      'Consider both authentication and authorization',
      'Check for timing attacks in comparison operations',
    ],

    optimization_priorities: ['security', 'maintainability', 'readability'],

    output_format: 'json',
  },

  capabilities: {
    analyzers: [
      {
        name: 'security-analyzer',
        type: 'semantic',
        config: {
          checkXSS: true,
          checkInjection: true,
          checkSecrets: true,
          checkCrypto: true,
          checkAuth: true,
        },
        enabled: true,
      },
      {
        name: 'ast-analyzer',
        type: 'ast',
        config: {
          checkComplexity: false,
          checkNesting: false,
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
      auto_fix: false, // Security fixes require human review
      learning: true,
    },
  },

  execution: {
    timeout_ms: 60000,
    max_file_size_mb: 20,
    max_files: 2000,
    parallel_analysis: true,
    cache_results: false, // Never cache security findings
    cache_ttl_seconds: 0,
  },

  dependencies: {
    npm_packages: [],
    python_packages: [],
    system_tools: [],
    other_skills: [],
    api_keys: [],
  },

  permissions: {
    file_read: true,
    file_write: false,
    network: ['api.anthropic.com'],
    execution: ['node'],
    environment_vars: ['ANTHROPIC_API_KEY'],
  },

  pricing: {
    type: 'enterprise',
    price_usd: 299,
  },
};
