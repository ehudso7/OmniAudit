// Export main client
export { OmniAuditClient } from './client.js';

// Export streaming client
export {
  StreamingAuditClient,
  createStreamingAudit,
  runAuditWithHooks,
  type AuditHooks,
} from './streaming.js';

// Export all types
export type {
  SDKConfig,
  AuditRequest,
  AuditResult,
  AuditProgress,
  Finding,
  Rule,
  Plugin,
  EventMap,
} from './types.js';

// Convenience factory function
import { OmniAuditClient } from './client.js';
import type { SDKConfig } from './types.js';

/**
 * Create a new OmniAudit client
 */
export function createClient(config: Partial<SDKConfig>): OmniAuditClient {
  return new OmniAuditClient(config);
}

/**
 * Quick audit function for simple use cases
 */
export async function audit(path: string, config?: Partial<SDKConfig>) {
  const client = new OmniAuditClient(config || {});
  return client.audit({ path });
}

// Re-export schemas for validation
export { SDKConfigSchema } from './types.js';

export const SDK_VERSION = '2.0.0';
