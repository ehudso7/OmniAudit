import { createHash } from 'crypto';
import { Anthropic } from '@anthropic-ai/sdk';
import * as Sentry from '@sentry/bun';
import { Redis } from '@upstash/redis';
import { AnalyzerFactory } from '../analyzers/index';
import { db } from '../db/client';
import { TransformerFactory } from '../transformers/index';
import type {
  AIAnalysisResult,
  Analyzer,
  CodeInput,
  EngineConfig,
  ExecutionOptions,
  LoadedSkill,
  Optimization,
  SkillActivation,
  SkillContext,
  SkillDefinition,
  SkillExecutionResult,
  StaticAnalysisResult,
  ToolCall,
  Transformer,
} from '../types/index';
import { SkillDefinitionSchema } from '../types/index';

export class OmniAuditSkillsEngine {
  private anthropic: Anthropic;
  private cache: Redis;
  private config: EngineConfig;
  private skills: Map<string, LoadedSkill> = new Map();
  private activeSkills: Set<string> = new Set();

  constructor(config: EngineConfig) {
    this.config = config;
    this.anthropic = new Anthropic({
      apiKey: config.anthropicApiKey,
    });

    this.cache = new Redis({
      url: config.upstashUrl,
      token: config.upstashToken,
    });

    // Initialize Sentry if DSN provided
    if (config.sentryDsn) {
      Sentry.init({
        dsn: config.sentryDsn,
        tracesSampleRate: 1.0,
      });
    }
  }

  /**
   * Register and load a skill into memory
   */
  async registerSkill(definition: SkillDefinition): Promise<string> {
    const transaction = Sentry.startTransaction({
      name: 'registerSkill',
      op: 'skill.register',
    });

    try {
      // Validate schema
      const validated = SkillDefinitionSchema.parse(definition);

      // Check dependencies
      await this.validateDependencies(validated);

      // Initialize analyzers
      const analyzers = await this.initializeAnalyzers(validated.capabilities.analyzers);

      // Initialize transformers
      const transformers = await this.initializeTransformers(validated.capabilities.transformers);

      // Create loaded skill instance
      const loadedSkill: LoadedSkill = {
        definition: validated,
        analyzers,
        transformers,
        context: {},
        stats: {
          registered_at: new Date().toISOString(),
          executions: 0,
          success_rate: 1.0,
          avg_execution_time_ms: 0,
        },
      };

      // Store in memory
      this.skills.set(validated.skill_id, loadedSkill);

      // Persist to database
      await db.createSkill({
        skill_id: validated.skill_id,
        version: validated.version,
        user_id: 'system',
        definition: validated as unknown as Record<string, unknown>,
        is_public: true,
      });

      transaction.finish();

      return validated.skill_id;
    } catch (error) {
      transaction.setStatus('internal_error');
      Sentry.captureException(error);
      throw error;
    }
  }

  /**
   * Activate a skill for use in current session
   */
  async activateSkill(skillId: string, context?: SkillContext): Promise<SkillActivation> {
    let skill = this.skills.get(skillId);

    // If not in memory, load from database
    if (!skill) {
      const skillData = await db.getSkill(skillId);
      if (!skillData) {
        throw new Error(`Skill ${skillId} not found. Register it first.`);
      }

      const definition = JSON.parse(skillData.definition as string) as SkillDefinition;
      await this.registerSkill(definition);
      skill = this.skills.get(skillId)!;
    }

    this.activeSkills.add(skillId);

    // Merge context
    if (context) {
      skill.context = { ...skill.context, ...context };
    }

    return {
      skill_id: skillId,
      system_prompt: skill.definition.instructions.system_prompt,
      analyzers: skill.analyzers,
      transformers: skill.transformers,
      behavior_rules: skill.definition.instructions.behavior_rules,
      ai_features: skill.definition.capabilities.ai_features,
      context: skill.context,
    };
  }

  /**
   * Execute skill on code input with AI orchestration
   */
  async executeSkill(
    skillId: string,
    input: CodeInput,
    options: ExecutionOptions = {},
  ): Promise<SkillExecutionResult> {
    const skill = this.skills.get(skillId);
    if (!skill) {
      throw new Error(`Skill ${skillId} not found`);
    }

    const executionId = crypto.randomUUID();
    const startTime = Date.now();

    try {
      // Check cache if enabled
      if (skill.definition.execution.cache_results && !options.skipCache) {
        const cached = await this.getCachedResult(skillId, input);
        if (cached) {
          return cached;
        }
      }

      // Phase 1: Static Analysis
      console.log('Phase 1: Running static analyzers...');
      const analysisResults = await this.runAnalyzers(skill, input);

      // Phase 2: AI-Powered Deep Analysis
      console.log('Phase 2: Running AI analysis...');
      const aiAnalysis = await this.runAIAnalysis(skill, input, analysisResults);

      // Phase 3: Generate Optimizations
      console.log('Phase 3: Generating optimizations...');
      const optimizations = await this.generateOptimizations(
        skill,
        input,
        analysisResults,
        aiAnalysis,
      );

      // Apply severity filter if specified
      const filteredOptimizations = options.severityFilter
        ? optimizations.filter((opt) => options.severityFilter!.includes(opt.severity))
        : optimizations;

      // Apply max issues limit
      const limitedOptimizations = options.maxIssues
        ? filteredOptimizations.slice(0, options.maxIssues)
        : filteredOptimizations;

      // Phase 4: Apply Transformations (if auto_fix enabled)
      let transformedCode: string | null = null;
      if (skill.definition.capabilities.ai_features.auto_fix && options.autoFix) {
        console.log('Phase 4: Applying transformations...');
        transformedCode = await this.applyTransformations(skill, input, limitedOptimizations);
      }

      const executionTime = Date.now() - startTime;

      // Update stats
      skill.stats.executions++;
      skill.stats.avg_execution_time_ms =
        (skill.stats.avg_execution_time_ms * (skill.stats.executions - 1) + executionTime) /
        skill.stats.executions;

      const result: SkillExecutionResult = {
        execution_id: executionId,
        skill_id: skillId,
        success: true,
        timestamp: new Date().toISOString(),
        execution_time_ms: executionTime,

        analysis: {
          static_analysis: analysisResults,
          ai_analysis: aiAnalysis,
        },

        optimizations: limitedOptimizations,
        transformed_code: transformedCode,

        metrics: {
          files_analyzed: input.files?.length || 1,
          issues_found: limitedOptimizations.filter((o) => o.severity === 'error').length,
          warnings_found: limitedOptimizations.filter((o) => o.severity === 'warning').length,
          suggestions_found: limitedOptimizations.filter((o) => o.severity === 'info').length,
          lines_affected: this.countAffectedLines(limitedOptimizations),
        },

        metadata: {
          skill_version: skill.definition.version,
          language: input.language,
          framework: input.framework,
        },
      };

      // Cache result
      if (skill.definition.execution.cache_results) {
        await this.cacheResult(
          skillId,
          input,
          result,
          skill.definition.execution.cache_ttl_seconds,
        );
      }

      // Log execution to database
      await this.logExecution(result);

      // Update analytics
      await db.updateAnalytics(skillId, {
        executions_count: 1,
        success_count: 1,
        failure_count: 0,
        avg_execution_time_ms: executionTime,
        total_execution_time_ms: executionTime,
      });

      return result;
    } catch (error) {
      const executionTime = Date.now() - startTime;

      skill.stats.success_rate =
        (skill.stats.success_rate * skill.stats.executions) / (skill.stats.executions + 1);
      skill.stats.executions++;

      const errorResult: SkillExecutionResult = {
        execution_id: executionId,
        skill_id: skillId,
        success: false,
        timestamp: new Date().toISOString(),
        execution_time_ms: executionTime,
        error: {
          message: error instanceof Error ? error.message : String(error),
          stack: error instanceof Error ? error.stack : undefined,
        },
      };

      await this.logExecution(errorResult);
      await db.updateAnalytics(skillId, {
        executions_count: 1,
        failure_count: 1,
      });

      Sentry.captureException(error, {
        tags: { skill_id: skillId, execution_id: executionId },
      });

      throw error;
    }
  }

  /**
   * Run static analyzers on code
   */
  private async runAnalyzers(
    skill: LoadedSkill,
    input: CodeInput,
  ): Promise<StaticAnalysisResult[]> {
    const results: StaticAnalysisResult[] = [];

    const analyzerPromises = skill.analyzers
      .filter((analyzer) => analyzer.enabled && analyzer.canHandle(input.language))
      .map(async (analyzer) => {
        try {
          return await analyzer.analyze(input);
        } catch (error) {
          console.error(`Analyzer ${analyzer.name} failed:`, error);
          Sentry.captureException(error, {
            tags: { analyzer: analyzer.name, skill_id: skill.definition.skill_id },
          });
          return null;
        }
      });

    const analyzerResults = await Promise.all(analyzerPromises);
    results.push(...analyzerResults.filter((r) => r !== null));

    return results;
  }

  /**
   * AI-powered deep code analysis using Claude
   */
  private async runAIAnalysis(
    skill: LoadedSkill,
    input: CodeInput,
    staticResults: StaticAnalysisResult[],
  ): Promise<AIAnalysisResult> {
    const systemPrompt = this.buildSystemPrompt(skill, staticResults);
    const userPrompt = this.buildUserPrompt(input, staticResults);

    try {
      const response = await this.anthropic.messages.create({
        model: 'claude-sonnet-4-5-20250929',
        max_tokens: 8000,
        system: systemPrompt,
        messages: [
          {
            role: 'user',
            content: userPrompt,
          },
        ],
        tools: this.getAnalysisTools(),
      });

      let fullResponse = '';
      const toolCalls: ToolCall[] = [];

      for (const block of response.content) {
        if (block.type === 'text') {
          fullResponse += block.text;
        } else if (block.type === 'tool_use') {
          toolCalls.push({
            name: block.name,
            input: block.input as Record<string, unknown>,
          });
        }
      }

      return {
        analysis: fullResponse,
        tool_calls: toolCalls,
        confidence: this.calculateConfidence(fullResponse, staticResults),
      };
    } catch (error) {
      console.error('AI analysis failed:', error);
      return {
        analysis: 'AI analysis unavailable',
        tool_calls: [],
        confidence: 0,
      };
    }
  }

  /**
   * Generate optimization suggestions
   */
  private async generateOptimizations(
    skill: LoadedSkill,
    input: CodeInput,
    staticResults: StaticAnalysisResult[],
    aiAnalysis: AIAnalysisResult,
  ): Promise<Optimization[]> {
    const optimizations: Optimization[] = [];

    // Combine static and AI findings
    for (const result of staticResults) {
      for (const issue of result.issues) {
        optimizations.push({
          id: crypto.randomUUID(),
          type: this.mapIssueType(issue.type),
          severity: issue.severity,
          title: issue.message,
          description: issue.description || aiAnalysis.analysis,
          location: {
            file: input.file_path || 'unknown',
            line: issue.line,
            column: issue.column,
            length: issue.length,
          },
          original_code: this.extractCodeSnippet(input.code, issue.line, 3),
          suggested_fix: issue.fix || null,
          auto_fixable: issue.fix !== null,
          confidence: issue.confidence || 0.8,
          impact: this.estimateImpact(issue.type, issue.severity),
          category: skill.definition.metadata.category,
        });
      }
    }

    // Add AI-generated suggestions
    const aiSuggestions = this.parseAISuggestions(aiAnalysis.analysis, input);
    optimizations.push(...aiSuggestions);

    // Sort by priority
    return optimizations.sort((a, b) => {
      const severityOrder = { error: 3, warning: 2, info: 1 };
      return (
        severityOrder[b.severity] - severityOrder[a.severity] || b.impact.overall - a.impact.overall
      );
    });
  }

  /**
   * Apply code transformations
   */
  private async applyTransformations(
    skill: LoadedSkill,
    input: CodeInput,
    optimizations: Optimization[],
  ): Promise<string> {
    let transformedCode = input.code;

    const autoFixable = optimizations.filter((o) => o.auto_fixable);

    for (const optimization of autoFixable) {
      for (const transformer of skill.transformers) {
        if (transformer.canHandle(optimization)) {
          try {
            transformedCode = await transformer.apply(transformedCode, optimization);
          } catch (error) {
            console.error(`Transformer ${transformer.name} failed:`, error);
          }
        }
      }
    }

    return transformedCode;
  }

  /**
   * Build system prompt for Claude
   */
  private buildSystemPrompt(skill: LoadedSkill, staticResults: StaticAnalysisResult[]): string {
    const { instructions, metadata } = skill.definition;

    return `You are OmniAudit, an expert code optimization AI assistant.

${instructions.system_prompt}

**Current Skill**: ${metadata.name} v${skill.definition.version}
**Category**: ${metadata.category}
**Language**: ${metadata.language.join(', ')}
${metadata.framework ? `**Framework**: ${metadata.framework.join(', ')}` : ''}

**Optimization Priorities** (in order):
${instructions.optimization_priorities.map((p, i) => `${i + 1}. ${p}`).join('\n')}

**Behavior Rules**:
${instructions.behavior_rules.map((r, i) => `${i + 1}. ${r}`).join('\n')}

**Static Analysis Summary**:
${this.summarizeStaticResults(staticResults)}

Your task is to provide deep, actionable insights that go beyond static analysis.
Output your analysis in ${instructions.output_format} format.`;
  }

  /**
   * Build user prompt with code context
   */
  private buildUserPrompt(input: CodeInput, staticResults: StaticAnalysisResult[]): string {
    return `Please analyze the following code and provide optimization recommendations:

**File**: ${input.file_path || 'untitled'}
**Language**: ${input.language}
${input.framework ? `**Framework**: ${input.framework}` : ''}
${input.context ? `**Context**: ${input.context}` : ''}

\`\`\`${input.language}
${input.code}
\`\`\`

${
  staticResults.length > 0
    ? `**Static Analysis Found**:
${staticResults.map((r) => `- ${r.analyzer_name}: ${r.issues.length} issues`).join('\n')}`
    : ''
}

Provide a comprehensive analysis with specific, actionable recommendations.`;
  }

  /**
   * Get analysis tools for Claude
   */
  private getAnalysisTools() {
    return [
      {
        name: 'analyze_complexity',
        description: 'Calculate cyclomatic complexity of code segments',
        input_schema: {
          type: 'object' as const,
          properties: {
            function_name: { type: 'string', description: 'Name of the function to analyze' },
          },
          required: ['function_name'],
        },
      },
      {
        name: 'suggest_refactoring',
        description: 'Generate refactoring suggestions for code patterns',
        input_schema: {
          type: 'object' as const,
          properties: {
            pattern: { type: 'string', description: 'The code pattern to refactor' },
            reason: { type: 'string', description: 'Reason for refactoring' },
          },
          required: ['pattern', 'reason'],
        },
      },
      {
        name: 'estimate_performance_impact',
        description: 'Estimate the performance impact of a change',
        input_schema: {
          type: 'object' as const,
          properties: {
            change_description: { type: 'string' },
            metric: {
              type: 'string',
              enum: ['runtime', 'memory', 'bundle-size', 'network'],
            },
          },
          required: ['change_description', 'metric'],
        },
      },
    ];
  }

  // ==================== Helper Methods ====================

  private async validateDependencies(definition: SkillDefinition): Promise<void> {
    const errors: string[] = [];
    const warnings: string[] = [];

    // 1. Check if required packages are available
    if (definition.capabilities.analyzers) {
      for (const analyzer of definition.capabilities.analyzers) {
        if (analyzer.enabled) {
          const isAvailable = this.checkAnalyzerAvailability(analyzer.name);
          if (!isAvailable) {
            errors.push(`Required analyzer '${analyzer.name}' is not available`);
          }
        }
      }
    }

    // 2. Check if required transformers are available
    if (definition.capabilities.transformers) {
      for (const transformer of definition.capabilities.transformers) {
        const isAvailable = this.checkTransformerAvailability(transformer.name);
        if (!isAvailable) {
          errors.push(`Required transformer '${transformer.name}' is not available`);
        }
      }
    }

    // 3. Check if dependent skills are registered
    if (definition.dependencies?.other_skills) {
      for (const skillId of definition.dependencies.other_skills) {
        const skill = this.skills.get(skillId);
        if (!skill) {
          errors.push(`Required skill dependency '${skillId}' is not registered`);
        }
      }
    }

    // 4. Check API keys configuration
    if (definition.capabilities.ai_features) {
      const aiFeatures = definition.capabilities.ai_features;

      // Check if Claude API is configured when AI features are enabled
      if (aiFeatures.code_generation || aiFeatures.auto_fix || aiFeatures.explanation) {
        if (!this.config.anthropicApiKey) {
          errors.push('Anthropic API key is required for AI features but not configured');
        }
      }
    }

    // 5. Check cache configuration
    if (definition.execution.cache_results) {
      if (!this.config.upstashUrl || !this.config.upstashToken) {
        warnings.push('Caching is enabled but Redis URL/token is not configured');
      }
    }

    // 6. Validate language support
    const supportedLanguages = [
      'typescript',
      'javascript',
      'python',
      'go',
      'java',
      'rust',
      'ruby',
      'php',
      'c',
      'cpp',
      'csharp',
      'kotlin',
    ];

    for (const lang of definition.metadata.language) {
      if (!supportedLanguages.includes(lang.toLowerCase())) {
        warnings.push(`Language '${lang}' may have limited support`);
      }
    }

    // Log warnings
    for (const warning of warnings) {
      console.warn(`[Skill Validation Warning] ${warning}`);
    }

    // Throw if there are errors
    if (errors.length > 0) {
      throw new Error(`Skill validation failed:\n- ${errors.join('\n- ')}`);
    }
  }

  private checkAnalyzerAvailability(analyzerName: string): boolean {
    // Check if the analyzer can be created by the factory
    try {
      AnalyzerFactory.createAnalyzer(analyzerName, {});
      return true;
    } catch {
      return false;
    }
  }

  private checkTransformerAvailability(transformerName: string): boolean {
    // Check if the transformer can be created by the factory
    try {
      TransformerFactory.createTransformer(transformerName);
      return true;
    } catch {
      return false;
    }
  }

  private async initializeAnalyzers(
    analyzerConfigs: SkillDefinition['capabilities']['analyzers'],
  ): Promise<Analyzer[]> {
    const analyzers: Analyzer[] = [];

    for (const config of analyzerConfigs) {
      try {
        const analyzer = AnalyzerFactory.createAnalyzer(config.name, config.config);
        analyzer.enabled = config.enabled;
        analyzers.push(analyzer);
      } catch (error) {
        console.warn(`Failed to initialize analyzer ${config.name}:`, error);
      }
    }

    return analyzers;
  }

  private async initializeTransformers(
    transformerConfigs: SkillDefinition['capabilities']['transformers'],
  ): Promise<Transformer[]> {
    const transformers: Transformer[] = [];

    for (const config of transformerConfigs) {
      try {
        const transformer = TransformerFactory.createTransformer(config.name);
        transformers.push(transformer);
      } catch (error) {
        console.warn(`Failed to initialize transformer ${config.name}:`, error);
      }
    }

    return transformers;
  }

  private async getCachedResult(
    skillId: string,
    input: CodeInput,
  ): Promise<SkillExecutionResult | null> {
    const inputHash = this.hashInput(input);
    const cacheKey = `skill:${skillId}:${inputHash}`;

    try {
      const cached = await this.cache.get(cacheKey);
      if (cached) {
        return JSON.parse(cached as string) as SkillExecutionResult;
      }
    } catch (error) {
      console.warn('Cache retrieval failed:', error);
    }

    return null;
  }

  private async cacheResult(
    skillId: string,
    input: CodeInput,
    result: SkillExecutionResult,
    ttl: number,
  ): Promise<void> {
    const inputHash = this.hashInput(input);
    const cacheKey = `skill:${skillId}:${inputHash}`;

    try {
      await this.cache.set(cacheKey, JSON.stringify(result), { ex: ttl });
    } catch (error) {
      console.warn('Cache storage failed:', error);
    }
  }

  private hashInput(input: CodeInput): string {
    return createHash('sha256').update(JSON.stringify(input)).digest('hex').substring(0, 16);
  }

  private async logExecution(result: SkillExecutionResult): Promise<void> {
    try {
      await db.createExecution({
        execution_id: result.execution_id,
        skill_id: result.skill_id,
        success: result.success,
        execution_time_ms: result.execution_time_ms,
        result: result.success ? (result as unknown as Record<string, unknown>) : undefined,
        error_message: result.error?.message,
      });
    } catch (error) {
      console.error('Failed to log execution:', error);
    }
  }

  private summarizeStaticResults(results: StaticAnalysisResult[]): string {
    if (results.length === 0) return 'No static analysis results available.';

    return results
      .map(
        (r) =>
          `- ${r.analyzer_name} (${r.analyzer_type}): Found ${r.issues.length} issues in ${r.execution_time_ms}ms`,
      )
      .join('\n');
  }

  private mapIssueType(issueType: string): Optimization['type'] {
    if (issueType.includes('performance') || issueType.includes('slow')) return 'performance';
    if (issueType.includes('security') || issueType.includes('vulnerability')) return 'security';
    if (issueType.includes('architecture') || issueType.includes('design')) return 'architecture';
    if (issueType.includes('style') || issueType.includes('format')) return 'style';
    return 'quality';
  }

  private extractCodeSnippet(code: string, line: number, context: number): string {
    const lines = code.split('\n');
    const start = Math.max(0, line - context - 1);
    const end = Math.min(lines.length, line + context);
    return lines.slice(start, end).join('\n');
  }

  private estimateImpact(
    issueType: string,
    severity: 'error' | 'warning' | 'info',
  ): Optimization['impact'] {
    const severityMultiplier = severity === 'error' ? 1.0 : severity === 'warning' ? 0.7 : 0.4;

    let performance = 0;
    let security = 0;
    let maintainability = 0;

    if (issueType.includes('performance')) performance = 0.8;
    if (issueType.includes('security')) security = 1.0;
    if (issueType.includes('complexity') || issueType.includes('nesting')) maintainability = 0.7;

    const overall = Math.max(performance, security, maintainability) * severityMultiplier;

    return {
      performance: performance * severityMultiplier,
      security: security * severityMultiplier,
      maintainability: maintainability * severityMultiplier,
      overall,
    };
  }

  private countAffectedLines(optimizations: Optimization[]): number {
    return optimizations.reduce((count, opt) => count + (opt.location.length || 1), 0);
  }

  private calculateConfidence(analysis: string, staticResults: StaticAnalysisResult[]): number {
    // Simple heuristic: longer analysis with more detail = higher confidence
    const lengthFactor = Math.min(analysis.length / 1000, 1);
    const staticFactor = Math.min(staticResults.length / 3, 1);
    return (lengthFactor + staticFactor) / 2;
  }

  private parseAISuggestions(analysis: string, input: CodeInput): Optimization[] {
    const suggestions: Optimization[] = [];

    // Simple pattern matching for suggestions
    // In production, this would be more sophisticated
    const suggestionPatterns = [
      /consider\s+(.+)/gi,
      /recommend\s+(.+)/gi,
      /should\s+(.+)/gi,
      /suggest\s+(.+)/gi,
    ];

    for (const pattern of suggestionPatterns) {
      let match;
      while ((match = pattern.exec(analysis)) !== null) {
        suggestions.push({
          id: crypto.randomUUID(),
          type: 'quality',
          severity: 'info',
          title: 'AI Suggestion',
          description: match[1].trim(),
          location: {
            file: input.file_path || 'unknown',
            line: 0,
          },
          original_code: '',
          suggested_fix: null,
          auto_fixable: false,
          confidence: 0.6,
          impact: {
            overall: 0.5,
          },
          category: 'ai-optimization',
        });
      }
    }

    return suggestions;
  }
}
