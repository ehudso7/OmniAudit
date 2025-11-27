import type { VercelRequest, VercelResponse } from '@vercel/node';
import { OmniAuditSkillsEngine } from '../src/core/skills-engine';
import type { CodeInput, SkillExecutionResult } from '../src/types/index';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // CORS headers - no credentials with wildcard origin per CORS spec
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With');

  // Handle OPTIONS for CORS preflight
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
        error: 'Missing required fields: code, language',
      });
    }

    // Validate skills parameter type
    if (skills !== undefined && !Array.isArray(skills)) {
      return res.status(400).json({
        success: false,
        error: 'Skills parameter must be an array',
      });
    }

    // Validate required environment variables
    const requiredEnvVars = {
      anthropicApiKey: process.env.ANTHROPIC_API_KEY,
      tursoUrl: process.env.TURSO_URL,
      tursoToken: process.env.TURSO_TOKEN,
      upstashUrl: process.env.UPSTASH_URL,
      upstashToken: process.env.UPSTASH_TOKEN,
    };

    const missingVars = Object.entries(requiredEnvVars)
      .filter(([_, value]) => !value)
      .map(([key]) => key);

    if (missingVars.length > 0) {
      console.error('Missing required environment variables:', missingVars);
      return res.status(500).json({
        success: false,
        error: 'Server configuration error',
      });
    }

    // Initialize engine
    const engine = new OmniAuditSkillsEngine({
      anthropicApiKey: requiredEnvVars.anthropicApiKey as string,
      tursoUrl: requiredEnvVars.tursoUrl as string,
      tursoToken: requiredEnvVars.tursoToken as string,
      upstashUrl: requiredEnvVars.upstashUrl as string,
      upstashToken: requiredEnvVars.upstashToken as string,
      pineconeApiKey: process.env.PINECONE_API_KEY,
      sentryDsn: process.env.SENTRY_DSN,
    });

    // Activate and execute skills in parallel for better performance
    const skillIds = skills || ['performance-optimizer-pro'];

    // Activate all skills in parallel
    await Promise.all(skillIds.map((id) => engine.activateSkill(id)));

    // Execute analysis
    const input: CodeInput = {
      code,
      language,
      file_path,
      framework,
    };

    // Execute all skills in parallel
    const results = await Promise.all(
      skillIds.map((id) => engine.executeSkill(id, input, options || {})),
    );

    return res.status(200).json({
      success: true,
      results,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Analysis failed:', error);
    return res.status(500).json({
      success: false,
      error: 'An error occurred during analysis',
    });
  }
}
