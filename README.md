# OmniAudit: Universal AI Coding Optimization Framework

**Production-Ready Implementation with Advanced Skills System**

Powered by Claude Sonnet 4.5 and built with the latest 2025 technologies.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-blue)](https://www.typescriptlang.org/)
[![Bun](https://img.shields.io/badge/Bun-1.1+-black)](https://bun.sh/)

---

## 🚀 Features

- **🤖 AI-Powered Analysis**: Leverages Claude Sonnet 4.5 for deep code understanding
- **🔌 Extensible Skills System**: Plug-and-play skills for different optimization goals
- **⚡ Multiple Analyzers**: AST, performance, security, and custom analyzers
- **🔧 Auto-Fix Capabilities**: Automatically apply safe code transformations
- **📊 Real-time Analytics**: Track analysis metrics and performance
- **🌍 Edge Deployment**: Deploy to Cloudflare Workers for global low-latency
- **💾 Smart Caching**: Redis-backed caching for faster repeated analysis
- **🎨 VS Code Extension**: Seamless IDE integration with inline diagnostics
- **📦 CLI Tool**: Powerful command-line interface for CI/CD integration

---

## 📦 Installation

### Using Bun (Recommended)

```bash
bun add omniaudit
```

### Using npm

```bash
npm install omniaudit
```

### Global CLI Installation

```bash
bun add -g omniaudit
```

---

## 🏃 Quick Start

### 1. Initialize OmniAudit

```bash
omniaudit init
```

This creates `omniaudit.config.ts`, optional pre-commit hooks, and CI configuration.

### 2. Configure API Key

Create a `.env` file:

```bash
ANTHROPIC_API_KEY=your_api_key_here
TURSO_URL=your_turso_database_url
TURSO_TOKEN=your_turso_token
UPSTASH_URL=your_upstash_redis_url
UPSTASH_TOKEN=your_upstash_token
```

### 3. Analyze Code

```bash
# Analyze a single file
omniaudit analyze src/index.ts

# With specific skills
omniaudit analyze src/ --skills performance-optimizer-pro security-auditor-enterprise

# Auto-fix issues
omniaudit analyze src/ --auto-fix

# Save results
omniaudit analyze src/ --output report.json --format json
```

---

## 🎯 Built-in Skills

### 1. Performance Optimizer Pro
Detects React re-render issues, expensive computations, and memory leaks.

### 2. Security Auditor Enterprise
OWASP Top 10 vulnerability detection, SQL injection, and XSS scanning.

### 3. React Best Practices
Hooks rules enforcement and component composition patterns.

### 4. TypeScript Expert
Advanced type checking and generic optimization.

### 5. Architecture Advisor
SOLID principles validation and design pattern suggestions.

---

## 💻 Programmatic Usage

```typescript
import { createEngine } from 'omniaudit';

const engine = await createEngine({
  anthropicApiKey: process.env.ANTHROPIC_API_KEY!,
});

await engine.activateSkill('performance-optimizer-pro');

const result = await engine.executeSkill(
  'performance-optimizer-pro',
  {
    code: 'export default function MyComponent({ data }) { ... }',
    language: 'typescript',
    framework: 'react',
  }
);

console.log(result.optimizations);
```

---

## 🔧 VS Code Extension

### Installation

1. Open VS Code Extensions (Ctrl+Shift+X)
2. Search for "OmniAudit"
3. Click Install

### Usage

- **Analyze Current File**: `Ctrl+Shift+P` → "OmniAudit: Analyze Current File"
- **Auto-fix**: Click diagnostic → "Quick Fix" → "Apply OmniAudit fix"

---

## 🌐 API Deployment

### Deploy to Cloudflare Workers

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### API Endpoints

```bash
# Analyze code
curl -X POST https://api.omniaudit.dev/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "code": "const x = 1;",
    "language": "javascript",
    "skills": ["performance-optimizer-pro"]
  }'

# List skills
curl https://api.omniaudit.dev/api/v1/skills
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        OmniAudit Core                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────┐  │
│  │ Skills Engine  │  │ Analysis Core  │  │  Optimization   │  │
│  │  - Registry    │  │  - AST Parser  │  │    Engine       │  │
│  │  - Loader      │  │  - Static      │  │  - Refactor     │  │
│  │  - Executor    │  │  - Runtime     │  │  - Transform    │  │
│  └────────────────┘  └────────────────┘  └─────────────────┘  │
│           │                   │                      │           │
│           └───────────────────┴──────────────────────┘           │
│                              │                                   │
│                   ┌──────────▼──────────┐                       │
│                   │   AI Orchestrator   │                       │
│                   │  - Claude Sonnet 4.5│                       │
│                   └─────────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

- **Runtime**: Bun 1.1+ / Node.js 22+
- **Language**: TypeScript 5.7+
- **AI**: Claude Sonnet 4.5
- **Database**: Turso (LibSQL)
- **Cache**: Upstash Redis
- **Edge**: Cloudflare Workers
- **Analysis**: Babel, ESLint
- **Monitoring**: Sentry

---

## 🔄 CI/CD Integration

### GitHub Actions

```yaml
name: OmniAudit

on: [push, pull_request]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Bun
        uses: oven-sh/setup-bun@v1
      - name: Install OmniAudit
        run: bun add -g omniaudit
      - name: Run Analysis
        run: omniaudit analyze src/ --format json
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

---

## 📄 License

MIT © OmniAudit Team

---

## 🙏 Credits

- Powered by [Anthropic Claude](https://www.anthropic.com/)
- Built with [Bun](https://bun.sh/)
- Deployed on [Cloudflare Workers](https://workers.cloudflare.com/)

---

**Made with ❤️ by the OmniAudit Team**
