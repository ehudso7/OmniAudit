import { VercelRequest, VercelResponse } from '@vercel/node';
import { OmniAuditSkillsEngine } from '../src/core/skills-engine';
import type { CodeInput, SkillExecutionResult } from '../src/types/index';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
  res.setHeader(
    'Access-Control-Allow-Headers',
    'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version, Authorization'
  );

  // Handle OPTIONS for CORS
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  // Only allow POST
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { code, language, file_path, framework, skills, options } = req.body;

    // Validate required fields
    if (!code || !language) {
      return res.status(400).json({ 
        success: false,
        error: 'Missing required fields: code, language' 
      });
    }

    // Initialize engine
    const engine = new OmniAuditSkillsEngine({
      anthropicApiKey: process.env.ANTHROPIC_API_KEY!,
      tursoUrl: process.env.TURSO_URL!,
      tursoToken: process.env.TURSO_TOKEN!,
      upstashUrl: process.env.UPSTASH_URL!,
      upstashToken: process.env.UPSTASH_TOKEN!,
      pineconeApiKey: process.env.PINECONE_API_KEY,
      sentryDsn: process.env.SENTRY_DSN,
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

    return res.status(200).json({
      success: true,
      results,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Analysis failed:', error);
    return res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    });
  }
}
