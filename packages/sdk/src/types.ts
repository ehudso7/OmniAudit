import { z } from 'zod';

export const SDKConfigSchema = z.object({
  apiUrl: z.string().url(),
  apiKey: z.string().optional(),
  timeout: z.number().default(30000),
  retries: z.number().default(3),
  retryDelay: z.number().default(1000),
});

export type SDKConfig = z.infer<typeof SDKConfigSchema>;

export interface AuditRequest {
  path: string;
  rules?: string[];
  severity?: string[];
  options?: {
    parallel?: boolean;
    maxWorkers?: number;
    timeout?: number;
    cache?: boolean;
  };
}

export interface AuditProgress {
  stage: 'initializing' | 'scanning' | 'analyzing' | 'reporting' | 'complete' | 'error';
  progress: number; // 0-100
  message: string;
  filesScanned?: number;
  totalFiles?: number;
  findingsCount?: number;
}

export interface Finding {
  id: string;
  rule_id: string;
  title: string;
  description: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  category: string;
  file: string;
  line?: number;
  column?: number;
  end_line?: number;
  end_column?: number;
  code_snippet?: string;
  message: string;
  recommendation?: string;
  confidence?: number;
  metadata?: Record<string, unknown>;
}

export interface AuditResult {
  id: string;
  project: string;
  timestamp: string;
  duration_ms: number;
  total_files: number;
  total_findings: number;
  findings_by_severity: {
    critical: number;
    high: number;
    medium: number;
    low: number;
    info: number;
  };
  findings: Finding[];
  metadata?: {
    version: string;
    rules_count: number;
    analyzers: string[];
  };
}

export type EventMap = {
  progress: (progress: AuditProgress) => void;
  finding: (finding: Finding) => void;
  complete: (result: AuditResult) => void;
  error: (error: Error) => void;
};

export interface Rule {
  id: string;
  name: string;
  description: string;
  category: string;
  severity: string;
  enabled: boolean;
  autoFixable: boolean;
}

export interface Plugin {
  name: string;
  version: string;
  enabled: boolean;
  config?: Record<string, unknown>;
}
