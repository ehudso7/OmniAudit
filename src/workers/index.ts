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

  try {
    // Query analytics from database
    // This is a placeholder - implement full analytics query
    return c.json({
      skillId,
      executions: 0,
      success_rate: 0,
      avg_execution_time_ms: 0,
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

// ==================== QUEUE CONSUMER ====================

export default {
  fetch: app.fetch,

  // Queue consumer for async analysis
  async queue(batch: MessageBatch<any>, env: Bindings): Promise<void> {
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
          const result = await engine.executeSkill(
            skillId,
            { code, language },
            options || {},
          );
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
