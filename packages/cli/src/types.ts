import { z } from 'zod';

export const CLIConfigSchema = z.object({
  apiUrl: z.string().url().default('http://localhost:8000'),
  apiKey: z.string().optional(),
  outputFormat: z.string().default('json'),
  outputPath: z.string().optional(),
  verbose: z.boolean().default(false),
  quiet: z.boolean().default(false),
  color: z.boolean().default(true),
});

export type CLIConfig = z.infer<typeof CLIConfigSchema>;

export interface CommandContext {
  config: CLIConfig;
  spinner?: any;
  verbose: boolean;
}

export interface AuditOptions {
  path: string;
  format?: string;
  output?: string;
  rules?: string[];
  severity?: string[];
  fix?: boolean;
  watch?: boolean;
  ci?: boolean;
}

export interface FindingFilter {
  severity?: string[];
  category?: string[];
  file?: string;
  ruleId?: string;
}
