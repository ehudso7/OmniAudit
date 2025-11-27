import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['src/**/*.ts'],
      exclude: [
        'src/**/*.test.ts',
        'src/**/__tests__/**',
        'src/**/types.ts', // Exclude type-only files
        'src/types/**',
        'src/index.ts',
      ],
      thresholds: {
        lines: 83,
        functions: 88,
        branches: 82,
        statements: 83,
      },
    },
  },
});
