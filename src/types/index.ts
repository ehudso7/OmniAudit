import { z } from 'zod';

// ==================== Skill Definition Schema ====================

export const SkillDefinitionSchema = z.object({
  // Core metadata
  skill_id: z.string().regex(/^[a-z0-9-]+$/),
  version: z.string().regex(/^\d+\.\d+\.\d+$/),

  metadata: z.object({
    name: z.string(),
    description: z.string(),
    author: z.string(),
    category: z.enum([
      'performance',
      'security',
      'quality',
      'refactoring',
      'architecture',
      'testing',
      'documentation',
      'ai-optimization',
      'custom',
    ]),
    tags: z.array(z.string()),
    language: z.array(z.string()),
    framework: z.array(z.string()).optional(),
    created: z.string().datetime(),
    updated: z.string().datetime(),
    min_omniaudit_version: z.string(),
    license: z.string().default('MIT'),
  }),

  // AI Instructions
  instructions: z.object({
    system_prompt: z.string(),
    analysis_strategy: z.enum(['comprehensive', 'targeted', 'incremental', 'critical-path']),

    behavior_rules: z.array(z.string()),

    optimization_priorities: z.array(
      z.enum([
        'performance',
        'readability',
        'maintainability',
        'security',
        'testability',
        'bundle-size',
        'runtime-speed',
        'memory-usage',
      ]),
    ),

    output_format: z.enum(['markdown', 'json', 'diff', 'ast', 'interactive']),

    code_style: z
      .object({
        indent: z.enum(['spaces', 'tabs']),
        indent_size: z.number(),
        quotes: z.enum(['single', 'double']),
        semi: z.boolean(),
        trailing_comma: z.enum(['none', 'es5', 'all']),
      })
      .optional(),
  }),

  // Analysis capabilities
  capabilities: z.object({
    analyzers: z.array(
      z.object({
        name: z.string(),
        type: z.enum(['ast', 'regex', 'semantic', 'dataflow', 'ai']),
        config: z.record(z.any()),
        enabled: z.boolean().default(true),
      }),
    ),

    transformers: z.array(
      z.object({
        name: z.string(),
        type: z.enum(['refactor', 'optimize', 'modernize', 'convert']),
        patterns: z.array(z.string()),
        replacement: z.string().optional(),
        ai_assisted: z.boolean().default(false),
      }),
    ),

    integrations: z.array(
      z.object({
        name: z.string(),
        type: z.enum(['linter', 'formatter', 'bundler', 'api', 'mcp']),
        endpoint: z.string().optional(),
        config: z.record(z.any()),
      }),
    ),

    ai_features: z.object({
      code_generation: z.boolean().default(false),
      explanation: z.boolean().default(true),
      suggestion: z.boolean().default(true),
      auto_fix: z.boolean().default(false),
      learning: z.boolean().default(false),
    }),
  }),

  // Performance & limits
  execution: z.object({
    timeout_ms: z.number().default(30000),
    max_file_size_mb: z.number().default(10),
    max_files: z.number().default(1000),
    parallel_analysis: z.boolean().default(true),
    cache_results: z.boolean().default(true),
    cache_ttl_seconds: z.number().default(3600),
  }),

  // Dependencies
  dependencies: z.object({
    npm_packages: z.array(z.string()),
    python_packages: z.array(z.string()),
    system_tools: z.array(z.string()),
    other_skills: z.array(z.string()),
    api_keys: z.array(z.string()).optional(),
  }),

  // Security permissions
  permissions: z.object({
    file_read: z.boolean().default(true),
    file_write: z.boolean().default(false),
    network: z.array(z.string()),
    execution: z.array(z.enum(['node', 'bun', 'python', 'rust'])),
    environment_vars: z.array(z.string()),
  }),

  // Testing & validation
  tests: z
    .object({
      test_cases: z.array(
        z.object({
          name: z.string(),
          input: z.string(),
          expected_output: z.any(),
          expected_issues: z.array(z.string()),
        }),
      ),
      benchmark: z
        .object({
          baseline_time_ms: z.number(),
          max_regression_percent: z.number().default(10),
        })
        .optional(),
    })
    .optional(),

  // Pricing (for marketplace)
  pricing: z
    .object({
      type: z.enum(['free', 'paid', 'freemium', 'enterprise']),
      price_usd: z.number().optional(),
      credits_per_use: z.number().optional(),
    })
    .optional(),
});

export type SkillDefinition = z.infer<typeof SkillDefinitionSchema>;

// ==================== Core Types ====================

export interface EngineConfig {
  anthropicApiKey: string;
  tursoUrl: string;
  tursoToken: string;
  upstashUrl: string;
  upstashToken: string;
  pineconeApiKey?: string;
  sentryDsn?: string;
}

export interface LoadedSkill {
  definition: SkillDefinition;
  analyzers: Analyzer[];
  transformers: Transformer[];
  context: Record<string, unknown>;
  stats: SkillStats;
}

export interface SkillStats {
  registered_at: string;
  executions: number;
  success_rate: number;
  avg_execution_time_ms: number;
}

export interface SkillContext {
  project_path?: string;
  file_patterns?: string[];
  exclude_patterns?: string[];
  user_preferences?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface SkillActivation {
  skill_id: string;
  system_prompt: string;
  analyzers: Analyzer[];
  transformers: Transformer[];
  behavior_rules: string[];
  ai_features: {
    code_generation: boolean;
    explanation: boolean;
    suggestion: boolean;
    auto_fix: boolean;
    learning: boolean;
  };
  context: Record<string, unknown>;
}

export interface CodeInput {
  code: string;
  language: string;
  file_path?: string;
  framework?: string;
  context?: string;
  files?: FileInput[];
}

export interface FileInput {
  path: string;
  content: string;
  language: string;
}

export interface ExecutionOptions {
  skipCache?: boolean;
  autoFix?: boolean;
  maxIssues?: number;
  severityFilter?: ('error' | 'warning' | 'info')[];
  stream?: boolean;
}

export interface SkillExecutionResult {
  execution_id: string;
  skill_id: string;
  success: boolean;
  timestamp: string;
  execution_time_ms: number;

  analysis?: {
    static_analysis: StaticAnalysisResult[];
    ai_analysis: AIAnalysisResult;
  };

  optimizations?: Optimization[];
  transformed_code?: string | null;

  metrics?: {
    files_analyzed: number;
    issues_found: number;
    warnings_found: number;
    suggestions_found: number;
    lines_affected: number;
  };

  metadata?: {
    skill_version: string;
    language: string;
    framework?: string;
  };

  error?: {
    message: string;
    stack?: string;
  };
}

export interface StaticAnalysisResult {
  analyzer_name: string;
  analyzer_type: 'ast' | 'regex' | 'semantic' | 'dataflow' | 'ai';
  execution_time_ms: number;
  issues: AnalysisIssue[];
  metadata?: Record<string, unknown>;
}

export interface AnalysisIssue {
  type: string;
  severity: 'error' | 'warning' | 'info';
  message: string;
  description?: string;
  line: number;
  column?: number;
  length?: number;
  fix?: string;
  confidence?: number;
}

export interface AIAnalysisResult {
  analysis: string;
  tool_calls: ToolCall[];
  confidence: number;
}

export interface ToolCall {
  name: string;
  input: Record<string, unknown>;
  output?: unknown;
}

export interface Optimization {
  id: string;
  type: 'performance' | 'security' | 'quality' | 'architecture' | 'style';
  severity: 'error' | 'warning' | 'info';
  title: string;
  description: string;
  location: {
    file: string;
    line: number;
    column?: number;
    length?: number;
  };
  original_code: string;
  suggested_fix: string | null;
  auto_fixable: boolean;
  confidence: number;
  impact: {
    performance?: number;
    security?: number;
    maintainability?: number;
    overall: number;
  };
  category: string;
  tags?: string[];
}

// ==================== Analyzer Interface ====================

export interface Analyzer {
  name: string;
  type: 'ast' | 'regex' | 'semantic' | 'dataflow' | 'ai';
  enabled: boolean;
  config: Record<string, unknown>;

  analyze(input: CodeInput): Promise<StaticAnalysisResult>;
  canHandle(language: string): boolean;
}

// ==================== Transformer Interface ====================

export interface Transformer {
  name: string;
  type: 'refactor' | 'optimize' | 'modernize' | 'convert';
  patterns: string[];
  ai_assisted: boolean;

  canHandle(optimization: Optimization): boolean;
  apply(code: string, optimization: Optimization): Promise<string>;
}

// ==================== Configuration ====================

export interface OmniAuditConfig {
  skills: string[];
  analysis: {
    strategy: 'comprehensive' | 'targeted' | 'incremental' | 'critical-path';
    parallel: boolean;
    cache: boolean;
  };
  autoFix: {
    enabled: boolean;
    on_save: boolean;
    require_confirmation: boolean;
  };
  integrations: {
    vscode: boolean;
    github: boolean;
    pre_commit_hook: boolean;
  };
  ai: {
    model: string;
    max_tokens: number;
    temperature: number;
  };
  exclude: string[];
  rules: Record<string, unknown>;
}

// ==================== API Types ====================

export interface MarketplaceSearchParams {
  query?: string;
  category?: string;
  language?: string;
  framework?: string;
  minRating?: number;
  sortBy?: 'downloads' | 'rating' | 'recent';
  limit?: number;
  offset?: number;
}

export interface MarketplaceSkill {
  id: string;
  skill_id: string;
  version: string;
  name: string;
  description: string;
  author: string;
  category: string;
  tags: string[];
  language: string[];
  framework?: string[];
  downloads_count: number;
  rating_avg: number;
  rating_count: number;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface SkillReview {
  id: string;
  skill_id: string;
  user_id: string;
  user_name: string;
  rating: number;
  review: string;
  helpful_count: number;
  created_at: string;
  updated_at: string;
}

export interface UserProfile {
  id: string;
  email: string;
  name?: string;
  avatar_url?: string;
  tier: 'free' | 'pro' | 'enterprise';
  credits: number;
  created_at: string;
}

export interface Project {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  repository_url?: string;
  language?: string;
  framework?: string;
  active_skills: string[];
  config: OmniAuditConfig;
  last_analyzed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface AnalysisResultRecord {
  id: string;
  project_id: string;
  execution_id: string;
  commit_sha?: string;
  branch?: string;
  files_analyzed: number;
  issues_found: number;
  warnings_found: number;
  suggestions_found: number;
  optimizations: Optimization[];
  metrics: Record<string, unknown>;
  created_at: string;
}

// ==================== Stream Types ====================

export interface StreamChunk {
  type: 'start' | 'progress' | 'result' | 'complete' | 'error';
  data?: unknown;
  message?: string;
  progress?: number;
}

// ==================== CLI Types ====================

export interface CLIOptions {
  config?: string;
  verbose?: boolean;
  silent?: boolean;
  noCache?: boolean;
  autoFix?: boolean;
  output?: string;
  format?: 'terminal' | 'json' | 'markdown';
}
