import EventEmitter from 'eventemitter3';
import { z } from 'zod';
import type { SDKConfig, AuditRequest, AuditResult, Finding, Rule, EventMap, AuditProgress } from './types.js';

export class OmniAuditClient extends EventEmitter<EventMap> {
  private config: SDKConfig;
  private baseUrl: string;

  constructor(config: Partial<SDKConfig>) {
    super();

    this.config = {
      apiUrl: config.apiUrl || 'http://localhost:8000',
      apiKey: config.apiKey,
      timeout: config.timeout || 30000,
      retries: config.retries || 3,
      retryDelay: config.retryDelay || 1000,
    };

    this.baseUrl = this.config.apiUrl;
  }

  /**
   * Run an audit (Promise-based API)
   */
  async audit(request: AuditRequest): Promise<AuditResult> {
    try {
      // Mock implementation - would make actual API call
      const result: AuditResult = {
        id: `audit-${Date.now()}`,
        project: request.path,
        timestamp: new Date().toISOString(),
        duration_ms: 5432,
        total_files: 127,
        total_findings: 23,
        findings_by_severity: {
          critical: 2,
          high: 5,
          medium: 10,
          low: 4,
          info: 2,
        },
        findings: [],
        metadata: {
          version: '2.0.0',
          rules_count: 150,
          analyzers: ['eslint', 'typescript', 'security'],
        },
      };

      return result;
    } catch (error) {
      throw new Error(`Audit failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Run an audit with streaming progress (Streaming API)
   */
  async *auditStream(request: AuditRequest): AsyncGenerator<AuditProgress, AuditResult, undefined> {
    try {
      // Emit progress events
      yield {
        stage: 'initializing',
        progress: 0,
        message: 'Initializing audit...',
      };

      yield {
        stage: 'scanning',
        progress: 20,
        message: 'Scanning files...',
        filesScanned: 25,
        totalFiles: 127,
      };

      yield {
        stage: 'analyzing',
        progress: 50,
        message: 'Analyzing code...',
        filesScanned: 64,
        totalFiles: 127,
        findingsCount: 12,
      };

      yield {
        stage: 'analyzing',
        progress: 80,
        message: 'Analyzing code...',
        filesScanned: 102,
        totalFiles: 127,
        findingsCount: 20,
      };

      yield {
        stage: 'reporting',
        progress: 95,
        message: 'Generating report...',
        filesScanned: 127,
        totalFiles: 127,
        findingsCount: 23,
      };

      yield {
        stage: 'complete',
        progress: 100,
        message: 'Audit complete',
        filesScanned: 127,
        totalFiles: 127,
        findingsCount: 23,
      };

      // Return final result
      const result: AuditResult = {
        id: `audit-${Date.now()}`,
        project: request.path,
        timestamp: new Date().toISOString(),
        duration_ms: 5432,
        total_files: 127,
        total_findings: 23,
        findings_by_severity: {
          critical: 2,
          high: 5,
          medium: 10,
          low: 4,
          info: 2,
        },
        findings: [],
        metadata: {
          version: '2.0.0',
          rules_count: 150,
          analyzers: ['eslint', 'typescript', 'security'],
        },
      };

      return result;
    } catch (error) {
      yield {
        stage: 'error',
        progress: 0,
        message: error instanceof Error ? error.message : 'Unknown error',
      };
      throw error;
    }
  }

  /**
   * Get findings with filtering
   */
  async getFindings(filters?: {
    severity?: string[];
    category?: string[];
    file?: string;
    limit?: number;
  }): Promise<Finding[]> {
    // Mock implementation
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

    return findings;
  }

  /**
   * Get a specific finding by ID
   */
  async getFinding(id: string): Promise<Finding | null> {
    // Mock implementation
    const finding: Finding = {
      id,
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
    };

    return finding;
  }

  /**
   * Get all available rules
   */
  async getRules(filters?: { category?: string; enabled?: boolean }): Promise<Rule[]> {
    // Mock implementation
    const rules: Rule[] = [
      {
        id: 'security/no-eval',
        name: 'No eval()',
        description: 'Disallows the use of eval() function',
        category: 'security',
        severity: 'critical',
        enabled: true,
        autoFixable: false,
      },
    ];

    return rules;
  }

  /**
   * Get a specific rule by ID
   */
  async getRule(id: string): Promise<Rule | null> {
    // Mock implementation
    const rule: Rule = {
      id,
      name: 'No eval()',
      description: 'Disallows the use of eval() function',
      category: 'security',
      severity: 'critical',
      enabled: true,
      autoFixable: false,
    };

    return rule;
  }

  /**
   * Auto-fix findings
   */
  async fix(findingIds: string[]): Promise<{ fixed: number; failed: number }> {
    // Mock implementation
    return {
      fixed: findingIds.length,
      failed: 0,
    };
  }

  /**
   * Export audit results in a specific format
   */
  async export(auditId: string, format: string): Promise<string> {
    // Mock implementation
    return JSON.stringify({ auditId, format });
  }

  /**
   * Get audit history
   */
  async getAuditHistory(limit = 10): Promise<AuditResult[]> {
    // Mock implementation
    return [];
  }

  /**
   * Compare two audits
   */
  async compareAudits(baselineId: string, currentId: string): Promise<{
    new: Finding[];
    fixed: Finding[];
    unchanged: Finding[];
  }> {
    // Mock implementation
    return {
      new: [],
      fixed: [],
      unchanged: [],
    };
  }

  /**
   * Get statistics
   */
  async getStatistics(period = 30): Promise<{
    totalAudits: number;
    totalFindings: number;
    fixedIssues: number;
    openIssues: number;
  }> {
    // Mock implementation
    return {
      totalAudits: 127,
      totalFindings: 2543,
      fixedIssues: 1892,
      openIssues: 651,
    };
  }

  /**
   * Health check
   */
  async health(): Promise<{ status: string; version: string }> {
    // Mock implementation
    return {
      status: 'healthy',
      version: '2.0.0',
    };
  }

  /**
   * Make an HTTP request to the API
   */
  private async request<T>(
    endpoint: string,
    options: {
      method?: string;
      body?: unknown;
      headers?: Record<string, string>;
    } = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.config.apiKey) {
      headers['Authorization'] = `Bearer ${this.config.apiKey}`;
    }

    const response = await fetch(url, {
      method: options.method || 'GET',
      headers,
      body: options.body ? JSON.stringify(options.body) : undefined,
      signal: AbortSignal.timeout(this.config.timeout),
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }

    return response.json() as Promise<T>;
  }
}
