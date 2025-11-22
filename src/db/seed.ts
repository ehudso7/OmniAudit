import { db } from './client';
import { PerformanceOptimizerSkill } from '../skills/performance-optimizer';
import { SecurityAuditorSkill } from '../skills/security-auditor';

async function seed() {
  console.log('🌱 Seeding database...');

  try {
    // Create system user
    console.log('Creating system user...');
    const systemUser = await db.createUser({
      email: 'system@omniaudit.dev',
      name: 'OmniAudit System',
      tier: 'enterprise',
    });
    console.log('✓ System user created:', systemUser);

    // Create demo user
    console.log('Creating demo user...');
    const demoUser = await db.createUser({
      email: 'demo@omniaudit.dev',
      name: 'Demo User',
      tier: 'pro',
    });
    console.log('✓ Demo user created:', demoUser);

    // Register pre-built skills
    console.log('Registering pre-built skills...');

    await db.createSkill({
      skill_id: PerformanceOptimizerSkill.skill_id,
      version: PerformanceOptimizerSkill.version,
      user_id: systemUser.id as string,
      definition: PerformanceOptimizerSkill as unknown as Record<string, unknown>,
      is_public: true,
    });
    console.log('✓ Performance Optimizer skill registered');

    await db.createSkill({
      skill_id: SecurityAuditorSkill.skill_id,
      version: SecurityAuditorSkill.version,
      user_id: systemUser.id as string,
      definition: SecurityAuditorSkill as unknown as Record<string, unknown>,
      is_public: true,
    });
    console.log('✓ Security Auditor skill registered');

    // Create demo project
    console.log('Creating demo project...');
    const demoProject = await db.createProject({
      user_id: demoUser.id as string,
      name: 'Demo Project',
      description: 'A sample project for testing OmniAudit',
      language: 'typescript',
      framework: 'nextjs',
    });
    console.log('✓ Demo project created:', demoProject);

    // Create some sample reviews
    console.log('Creating sample reviews...');
    const client = db.getClient();

    await client.execute({
      sql: `
        INSERT INTO skill_reviews (skill_id, user_id, rating, review)
        VALUES (?, ?, ?, ?)
      `,
      args: [
        PerformanceOptimizerSkill.skill_id,
        demoUser.id,
        5,
        'Excellent skill! Found several performance bottlenecks in my React app.',
      ],
    });

    await client.execute({
      sql: `
        INSERT INTO skill_reviews (skill_id, user_id, rating, review)
        VALUES (?, ?, ?, ?)
      `,
      args: [
        SecurityAuditorSkill.skill_id,
        demoUser.id,
        5,
        'Caught a critical SQL injection vulnerability. Highly recommended!',
      ],
    });

    console.log('✓ Sample reviews created');

    // Update skill download counts
    await db.incrementSkillDownloads(PerformanceOptimizerSkill.skill_id);
    await db.incrementSkillDownloads(PerformanceOptimizerSkill.skill_id);
    await db.incrementSkillDownloads(SecurityAuditorSkill.skill_id);

    console.log('✅ Database seeded successfully!');
  } catch (error) {
    console.error('❌ Seeding failed:', error);
    process.exit(1);
  } finally {
    await db.close();
  }
}

seed();
