import type { VercelRequest, VercelResponse } from '@vercel/node';
import { getAllBuiltinSkills, getBuiltinSkill } from '../src/skills/index';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    let { id } = req.query;

    // Handle array case - take first value
    if (Array.isArray(id)) {
      id = id[0];
    }

    // If ID provided, return specific skill
    if (id && typeof id === 'string') {
      const skill = getBuiltinSkill(id);

      if (!skill) {
        return res.status(404).json({
          success: false,
          error: 'Skill not found',
        });
      }

      return res.status(200).json({
        success: true,
        skill,
      });
    }

    // Otherwise return all skills
    const skills = getAllBuiltinSkills();

    return res.status(200).json({
      success: true,
      skills,
      count: skills.length,
    });
  } catch (error) {
    console.error('Failed to fetch skills:', error);
    return res.status(500).json({
      success: false,
      error: 'An error occurred while fetching skills',
    });
  }
}
