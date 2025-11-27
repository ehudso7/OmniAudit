import { describe, it, expect } from 'vitest';
import { RegexMatcher } from '../matchers/regex-matcher';
import type { Rule, FileToAnalyze } from '../types';

describe('RegexMatcher', () => {
  const matcher = new RegexMatcher();

  const createRule = (pattern: string, flags?: string): Rule => ({
    id: 'TEST001',
    name: 'Test Rule',
    description: 'Test description',
    severity: 'medium',
    category: 'security',
    languages: ['javascript'],
    patterns: { regex: pattern, flags },
    enabled: true,
  });

  it('should match simple regex pattern', () => {
    const rule = createRule('console\\.log');
    const file: FileToAnalyze = {
      path: 'test.js',
      content: 'console.log("Hello");',
      language: 'javascript',
    };

    const matches = matcher.match(file.content, rule, file);
    expect(matches).toHaveLength(1);
    expect(matches[0]?.line).toBeGreaterThan(0);
  });

  it('should match with capture groups', () => {
    const rule = createRule('const\\s+(\\w+)\\s*=');
    const file: FileToAnalyze = {
      path: 'test.js',
      content: 'const myVar = 123;',
      language: 'javascript',
    };

    const matches = matcher.match(file.content, rule, file);
    expect(matches).toHaveLength(1);
    expect(matches[0]?.message).toContain('myVar');
  });

  it('should use cached regex', () => {
    const rule = createRule('test');
    const file: FileToAnalyze = {
      path: 'test.js',
      content: 'test test test',
      language: 'javascript',
    };

    // First call
    matcher.match(file.content, rule, file);

    const stats = matcher.getCacheStats();
    expect(stats.size).toBeGreaterThan(0);

    // Second call should use cache
    const matches = matcher.match(file.content, rule, file);
    expect(matches).toHaveLength(3);
  });

  it('should handle multiline content', () => {
    const rule = createRule('function\\s+\\w+', 'gm');
    const file: FileToAnalyze = {
      path: 'test.js',
      content: 'function test1() {}\nfunction test2() {}',
      language: 'javascript',
    };

    const matches = matcher.match(file.content, rule, file);
    expect(matches).toHaveLength(2);
  });

  it('should extract snippet around match', () => {
    const rule = createRule('console\\.log');
    const file: FileToAnalyze = {
      path: 'test.js',
      content: 'const x = 1;\nconsole.log(x);\nconst y = 2;',
      language: 'javascript',
    };

    const matches = matcher.match(file.content, rule, file);
    expect(matches[0]?.snippet).toContain('console.log');
  });

  it('should clear cache', () => {
    const rule = createRule('test');
    const file: FileToAnalyze = {
      path: 'test.js',
      content: 'test',
      language: 'javascript',
    };

    matcher.match(file.content, rule, file);
    expect(matcher.getCacheStats().size).toBeGreaterThan(0);

    matcher.clearCache();
    expect(matcher.getCacheStats().size).toBe(0);
  });
});
