/**
 * Complexity analyzer tests
 */

import { describe, it, expect } from 'vitest';
import { calculateLocScore } from '../complexity/scorers/loc.js';
import { calculateCyclomaticScore } from '../complexity/scorers/cyclomatic.js';
import { calculateDependencyScore } from '../complexity/scorers/dependencies.js';
import { detectLanguage } from '../complexity/analyzer.js';
import { Language } from '../complexity/types.js';

describe('Complexity Scoring', () => {
  describe('LOC Scorer', () => {
    it('should calculate LOC score for small file', () => {
      const content = `
function hello() {
  console.log('Hello');
}
      `.trim();

      const result = calculateLocScore(content);

      expect(result.name).toBe('loc');
      expect(result.score).toBe(1); // < 100 lines
      expect(result.metadata?.codeLines).toBe(3);
    });

    it('should calculate LOC score for medium file', () => {
      const lines = Array.from({ length: 150 }, (_, i) => `const line${i} = ${i};`);
      const content = lines.join('\n');

      const result = calculateLocScore(content);

      expect(result.score).toBe(2); // 101-300 lines
    });

    it('should calculate LOC score for large file', () => {
      const lines = Array.from({ length: 600 }, (_, i) => `const line${i} = ${i};`);
      const content = lines.join('\n');

      const result = calculateLocScore(content);

      expect(result.score).toBe(5); // 501-1000 lines
    });

    it('should ignore empty lines', () => {
      const content = `
function hello() {

  console.log('Hello');

}
      `.trim();

      const result = calculateLocScore(content);

      expect(result.metadata?.codeLines).toBe(3);
    });

    it('should ignore comment lines', () => {
      const content = `
// Comment
function hello() {
  // Another comment
  console.log('Hello');
}
      `.trim();

      const result = calculateLocScore(content);

      expect(result.metadata?.codeLines).toBe(3);
    });
  });

  describe('Cyclomatic Complexity Scorer', () => {
    it('should count if statements', () => {
      const content = `
function test() {
  if (a) {
    // do something
  }
  if (b) {
    // do something else
  }
  else if (c) {
    // another case
  }
}
      `.trim();

      const result = calculateCyclomaticScore(content);

      expect(result.metadata?.ifStatements).toBeGreaterThan(0);
      expect(result.score).toBeGreaterThan(0);
    });

    it('should count loops', () => {
      const content = `
function test() {
  for (let i = 0; i < 10; i++) {
    // do something
  }
  while (condition) {
    // do something
  }
}
      `.trim();

      const result = calculateCyclomaticScore(content);

      expect(result.metadata?.loops).toBe(2);
    });

    it('should count ternary operators', () => {
      const content = `
const value = condition ? 'yes' : 'no';
const other = test ? 1 : 2;
      `.trim();

      const result = calculateCyclomaticScore(content);

      expect(result.metadata?.ternaries).toBe(2);
    });

    it('should calculate score based on decision points', () => {
      const simpleContent = 'function test() { return true; }';
      const simpleResult = calculateCyclomaticScore(simpleContent);
      expect(simpleResult.score).toBe(1); // 0-5 decision points

      const complexContent = Array.from(
        { length: 15 },
        (_, i) => `if (condition${i}) { /* do something */ }`,
      ).join('\n');
      const complexResult = calculateCyclomaticScore(complexContent);
      expect(complexResult.score).toBeGreaterThan(1);
    });
  });

  describe('Dependency Scorer', () => {
    it('should count ES6 imports', () => {
      const content = `
import { foo } from 'foo';
import bar from 'bar';
import * as baz from 'baz';
      `.trim();

      const result = calculateDependencyScore(content);

      expect(result.metadata?.es6Imports).toBe(3);
    });

    it('should count CommonJS requires', () => {
      const content = `
const fs = require('fs');
const path = require('path');
      `.trim();

      const result = calculateDependencyScore(content);

      expect(result.metadata?.commonjsRequires).toBe(2);
    });

    it('should calculate score based on dependency count', () => {
      const fewDeps = `
import { a } from 'a';
import { b } from 'b';
      `.trim();

      const fewResult = calculateDependencyScore(fewDeps);
      expect(fewResult.score).toBe(1); // 0-5 imports

      const manyDeps = Array.from(
        { length: 12 },
        (_, i) => `import { dep${i} } from 'dep${i}';`,
      ).join('\n');

      const manyResult = calculateDependencyScore(manyDeps);
      expect(manyResult.score).toBeGreaterThan(1);
    });
  });

  describe('Language Detection', () => {
    it('should detect TypeScript', () => {
      expect(detectLanguage('/path/to/file.ts')).toBe(Language.TYPESCRIPT);
      expect(detectLanguage('/path/to/file.tsx')).toBe(Language.TYPESCRIPT);
    });

    it('should detect JavaScript', () => {
      expect(detectLanguage('/path/to/file.js')).toBe(Language.JAVASCRIPT);
      expect(detectLanguage('/path/to/file.jsx')).toBe(Language.JAVASCRIPT);
      expect(detectLanguage('/path/to/file.mjs')).toBe(Language.JAVASCRIPT);
    });

    it('should detect Python', () => {
      expect(detectLanguage('/path/to/file.py')).toBe(Language.PYTHON);
    });

    it('should detect Java', () => {
      expect(detectLanguage('/path/to/File.java')).toBe(Language.JAVA);
    });

    it('should detect Go', () => {
      expect(detectLanguage('/path/to/file.go')).toBe(Language.GO);
    });

    it('should detect Rust', () => {
      expect(detectLanguage('/path/to/file.rs')).toBe(Language.RUST);
    });

    it('should detect C/C++', () => {
      expect(detectLanguage('/path/to/file.c')).toBe(Language.C);
      expect(detectLanguage('/path/to/file.h')).toBe(Language.C);
      expect(detectLanguage('/path/to/file.cpp')).toBe(Language.CPP);
      expect(detectLanguage('/path/to/file.hpp')).toBe(Language.CPP);
    });

    it('should return UNKNOWN for unknown extensions', () => {
      expect(detectLanguage('/path/to/file.xyz')).toBe(Language.UNKNOWN);
    });
  });
});
