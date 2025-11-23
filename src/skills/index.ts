export { PerformanceOptimizerSkill } from './performance-optimizer';
export { SecurityAuditorSkill } from './security-auditor';
export { ReactBestPracticesSkill } from './react-best-practices';
export { TypeScriptExpertSkill } from './typescript-expert';
export { ArchitectureAdvisorSkill } from './architecture-advisor';

import type { SkillDefinition } from '../types/index';
import { ArchitectureAdvisorSkill } from './architecture-advisor';
import { PerformanceOptimizerSkill } from './performance-optimizer';
import { ReactBestPracticesSkill } from './react-best-practices';
import { SecurityAuditorSkill } from './security-auditor';
import { TypeScriptExpertSkill } from './typescript-expert';

export const BUILTIN_SKILLS: Record<string, SkillDefinition> = {
  [PerformanceOptimizerSkill.skill_id]: PerformanceOptimizerSkill,
  [SecurityAuditorSkill.skill_id]: SecurityAuditorSkill,
  [ReactBestPracticesSkill.skill_id]: ReactBestPracticesSkill,
  [TypeScriptExpertSkill.skill_id]: TypeScriptExpertSkill,
  [ArchitectureAdvisorSkill.skill_id]: ArchitectureAdvisorSkill,
};

export function getAllBuiltinSkills(): SkillDefinition[] {
  return Object.values(BUILTIN_SKILLS);
}

export function getBuiltinSkill(skillId: string): SkillDefinition | undefined {
  return BUILTIN_SKILLS[skillId];
}
