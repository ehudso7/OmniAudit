# OmniAudit Deployment Architecture

## System Overview

OmniAudit is a **two-tier application**:

1. **Frontend** — React SPA (Vite), deployed to Vercel as static files
2. **Backend** — Python FastAPI app (`python-app/`), deployed separately (Railway, Fly.io, Render, VPS, etc.)

These are **independent deployments**. The frontend talks to the backend via `VITE_API_URL`.

```
┌──────────────────────────────────────────────────────────┐
│  Vercel                                                  │
│  ┌────────────────────────────┐  ┌─────────────────────┐ │
│  │  frontend/dist/            │  │  api/health.ts      │ │
│  │  (React SPA — static)      │  │  api/skills.ts      │ │
│  │                            │  │  api/analyze.ts     │ │
│  │  All /api/v1/* calls go    │  │  (stateless utils)  │ │
│  │  to VITE_API_URL (Python)  │  │                     │ │
│  └────────────────────────────┘  └─────────────────────┘ │
└──────────────────────────────────────────────────────────┘
                        │
                        │ VITE_API_URL
                        ▼
┌──────────────────────────────────────────────────────────┐
│  Backend Host (Railway / Fly.io / Render / VPS)          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  python-app/                                       │  │
│  │  FastAPI + SQLAlchemy + PostgreSQL                  │  │
│  │                                                    │  │
│  │  /api/v1/auth/*          — auth, API keys          │  │
│  │  /api/v1/reviews/*       — PR reviews (real DB)    │  │
│  │  /api/v1/browser-runs/*  — browser verification    │  │
│  │  /api/v1/notifications/* — notification system     │  │
│  │  /api/v1/repositories/*  — repo management         │  │
│  │  /api/v1/webhooks/*      — GitHub/Slack webhooks   │  │
│  │  /api/v1/release-policies — release gates          │  │
│  │  /api/v1/export/*        — data export             │  │
│  │  /api/health             — health check            │  │
│  │  /api/skills             — skill catalog           │  │
│  │  /api/analyze            — code analysis           │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

## Vercel Deployment (Frontend)

**What it deploys:**
- Static React SPA from `frontend/dist/`
- 3 stateless TypeScript serverless functions: `api/health.ts`, `api/skills.ts`, `api/analyze.ts`

**What it does NOT deploy:**
- `python-app/` (the real backend)
- Any `/api/v1/*` routes with database persistence

**Vercel config:** `vercel.json`
- Install: `pnpm install`
- Build: `cd frontend && pnpm run build`
- Output: `frontend/dist/`

## Python Backend Deployment

**Start command:**
```bash
uvicorn omniaudit.api.main:app --host 0.0.0.0 --port 8000
```

**Required environment variables:**
```
DATABASE_URL=postgresql://user:pass@host:5432/omniaudit
SECRET_KEY=<random-256-bit-hex>
```

**Database:** PostgreSQL in production, SQLite for local development.

## Environment Modes

| Mode | `VITE_API_URL` | Frontend Source | API Source | Features |
|------|----------------|-----------------|-----------|----------|
| Local dev | `http://localhost:8000` | `vite dev` | Python backend | Full |
| Production | `https://api.omniaudit.com` | Vercel static | Python backend (remote) | Full |
| Vercel demo | _(empty)_ | Vercel static | TS serverless stubs | Health, skills, analyze only |

## What Works in Each Mode

| Feature | Local Dev | Production | Vercel Demo |
|---------|-----------|------------|-------------|
| Health check | Yes | Yes | Yes |
| Skill catalog | Yes | Yes | Yes |
| Code analysis | Yes | Yes | Yes |
| Auth (register/login) | Yes | Yes | No |
| User settings | Yes | Yes | No |
| API key management | Yes | Yes | No |
| Notifications | Yes | Yes | No |
| Browser verification | Yes | Yes | No |
| PR reviews (real data) | Yes | Yes | No |
| Dashboard (real data) | Yes | Yes | No |
| Repository management | Yes | Yes | No |
| Release policies | Yes | Yes | No |

## TS Serverless Functions (Vercel-only)

These 3 functions exist in `api/` and run on Vercel as serverless functions:

| File | Route | Purpose |
|------|-------|---------|
| `api/health.ts` | `/api/health` | Returns service health status |
| `api/skills.ts` | `/api/skills` | Returns static skill catalog |
| `api/analyze.ts` | `/api/analyze` | Regex-based code analysis (no DB) |

These are **stateless utilities** that work identically to their Python counterparts. They exist so the Vercel demo deployment has minimal functionality without a backend.

They do **NOT** conflict with the Python backend because in production, `VITE_API_URL` routes all frontend requests directly to the Python host.
