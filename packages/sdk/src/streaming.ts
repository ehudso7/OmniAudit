import EventEmitter from 'eventemitter3';
import type { AuditRequest, AuditResult, AuditProgress, Finding, EventMap } from './types.js';

/**
 * Streaming audit client with event-based API
 */
export class StreamingAuditClient extends EventEmitter<EventMap> {
  private _apiUrl: string;
  private _apiKey?: string;

  constructor(apiUrl: string, apiKey?: string) {
    super();
    this._apiUrl = apiUrl;
    this._apiKey = apiKey;
  }

  get apiUrl(): string {
    return this._apiUrl;
  }

  get apiKey(): string | undefined {
    return this._apiKey;
  }

  /**
   * Start a streaming audit
   */
  async start(request: AuditRequest): Promise<void> {
    try {
      // Emit progress events
      this.emit('progress', {
        stage: 'initializing',
        progress: 0,
        message: 'Initializing audit...',
      });

      // Simulate scanning
      await this.simulateScanning();

      // Simulate analysis
      await this.simulateAnalysis();

      // Emit findings as they're discovered
      const findings: Finding[] = [
        {
          id: '1',
          rule_id: 'security/no-eval',
          title: 'Dangerous use of eval()',
          description: 'Using eval() can lead to code injection vulnerabilities',
          severity: 'critical',
          category: 'security',
          file: 'src/utils.ts',
          line: 42,
          column: 10,
          message: 'Avoid using eval() as it poses security risks',
          recommendation: 'Use safer alternatives',
        },
      ];

      for (const finding of findings) {
        this.emit('finding', finding);
      }

      this.emit('progress', {
        stage: 'reporting',
        progress: 95,
        message: 'Generating report...',
      });

      // Emit final result
      const result: AuditResult = {
        id: `audit-${Date.now()}`,
        project: request.path,
        timestamp: new Date().toISOString(),
        duration_ms: 5432,
        total_files: 127,
        total_findings: findings.length,
        findings_by_severity: {
          critical: 1,
          high: 0,
          medium: 0,
          low: 0,
          info: 0,
        },
        findings,
        metadata: {
          version: '2.0.0',
          rules_count: 150,
          analyzers: ['eslint', 'typescript', 'security'],
        },
      };

      this.emit('complete', result);

      this.emit('progress', {
        stage: 'complete',
        progress: 100,
        message: 'Audit complete',
      });
    } catch (error) {
      this.emit('error', error instanceof Error ? error : new Error('Unknown error'));
      throw error;
    }
  }

  private async simulateScanning(): Promise<void> {
    const steps = 10;
    for (let i = 0; i < steps; i++) {
      await new Promise(resolve => setTimeout(resolve, 100));
      this.emit('progress', {
        stage: 'scanning',
        progress: 10 + (i / steps) * 30,
        message: 'Scanning files...',
        filesScanned: Math.floor((i / steps) * 127),
        totalFiles: 127,
      });
    }
  }

  private async simulateAnalysis(): Promise<void> {
    const steps = 10;
    for (let i = 0; i < steps; i++) {
      await new Promise(resolve => setTimeout(resolve, 100));
      this.emit('progress', {
        stage: 'analyzing',
        progress: 40 + (i / steps) * 50,
        message: 'Analyzing code...',
        filesScanned: 127,
        totalFiles: 127,
        findingsCount: Math.floor((i / steps) * 23),
      });
    }
  }

  /**
   * Cancel the current audit
   */
  cancel(): void {
    this.removeAllListeners();
  }
}

/**
 * Create a streaming audit with convenience hooks
 */
export function createStreamingAudit(
  _request: AuditRequest,
  apiUrl: string,
  apiKey?: string
): StreamingAuditClient {
  return new StreamingAuditClient(apiUrl, apiKey);
}

/**
 * Hook-based API for React-like usage
 */
export interface AuditHooks {
  onProgress?: (progress: AuditProgress) => void;
  onFinding?: (finding: Finding) => void;
  onComplete?: (result: AuditResult) => void;
  onError?: (error: Error) => void;
}

/**
 * Run audit with hooks
 */
export async function runAuditWithHooks(
  request: AuditRequest,
  hooks: AuditHooks,
  apiUrl: string,
  apiKey?: string
): Promise<AuditResult> {
  return new Promise((resolve, reject) => {
    const client = new StreamingAuditClient(apiUrl, apiKey);

    if (hooks.onProgress) {
      client.on('progress', hooks.onProgress);
    }

    if (hooks.onFinding) {
      client.on('finding', hooks.onFinding);
    }

    if (hooks.onComplete) {
      client.on('complete', (result) => {
        hooks.onComplete?.(result);
        resolve(result);
      });
    } else {
      client.on('complete', resolve);
    }

    if (hooks.onError) {
      client.on('error', (error) => {
        hooks.onError?.(error);
        reject(error);
      });
    } else {
      client.on('error', reject);
    }

    client.start(request).catch(reject);
  });
}
