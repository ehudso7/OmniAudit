/**
 * OmniAudit: Universal AI Coding Optimization Framework
 * Powered by Claude Sonnet 4.5
 */

import { OmniAuditSkillsEngine as Engine } from './core/skills-engine';

export { OmniAuditSkillsEngine } from './core/skills-engine';
export { db, DatabaseClient } from './db/client';

export {
  ASTAnalyzer,
  PerformanceAnalyzer,
  SecurityAnalyzer,
  AnalyzerFactory,
} from './analyzers/index';

export {
  ReactMemoTransformer,
  UseMemoTransformer,
  RemoveConsoleTransformer,
  TransformerFactory,
} from './transformers/index';

export {
  PerformanceOptimizerSkill,
  SecurityAuditorSkill,
  ReactBestPracticesSkill,
  TypeScriptExpertSkill,
  ArchitectureAdvisorSkill,
  getAllBuiltinSkills,
  getBuiltinSkill,
  BUILTIN_SKILLS,
} from './skills/index';

export type {
  SkillDefinition,
  EngineConfig,
  LoadedSkill,
  SkillContext,
  SkillActivation,
  CodeInput,
  ExecutionOptions,
  SkillExecutionResult,
  StaticAnalysisResult,
  AIAnalysisResult,
  Optimization,
  Analyzer,
  Transformer,
  OmniAuditConfig,
  MarketplaceSearchParams,
  MarketplaceSkill,
  SkillReview,
  UserProfile,
  Project,
  AnalysisResultRecord,
} from './types/index';

export { SkillDefinitionSchema } from './types/index';

// Version
export const VERSION = '1.0.0';

// Quick start helper
export async function createEngine(config: {
  anthropicApiKey: string;
  tursoUrl?: string;
  tursoToken?: string;
  upstashUrl?: string;
  upstashToken?: string;
}) {
  const { OmniAuditSkillsEngine } = await import('./core/skills-engine');

  return new OmniAuditSkillsEngine({
    anthropicApiKey: config.anthropicApiKey,
    tursoUrl: config.tursoUrl || process.env.TURSO_URL!,
    tursoToken: config.tursoToken || process.env.TURSO_TOKEN!,
    upstashUrl: config.upstashUrl || process.env.UPSTASH_URL!,
    upstashToken: config.upstashToken || process.env.UPSTASH_TOKEN!,
  });
}

// Default export
export default {
  OmniAuditSkillsEngine: Engine,
  createEngine,
  VERSION,
};
