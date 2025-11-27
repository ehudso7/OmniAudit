import { z } from 'zod';

export const SeveritySchema = z.enum(['critical', 'high', 'medium', 'low', 'info']);
export type Severity = z.infer<typeof SeveritySchema>;

export const CategorySchema = z.enum([
  'security',
  'performance',
  'accessibility',
  'best-practices',
  'maintainability',
  'code-quality'
]);
export type Category = z.infer<typeof CategorySchema>;

export const FindingSchema = z.object({
  id: z.string(),
  rule_id: z.string(),
  title: z.string(),
  description: z.string(),
  severity: SeveritySchema,
  category: CategorySchema,
  file: z.string(),
  line: z.number().optional(),
  column: z.number().optional(),
  end_line: z.number().optional(),
  end_column: z.number().optional(),
  code_snippet: z.string().optional(),
  message: z.string(),
  recommendation: z.string().optional(),
  confidence: z.number().min(0).max(1).optional(),
  cwe: z.array(z.string()).optional(),
  owasp: z.array(z.string()).optional(),
  metadata: z.record(z.unknown()).optional(),
  created_at: z.string().optional(),
});

export type Finding = z.infer<typeof FindingSchema>;

export const AuditResultSchema = z.object({
  id: z.string(),
  project: z.string(),
  timestamp: z.string(),
  duration_ms: z.number(),
  total_files: z.number(),
  total_findings: z.number(),
  findings_by_severity: z.object({
    critical: z.number(),
    high: z.number(),
    medium: z.number(),
    low: z.number(),
    info: z.number(),
  }),
  findings: z.array(FindingSchema),
  metadata: z.object({
    version: z.string(),
    rules_count: z.number(),
    analyzers: z.array(z.string()),
  }).optional(),
});

export type AuditResult = z.infer<typeof AuditResultSchema>;

export interface ReporterOptions {
  format?: string;
  output?: string;
  pretty?: boolean;
  includeMetadata?: boolean;
  template?: string;
}

export interface Reporter {
  name: string;
  format: string;
  generate(result: AuditResult, options?: ReporterOptions): Promise<string>;
}
