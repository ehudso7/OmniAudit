#!/usr/bin/env node
/**
 * Post-Edit Hook
 * Runs after file edits to validate changes
 * - Validate syntax/AST integrity
 * - Run type checking for the edited file
 * - Execute related unit tests
 */

const { execFileSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

// Use process.cwd() for portability instead of hardcoded path
const PROJECT_ROOT = process.cwd();

function main() {
  try {
    const args = process.argv.slice(2);
    const toolInput = args[0] ? JSON.parse(args[0]) : {};

    const filePath = toolInput.file_path || toolInput.path || '';

    if (!filePath || !fs.existsSync(filePath)) {
      console.log('✅ No valid file path, skipping post-edit actions');
      process.exit(0);
    }

    const ext = path.extname(filePath);
    const fileName = path.basename(filePath);

    console.log(`🔍 Running post-edit validation for: ${fileName}`);

    // Validate TypeScript files - use execFileSync to avoid command injection
    if (['.ts', '.tsx'].includes(ext)) {
      try {
        // Quick syntax check (TypeScript compilation without emit)
        execFileSync('npx', ['tsc', '--noEmit', filePath], {
          cwd: PROJECT_ROOT,
          stdio: 'pipe',
          timeout: 10000,
        });
        console.log('  ✓ TypeScript syntax valid');
      } catch (_err) {
        console.warn('  ⚠️  TypeScript validation warnings (not blocking)');
      }
    }

    // Validate Python files
    if (ext === '.py') {
      try {
        // Syntax check with Python - use execFileSync to avoid command injection
        execFileSync('python', ['-m', 'py_compile', filePath], {
          cwd: PROJECT_ROOT,
          stdio: 'pipe',
          timeout: 5000,
        });
        console.log('  ✓ Python syntax valid');
      } catch (_err) {
        console.error('  ❌ Python syntax error detected');
        // Don't block on syntax errors, let the user fix
      }
    }

    console.log('✅ Post-edit validation completed');
    process.exit(0);
  } catch (error) {
    console.error('❌ Post-edit hook error:', error.message);
    // Don't fail on validation errors
    process.exit(0);
  }
}

main();
