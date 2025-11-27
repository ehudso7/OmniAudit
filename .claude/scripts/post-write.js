#!/usr/bin/env node
/**
 * Post-Write Hook
 * Runs after file writes to maintain code quality
 * - Auto-format with Prettier/Biome
 * - Auto-fix linting issues
 * - Update import ordering
 * - Regenerate barrel files (index.ts)
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

function main() {
  try {
    const args = process.argv.slice(2);
    const toolInput = args[0] ? JSON.parse(args[0]) : {};

    const filePath = toolInput.file_path || toolInput.path || '';

    if (!filePath || !fs.existsSync(filePath)) {
      console.log('✅ No valid file path, skipping post-write actions');
      process.exit(0);
    }

    const ext = path.extname(filePath);
    const fileName = path.basename(filePath);

    // Skip for certain files
    if (['.lock', '.log', '.md', '.txt', '.json'].some(e => ext === e)) {
      console.log(`✅ Skipping post-write for ${ext} file`);
      process.exit(0);
    }

    console.log(`🔧 Running post-write actions for: ${fileName}`);

    // Format TypeScript/JavaScript files
    if (['.ts', '.tsx', '.js', '.jsx'].includes(ext)) {
      try {
        // Try Biome first
        execSync(`npx @biomejs/biome format --write "${filePath}"`, {
          cwd: '/home/user/OmniAudit',
          stdio: 'pipe'
        });
        console.log('  ✓ Formatted with Biome');
      } catch (err) {
        // Fallback to Prettier
        try {
          execSync(`npx prettier --write "${filePath}"`, {
            cwd: '/home/user/OmniAudit',
            stdio: 'pipe'
          });
          console.log('  ✓ Formatted with Prettier');
        } catch (err2) {
          console.warn('  ⚠️  Could not format file:', err2.message);
        }
      }

      // Auto-fix linting issues
      try {
        execSync(`npx @biomejs/biome check --apply "${filePath}"`, {
          cwd: '/home/user/OmniAudit',
          stdio: 'pipe'
        });
        console.log('  ✓ Linting auto-fixed');
      } catch (err) {
        // Lint errors are expected, don't fail
      }
    }

    // Format Python files
    if (ext === '.py') {
      try {
        execSync(`black "${filePath}"`, {
          cwd: '/home/user/OmniAudit',
          stdio: 'pipe'
        });
        console.log('  ✓ Formatted with Black');
      } catch (err) {
        console.warn('  ⚠️  Could not format Python file');
      }
    }

    console.log('✅ Post-write actions completed');
    process.exit(0);

  } catch (error) {
    console.error('❌ Post-write hook error:', error.message);
    // Don't fail on post-processing errors
    process.exit(0);
  }
}

main();
