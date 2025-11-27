#!/usr/bin/env node
/**
 * Performance Benchmark for Rules Engine
 */

import { RulesEngine } from './src/engine';
import { RuleLoader } from './src/rule-loader';
import type { FileToAnalyze } from './src/types';
import * as path from 'path';

const COLORS = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

async function main() {
  console.log(`${COLORS.cyan}========================================`);
  console.log('Rules Engine Performance Benchmark');
  console.log(`========================================${COLORS.reset}\n`);

  // Load all built-in rules
  console.log(`${COLORS.blue}Loading rules...${COLORS.reset}`);
  const loader = new RuleLoader();
  const rulesPath = path.join(process.cwd(), '../../rules/builtin');

  let rules;
  try {
    rules = await loader.loadDirectory(rulesPath);
  } catch (error) {
    console.log(`${COLORS.yellow}Note: Built-in rules not loaded (expected in test environment)${COLORS.reset}`);
    // Create sample rules for benchmarking
    rules = [
      {
        id: 'BENCH001',
        name: 'Benchmark Rule 1',
        description: 'Test rule for benchmarking',
        severity: 'medium' as const,
        category: 'security' as const,
        languages: ['javascript', 'typescript'],
        patterns: { regex: 'console\\.log' },
        enabled: true,
      },
      {
        id: 'BENCH002',
        name: 'Benchmark Rule 2',
        description: 'Test rule for benchmarking',
        severity: 'high' as const,
        category: 'quality' as const,
        languages: ['javascript', 'typescript'],
        patterns: { regex: 'debugger' },
        enabled: true,
      },
    ];
  }

  console.log(`${COLORS.green}✓ Loaded ${rules.length} rules${COLORS.reset}\n`);

  // Create engine
  const engine = new RulesEngine({ rules });

  // Display rule statistics
  const stats = engine.getStats();
  console.log(`${COLORS.cyan}Rule Statistics:${COLORS.reset}`);
  console.log(`  Total: ${stats.total}`);
  console.log(`  By Category:`, stats.byCategory);
  console.log(`  By Severity:`, stats.bySeverity);
  console.log('');

  // Test file samples
  const testFiles: FileToAnalyze[] = [
    {
      path: 'test1.js',
      content: `
        const apiKey = "example_key_XXXXXXXXXXXX";
        const password = "example_password_123";
        console.log("Debug:", apiKey);

        function processData(data) {
          if (!data) throw new Error("Invalid");
          return data.map(item => item.value);
        }
      `,
      language: 'javascript',
    },
    {
      path: 'test2.ts',
      content: `
        import React from 'react';

        function Component({ data }: any) {
          const [state, setState] = React.useState([]);

          React.useEffect(() => {
            fetch('https://api.example.com/data')
              .then(res => res.json())
              .then(setState);
          }, []);

          return data.map((item, i) => <div key={i}>{item}</div>);
        }
      `,
      language: 'typescript',
    },
    {
      path: 'test3.py',
      content: `
        import os

        def process_file(filename):
            file = open(filename)
            data = file.read()
            return data

        def validate(data):
            assert data is not None
            return type(data) == str
      `,
      language: 'python',
    },
  ];

  // Benchmark 1: Single file analysis
  console.log(`${COLORS.cyan}Benchmark 1: Single File Analysis${COLORS.reset}`);
  const singleFileBench = await engine.benchmark(testFiles[0]!, 100);
  console.log(`  Iterations: 100`);
  console.log(`  Total time: ${singleFileBench.totalMs.toFixed(2)}ms`);
  console.log(`  Avg time: ${singleFileBench.avgMs.toFixed(2)}ms`);
  console.log(`  Rules/second: ${singleFileBench.rulesPerSecond.toLocaleString()}`);
  console.log(`  Matches found: ${singleFileBench.matchesFound}`);
  console.log('');

  // Benchmark 2: Multiple files
  console.log(`${COLORS.cyan}Benchmark 2: Multiple Files Analysis${COLORS.reset}`);
  const startTime = Date.now();
  const result = await engine.analyzeFiles(testFiles);
  const endTime = Date.now();

  console.log(`  Files analyzed: ${result.stats.filesAnalyzed}`);
  console.log(`  Rules executed: ${result.stats.rulesExecuted}`);
  console.log(`  Matches found: ${result.stats.matchesFound}`);
  console.log(`  Total time: ${(endTime - startTime).toFixed(2)}ms`);
  console.log(`  Avg per file: ${((endTime - startTime) / testFiles.length).toFixed(2)}ms`);
  console.log('');

  // Benchmark 3: Rule filtering
  console.log(`${COLORS.cyan}Benchmark 3: Rule Filtering${COLORS.reset}`);
  const filterStart = Date.now();
  for (let i = 0; i < 10000; i++) {
    engine.filterRules({ categories: ['security'], severities: ['critical', 'high'] });
  }
  const filterEnd = Date.now();
  console.log(`  Iterations: 10,000`);
  console.log(`  Total time: ${(filterEnd - filterStart).toFixed(2)}ms`);
  console.log(`  Avg time: ${((filterEnd - filterStart) / 10000).toFixed(4)}ms`);
  console.log('');

  // Display sample matches
  if (result.matches.length > 0) {
    console.log(`${COLORS.cyan}Sample Findings:${COLORS.reset}`);
    const sampleMatches = result.matches.slice(0, 5);
    for (const match of sampleMatches) {
      console.log(`  ${COLORS.yellow}[${match.severity.toUpperCase()}]${COLORS.reset} ${match.ruleId}: ${match.message}`);
      console.log(`    File: ${match.file}:${match.line}:${match.column}`);
    }
    console.log('');
  }

  // Summary
  console.log(`${COLORS.green}========================================`);
  console.log('Benchmark Complete!');
  console.log(`========================================${COLORS.reset}`);
}

main().catch(console.error);
