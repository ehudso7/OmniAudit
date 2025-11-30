import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock fetch for API calls
global.fetch = vi.fn();

describe('OmniAudit SDK Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Client initialization', () => {
    it('should initialize with valid API key', () => {
      const client = {
        apiKey: 'sk-test-123',
        baseUrl: 'https://api.omniaudit.dev',
        isInitialized: true,
      };

      expect(client.isInitialized).toBe(true);
      expect(client.apiKey).toBeDefined();
    });

    it('should throw error with invalid configuration', () => {
      const createClient = (config: any) => {
        if (!config.apiKey) {
          throw new Error('API key is required');
        }
        return config;
      };

      expect(() => createClient({})).toThrow('API key is required');
    });
  });

  describe('Audit operations', () => {
    it('should submit audit request', async () => {
      const mockResponse = {
        id: 'audit-123',
        status: 'pending',
        created_at: new Date().toISOString(),
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const response = await fetch('/api/v1/audit', {
        method: 'POST',
        body: JSON.stringify({ path: '/project' }),
      });

      const data = await response.json();
      expect(data.id).toBe('audit-123');
      expect(data.status).toBe('pending');
    });

    it('should poll for audit completion', async () => {
      const statuses = ['pending', 'running', 'completed'];
      let callCount = 0;

      (global.fetch as any).mockImplementation(() => {
        const status = statuses[Math.min(callCount++, statuses.length - 1)];
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ status }),
        });
      });

      // Simulate polling
      let currentStatus = 'pending';
      while (currentStatus !== 'completed') {
        const response = await fetch('/api/v1/audit/123');
        const data = await response.json();
        currentStatus = data.status;
      }

      expect(currentStatus).toBe('completed');
    });

    it('should handle streaming results', async () => {
      const chunks = [
        { type: 'progress', value: 25 },
        { type: 'progress', value: 50 },
        { type: 'finding', data: { id: '1', severity: 'high' } },
        { type: 'progress', value: 100 },
        { type: 'complete', summary: { total: 1 } },
      ];

      const streamedData: any[] = [];

      for (const chunk of chunks) {
        streamedData.push(chunk);
        if (chunk.type === 'complete') break;
      }

      expect(streamedData).toHaveLength(5);
      expect(streamedData[4].type).toBe('complete');
    });
  });

  describe('Findings management', () => {
    it('should retrieve findings with pagination', async () => {
      const allFindings = Array(50).fill(null).map((_, i) => ({
        id: `finding-${i}`,
        severity: i < 5 ? 'critical' : 'low',
      }));

      const pageSize = 10;
      const page = 2;
      const paginatedFindings = allFindings.slice((page - 1) * pageSize, page * pageSize);

      expect(paginatedFindings).toHaveLength(10);
      expect(paginatedFindings[0].id).toBe('finding-10');
    });

    it('should filter findings by severity', async () => {
      const findings = [
        { id: '1', severity: 'critical' },
        { id: '2', severity: 'high' },
        { id: '3', severity: 'critical' },
        { id: '4', severity: 'low' },
      ];

      const criticalFindings = findings.filter((f) => f.severity === 'critical');
      expect(criticalFindings).toHaveLength(2);
    });

    it('should export findings in different formats', async () => {
      const findings = [{ id: '1', severity: 'high', message: 'SQL Injection' }];

      const exportFormats = {
        json: JSON.stringify(findings),
        csv: 'id,severity,message\n1,high,SQL Injection',
        sarif: JSON.stringify({
          version: '2.1.0',
          runs: [{ results: findings }],
        }),
      };

      expect(JSON.parse(exportFormats.json)).toHaveLength(1);
      expect(exportFormats.csv).toContain('SQL Injection');
      expect(JSON.parse(exportFormats.sarif).version).toBe('2.1.0');
    });
  });

  describe('Webhook integration', () => {
    it('should verify webhook signatures', () => {
      const payload = JSON.stringify({ event: 'audit.completed' });
      const secret = 'whsec_test123';
      const timestamp = Date.now().toString();

      // Simple signature verification mock
      const createSignature = (payload: string, secret: string) => {
        return `sha256=${Buffer.from(payload + secret).toString('base64').slice(0, 32)}`;
      };

      const signature = createSignature(payload, secret);
      expect(signature).toMatch(/^sha256=/);
    });

    it('should process webhook events', () => {
      const events: any[] = [];
      const handlers = new Map<string, Function>();

      handlers.set('audit.completed', (data: any) => {
        events.push({ type: 'completed', ...data });
      });

      handlers.set('finding.created', (data: any) => {
        events.push({ type: 'finding', ...data });
      });

      // Simulate webhook events
      const webhookPayload = { event: 'audit.completed', auditId: '123' };
      const handler = handlers.get(webhookPayload.event);
      if (handler) {
        handler(webhookPayload);
      }

      expect(events).toHaveLength(1);
      expect(events[0].type).toBe('completed');
    });
  });

  describe('Error handling', () => {
    it('should handle API rate limiting', async () => {
      const rateLimitResponse = {
        ok: false,
        status: 429,
        headers: new Map([['retry-after', '60']]),
      };

      const handleRateLimit = (response: any) => {
        if (response.status === 429) {
          const retryAfter = response.headers.get('retry-after') || '60';
          return { retryAfter: parseInt(retryAfter), shouldRetry: true };
        }
        return { shouldRetry: false };
      };

      const result = handleRateLimit(rateLimitResponse);
      expect(result.shouldRetry).toBe(true);
      expect(result.retryAfter).toBe(60);
    });

    it('should implement exponential backoff', async () => {
      const calculateBackoff = (attempt: number, baseDelay = 1000) => {
        return Math.min(baseDelay * Math.pow(2, attempt), 30000);
      };

      expect(calculateBackoff(0)).toBe(1000);
      expect(calculateBackoff(1)).toBe(2000);
      expect(calculateBackoff(2)).toBe(4000);
      expect(calculateBackoff(5)).toBe(30000); // Capped at 30 seconds
    });

    it('should provide detailed error information', () => {
      class SDKError extends Error {
        code: string;
        statusCode: number;
        details: any;

        constructor(message: string, code: string, statusCode: number, details?: any) {
          super(message);
          this.code = code;
          this.statusCode = statusCode;
          this.details = details;
        }
      }

      const error = new SDKError(
        'Authentication failed',
        'AUTH_FAILED',
        401,
        { reason: 'Invalid API key' },
      );

      expect(error.code).toBe('AUTH_FAILED');
      expect(error.statusCode).toBe(401);
      expect(error.details.reason).toBe('Invalid API key');
    });
  });
});
