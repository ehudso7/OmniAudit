/**
 * OmniAudit Cloudflare Workers API
 * Edge-deployed analysis API with global low-latency
 */

import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { logger } from 'hono/logger';
import { OmniAuditSkillsEngine } from '../core/skills-engine';
import { getBuiltinSkill } from '../skills/index';
import type { CodeInput, SkillExecutionResult } from '../types/index';

type Bindings = {
  ANTHROPIC_API_KEY: string;
  TURSO_URL: string;
  TURSO_TOKEN: string;
  UPSTASH_URL: string;
  UPSTASH_TOKEN: string;
  PINECONE_API_KEY?: string;
  SENTRY_DSN?: string;
  JWT_SECRET: string;
  CACHE: KVNamespace;
  STORAGE: R2Bucket;
  ANALYSIS_QUEUE: Queue;
  ANALYTICS: AnalyticsEngineDataset;
  RATE_LIMITER: DurableObjectNamespace;
};

interface ExecutionHistoryEntry {
  success: boolean;
  execution_time_ms: number;
  error_type?: string;
  error_message?: string;
  language?: string;
  timestamp: string;
}

interface AnalyticsEngineResult {
  query_time_ms?: number;
  data_points?: number;
  message?: string;
  error?: string;
}

interface QueueMessageBody {
  jobId: string;
  code: string;
  language: string;
  skills: string[];
  options?: Record<string, unknown>;
  timestamp?: number;
}

const app = new Hono<{ Bindings: Bindings }>();

// Middleware
app.use('*', logger());
app.use(
  '*',
  cors({
    origin: ['https://omniaudit.dev', 'https://app.omniaudit.dev'],
    allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowHeaders: ['Content-Type', 'Authorization'],
    exposeHeaders: ['Content-Length', 'X-Request-Id'],
    maxAge: 86400,
    credentials: true,
  }),
);

// Add request ID
app.use('*', async (c, next) => {
  c.header('X-Request-Id', crypto.randomUUID());
  await next();
});

// Health check
app.get('/health', (c) => {
  return c.json({
    status: 'healthy',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
  });
});

// ==================== ANALYSIS API ====================

app.post('/api/v1/analyze', async (c) => {
  try {
    const body = await c.req.json();
    const { code, language, file_path, framework, skills, options } = body;

    if (!code || !language) {
      return c.json({ error: 'Missing required fields: code, language' }, 400);
    }

    // Initialize engine
    const engine = new OmniAuditSkillsEngine({
      anthropicApiKey: c.env.ANTHROPIC_API_KEY,
      tursoUrl: c.env.TURSO_URL,
      tursoToken: c.env.TURSO_TOKEN,
      upstashUrl: c.env.UPSTASH_URL,
      upstashToken: c.env.UPSTASH_TOKEN,
      pineconeApiKey: c.env.PINECONE_API_KEY,
      sentryDsn: c.env.SENTRY_DSN,
    });

    // Activate skills
    const skillIds = skills || ['performance-optimizer-pro'];
    for (const skillId of skillIds) {
      await engine.activateSkill(skillId);
    }

    // Execute analysis
    const input: CodeInput = {
      code,
      language,
      file_path,
      framework,
    };

    const results: SkillExecutionResult[] = [];
    for (const skillId of skillIds) {
      const result = await engine.executeSkill(skillId, input, options || {});
      results.push(result);
    }

    // Track analytics
    c.env.ANALYTICS.writeDataPoint({
      blobs: [skillIds.join(','), language],
      doubles: [results[0].execution_time_ms],
      indexes: [results[0].success ? '1' : '0'],
    });

    return c.json({
      success: true,
      results,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Analysis failed:', error);
    return c.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      500,
    );
  }
});

// Async analysis (queue-based)
app.post('/api/v1/analyze/async', async (c) => {
  try {
    const body = await c.req.json();
    const jobId = crypto.randomUUID();

    // Send to queue
    await c.env.ANALYSIS_QUEUE.send({
      jobId,
      ...body,
      timestamp: Date.now(),
    });

    return c.json({
      success: true,
      jobId,
      message: 'Analysis job queued',
      statusUrl: `/api/v1/jobs/${jobId}`,
    });
  } catch (error) {
    return c.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      500,
    );
  }
});

// Get analysis job status
app.get('/api/v1/jobs/:jobId', async (c) => {
  const jobId = c.req.param('jobId');

  try {
    // Check R2 storage for results
    const result = await c.env.STORAGE.get(`jobs/${jobId}/result.json`);

    if (!result) {
      return c.json({
        status: 'pending',
        jobId,
        message: 'Analysis in progress',
      });
    }

    const data = await result.json();
    return c.json({
      status: 'completed',
      jobId,
      result: data,
    });
  } catch (error) {
    return c.json(
      {
        status: 'error',
        jobId,
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      500,
    );
  }
});

// ==================== SKILLS API ====================

app.get('/api/v1/skills', async (c) => {
  try {
    const category = c.req.query('category');
    const language = c.req.query('language');

    // For now, return built-in skills
    // In production, query from database
    const skills = [
      'performance-optimizer-pro',
      'security-auditor-enterprise',
      'react-best-practices',
      'typescript-expert',
      'architecture-advisor',
    ]
      .map((id) => getBuiltinSkill(id))
      .filter((skill) => {
        if (!skill) return false;
        if (category && skill.metadata.category !== category) return false;
        if (language && !skill.metadata.language.includes(language)) return false;
        return true;
      });

    return c.json({
      skills,
      count: skills.length,
    });
  } catch (error) {
    return c.json(
      {
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      500,
    );
  }
});

app.get('/api/v1/skills/:skillId', async (c) => {
  const skillId = c.req.param('skillId');

  try {
    const skill = getBuiltinSkill(skillId);

    if (!skill) {
      return c.json({ error: 'Skill not found' }, 404);
    }

    return c.json({ skill });
  } catch (error) {
    return c.json(
      {
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      500,
    );
  }
});

// ==================== ANALYTICS API ====================

app.get('/api/v1/analytics/skills/:skillId', async (c) => {
  const skillId = c.req.param('skillId');
  const timeRange = c.req.query('range') || '7d'; // Default to 7 days

  try {
    // Parse time range
    const now = Date.now();
    const rangeMs = parseTimeRange(timeRange);
    const startTime = now - rangeMs;

    // Query analytics from Cloudflare Analytics Engine
    const analyticsData = await queryAnalyticsEngine(c.env.ANALYTICS, skillId, startTime, now);

    // Query execution history from KV cache or R2 storage
    const executionHistory = await getExecutionHistory(c.env.CACHE, c.env.STORAGE, skillId, 100);

    // Calculate statistics
    const totalExecutions = executionHistory.length;
    const successfulExecutions = executionHistory.filter(
      (e: ExecutionHistoryEntry) => e.success,
    ).length;
    const successRate = totalExecutions > 0 ? (successfulExecutions / totalExecutions) * 100 : 0;

    const executionTimes = executionHistory.map(
      (e: ExecutionHistoryEntry) => e.execution_time_ms || 0,
    );
    const avgExecutionTime =
      executionTimes.length > 0
        ? executionTimes.reduce((a: number, b: number) => a + b, 0) / executionTimes.length
        : 0;

    const minExecutionTime = executionTimes.length > 0 ? Math.min(...executionTimes) : 0;
    const maxExecutionTime = executionTimes.length > 0 ? Math.max(...executionTimes) : 0;

    // Calculate p50, p90, p99 percentiles
    const sortedTimes = [...executionTimes].sort((a, b) => a - b);
    const p50 = getPercentile(sortedTimes, 50);
    const p90 = getPercentile(sortedTimes, 90);
    const p99 = getPercentile(sortedTimes, 99);

    // Calculate error rate and error breakdown
    const errors = executionHistory.filter((e: ExecutionHistoryEntry) => !e.success);
    const errorRate = totalExecutions > 0 ? (errors.length / totalExecutions) * 100 : 0;
    const errorBreakdown = errors.reduce(
      (acc: Record<string, number>, e: ExecutionHistoryEntry) => {
        const errorType = e.error_type || 'unknown';
        acc[errorType] = (acc[errorType] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>,
    );

    // Calculate usage by language
    const languageBreakdown = executionHistory.reduce(
      (acc: Record<string, number>, e: ExecutionHistoryEntry) => {
        const lang = e.language || 'unknown';
        acc[lang] = (acc[lang] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>,
    );

    // Build daily/hourly breakdown
    const dailyStats = buildTimeSeriesStats(executionHistory, 'day', 7);
    const hourlyStats = buildTimeSeriesStats(executionHistory, 'hour', 24);

    return c.json({
      skillId,
      timeRange,
      timestamp: new Date().toISOString(),

      // Core metrics
      summary: {
        total_executions: totalExecutions,
        successful_executions: successfulExecutions,
        failed_executions: errors.length,
        success_rate: Math.round(successRate * 100) / 100,
        error_rate: Math.round(errorRate * 100) / 100,
      },

      // Performance metrics
      performance: {
        avg_execution_time_ms: Math.round(avgExecutionTime * 100) / 100,
        min_execution_time_ms: minExecutionTime,
        max_execution_time_ms: maxExecutionTime,
        p50_execution_time_ms: p50,
        p90_execution_time_ms: p90,
        p99_execution_time_ms: p99,
      },

      // Usage breakdown
      usage: {
        by_language: languageBreakdown,
        daily_stats: dailyStats,
        hourly_stats: hourlyStats,
      },

      // Error analysis
      errors: {
        total: errors.length,
        breakdown: errorBreakdown,
        recent: errors.slice(0, 5).map((e: ExecutionHistoryEntry) => ({
          timestamp: e.timestamp,
          error_type: e.error_type,
          error_message: e.error_message?.substring(0, 100),
        })),
      },

      // Raw analytics data from Analytics Engine
      analytics_engine: analyticsData,
    });
  } catch (error) {
    console.error('Analytics query failed:', error);
    return c.json(
      {
        error: error instanceof Error ? error.message : 'Unknown error',
        skillId,
      },
      500,
    );
  }
});

// Analytics summary endpoint
app.get('/api/v1/analytics/summary', async (c) => {
  try {
    // Get overall platform analytics
    const skills = [
      'performance-optimizer-pro',
      'security-auditor-enterprise',
      'react-best-practices',
    ];
    const summaryPromises = skills.map(async (skillId) => {
      const history = await getExecutionHistory(c.env.CACHE, c.env.STORAGE, skillId, 100);
      return {
        skillId,
        executions: history.length,
        success_rate:
          history.length > 0
            ? (history.filter((e: ExecutionHistoryEntry) => e.success).length / history.length) *
              100
            : 0,
      };
    });

    const skillStats = await Promise.all(summaryPromises);
    const totalExecutions = skillStats.reduce((sum, s) => sum + s.executions, 0);
    const avgSuccessRate =
      skillStats.length > 0
        ? skillStats.reduce((sum, s) => sum + s.success_rate, 0) / skillStats.length
        : 0;

    return c.json({
      timestamp: new Date().toISOString(),
      total_executions: totalExecutions,
      avg_success_rate: Math.round(avgSuccessRate * 100) / 100,
      skills: skillStats,
      top_skill: skillStats.sort((a, b) => b.executions - a.executions)[0]?.skillId || 'none',
    });
  } catch (error) {
    return c.json(
      {
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      500,
    );
  }
});

// Helper functions for analytics
function parseTimeRange(range: string): number {
  const match = range.match(/^(\d+)([hdwm])$/);
  if (!match) return 7 * 24 * 60 * 60 * 1000; // Default 7 days

  const value = Number.parseInt(match[1], 10);
  const unit = match[2];

  switch (unit) {
    case 'h':
      return value * 60 * 60 * 1000;
    case 'd':
      return value * 24 * 60 * 60 * 1000;
    case 'w':
      return value * 7 * 24 * 60 * 60 * 1000;
    case 'm':
      return value * 30 * 24 * 60 * 60 * 1000;
    default:
      return 7 * 24 * 60 * 60 * 1000;
  }
}

async function queryAnalyticsEngine(
  _analytics: AnalyticsEngineDataset,
  _skillId: string,
  _startTime: number,
  _endTime: number,
): Promise<AnalyticsEngineResult> {
  // Note: Analytics Engine queries are typically done via SQL API
  // This is a simplified version that returns cached aggregates

  try {
    // In production, you would query the Analytics Engine SQL API
    // For now, return a structured placeholder that matches real data format
    return {
      query_time_ms: 0,
      data_points: 0,
      message: 'Analytics Engine data available via SQL API',
    };
  } catch {
    return { error: 'Analytics Engine query failed' };
  }
}

async function getExecutionHistory(
  cache: KVNamespace,
  storage: R2Bucket,
  skillId: string,
  limit: number,
): Promise<ExecutionHistoryEntry[]> {
  try {
    // Try to get from KV cache first
    const cacheKey = `executions:${skillId}:recent`;
    const cached = await cache.get(cacheKey, { type: 'json' });
    if (cached && Array.isArray(cached)) {
      return cached.slice(0, limit);
    }

    // Fall back to R2 storage
    const storageKey = `analytics/${skillId}/history.json`;
    const object = await storage.get(storageKey);
    if (object) {
      const data = (await object.json()) as ExecutionHistoryEntry[];
      // Cache for 5 minutes
      await cache.put(cacheKey, JSON.stringify(data.slice(0, 1000)), { expirationTtl: 300 });
      return data.slice(0, limit);
    }

    return [];
  } catch {
    return [];
  }
}

function getPercentile(sortedArray: number[], percentile: number): number {
  if (sortedArray.length === 0) return 0;
  const index = Math.ceil((percentile / 100) * sortedArray.length) - 1;
  return sortedArray[Math.max(0, Math.min(index, sortedArray.length - 1))];
}

function buildTimeSeriesStats(
  executions: ExecutionHistoryEntry[],
  granularity: 'hour' | 'day',
  periods: number,
): Array<{ period: string; count: number; success_rate: number }> {
  const stats: Array<{ period: string; count: number; success_rate: number }> = [];
  const now = new Date();

  for (let i = periods - 1; i >= 0; i--) {
    const periodStart = new Date(now);
    const periodEnd = new Date(now);

    if (granularity === 'hour') {
      periodStart.setHours(now.getHours() - i, 0, 0, 0);
      periodEnd.setHours(now.getHours() - i + 1, 0, 0, 0);
    } else {
      periodStart.setDate(now.getDate() - i);
      periodStart.setHours(0, 0, 0, 0);
      periodEnd.setDate(now.getDate() - i + 1);
      periodEnd.setHours(0, 0, 0, 0);
    }

    const periodExecutions = executions.filter((e: ExecutionHistoryEntry) => {
      const execTime = new Date(e.timestamp).getTime();
      return execTime >= periodStart.getTime() && execTime < periodEnd.getTime();
    });

    const successCount = periodExecutions.filter((e: ExecutionHistoryEntry) => e.success).length;
    const successRate =
      periodExecutions.length > 0 ? (successCount / periodExecutions.length) * 100 : 0;

    stats.push({
      period: periodStart.toISOString(),
      count: periodExecutions.length,
      success_rate: Math.round(successRate * 100) / 100,
    });
  }

  return stats;
}

// ==================== QUEUE CONSUMER ====================

export default {
  fetch: app.fetch,

  // Queue consumer for async analysis
  async queue(batch: MessageBatch<QueueMessageBody>, env: Bindings): Promise<void> {
    for (const message of batch.messages) {
      try {
        const { jobId, code, language, skills, options } = message.body;

        // Initialize engine
        const engine = new OmniAuditSkillsEngine({
          anthropicApiKey: env.ANTHROPIC_API_KEY,
          tursoUrl: env.TURSO_URL,
          tursoToken: env.TURSO_TOKEN,
          upstashUrl: env.UPSTASH_URL,
          upstashToken: env.UPSTASH_TOKEN,
          pineconeApiKey: env.PINECONE_API_KEY,
          sentryDsn: env.SENTRY_DSN,
        });

        // Execute analysis
        const results: SkillExecutionResult[] = [];
        for (const skillId of skills || ['performance-optimizer-pro']) {
          await engine.activateSkill(skillId);
          const result = await engine.executeSkill(skillId, { code, language }, options || {});
          results.push(result);
        }

        // Store results in R2
        await env.STORAGE.put(
          `jobs/${jobId}/result.json`,
          JSON.stringify({ results, timestamp: new Date().toISOString() }),
        );

        message.ack();
      } catch (error) {
        console.error('Queue processing failed:', error);
        message.retry();
      }
    }
  },

  // Scheduled cleanup of cache
  async scheduled(_event: ScheduledEvent, _env: Bindings, _ctx: ExecutionContext): Promise<void> {
    console.log('Running scheduled cache cleanup...');
    // Implement cache cleanup logic
  },
};

// ==================== RATE LIMITER DURABLE OBJECT ====================

export class RateLimiter {
  private requests: Map<string, number[]>;

  constructor(_state: DurableObjectState) {
    this.requests = new Map();
  }

  async fetch(request: Request): Promise<Response> {
    const clientId = new URL(request.url).searchParams.get('clientId') || 'anonymous';
    const limit = 100; // requests per hour
    const windowMs = 60 * 60 * 1000; // 1 hour

    const now = Date.now();
    const requests = this.requests.get(clientId) || [];

    // Remove old requests outside the window
    const recentRequests = requests.filter((timestamp) => now - timestamp < windowMs);

    if (recentRequests.length >= limit) {
      return new Response('Rate limit exceeded', { status: 429 });
    }

    // Add current request
    recentRequests.push(now);
    this.requests.set(clientId, recentRequests);

    return new Response('OK', { status: 200 });
  }
}
