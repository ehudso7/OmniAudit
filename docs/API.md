# OmniAudit API Documentation

## Overview

OmniAudit provides a comprehensive REST API for project auditing, code quality analysis, and repository monitoring. The API is built with FastAPI and supports various integrations including GitHub webhooks, Slack notifications, and AI-powered insights.

**Base URL:** `https://your-deployment.vercel.app`
**API Version:** 0.3.0
**Documentation:** `/docs` (Swagger UI)

## Authentication

Currently, the API endpoints are open for testing. For production use, implement authentication using:
- API keys via headers
- OAuth 2.0
- GitHub App authentication

## Quick Start

### 1. Health Check

```bash
curl https://your-deployment.vercel.app/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-17T03:15:18.829622Z"
}
```

### 2. Run a Simple Audit

```bash
curl -X POST https://your-deployment.vercel.app/api/v1/audit \
  -H "Content-Type: application/json" \
  -d '{
    "collectors": {
      "git_collector": {
        "repo_path": "/path/to/repo",
        "max_commits": 50
      }
    },
    "analyzers": {
      "code_quality": {
        "project_path": "/path/to/repo",
        "languages": ["python"]
      }
    }
  }'
```

## Core Endpoints

### Collectors

#### List Available Collectors
```
GET /api/v1/collectors
```

Response:
```json
{
  "collectors": [
    {
      "name": "git_collector",
      "version": "0.1.0"
    },
    {
      "name": "github_collector",
      "version": "0.1.0"
    }
  ]
}
```

#### Run Specific Collector
```
POST /api/v1/collectors/{collector_name}/collect
```

Request body:
```json
{
  "config": {
    "repo_path": ".",
    "max_commits": 100
  }
}
```

### Analyzers

#### Run Code Quality Analysis
```
POST /api/v1/analyzers/code-quality
```

Request body:
```json
{
  "config": {
    "project_path": ".",
    "languages": ["python", "javascript"]
  }
}
```

### Full Audit Workflow

#### Run Complete Audit
```
POST /api/v1/audit
```

Request body:
```json
{
  "collectors": {
    "git_collector": {
      "repo_path": ".",
      "branch": "main",
      "max_commits": 100
    },
    "github_collector": {
      "owner": "yourusername",
      "repo": "your-repo",
      "token": "ghp_xxxxx"
    }
  },
  "analyzers": {
    "code_quality": {
      "project_path": ".",
      "languages": ["python"]
    }
  }
}
```

Response:
```json
{
  "success": true,
  "audit_id": "123e4567-e89b-12d3-a456-426614174000",
  "results": {
    "collectors": {
      "git_collector": {
        "status": "success",
        "data": {
          "commits_count": 100,
          "contributors_count": 5,
          "branches": [...]
        }
      }
    },
    "analyzers": {
      "code_quality": {
        "status": "success",
        "data": {
          "overall_score": 85.5,
          "metrics": {...}
        }
      }
    }
  }
}
```

## AI Features

### Check AI Status
```
GET /api/v1/ai/status
```

### Get AI Insights
```
POST /api/v1/ai/insights
```

Request body:
```json
{
  "project_path": "/path/to/project",
  "files": [],
  "metrics": {},
  "language_breakdown": {},
  "enable_cache": true
}
```

**Note:** Requires `AI_FEATURES_ENABLED=true` and `ANTHROPIC_API_KEY` environment variables.

## Webhooks

### GitHub Webhook
```
POST /api/v1/webhooks/github
```

Configure in GitHub repository settings:
- **Payload URL:** `https://your-deployment.vercel.app/api/v1/webhooks/github`
- **Content type:** `application/json`
- **Secret:** Set `GITHUB_WEBHOOK_SECRET` environment variable
- **Events:** Select `push`, `pull_request`, etc.

Supported events:
- `push` - Code pushed to repository
- `pull_request` - PR opened, closed, or updated
- `release` - New release published

### Slack Webhook
```
POST /api/v1/webhooks/slack
```

Configure as Slack slash command:
```
/omniaudit status
/omniaudit audit <repo>
/omniaudit help
```

### Webhook Status
```
GET /api/v1/webhooks/status
```

## Batch Operations

### Create Batch Audit
```
POST /api/v1/batch/audit
```

Request body:
```json
{
  "repositories": [
    {
      "name": "repo1",
      "repo_path": "/path/to/repo1"
    },
    {
      "name": "repo2",
      "repo_path": "/path/to/repo2"
    }
  ],
  "collectors": ["git_collector"],
  "analyzers": ["code_quality"]
}
```

Response:
```json
{
  "job_id": "batch-123-456",
  "status": "pending",
  "message": "Batch audit started for 2 repositories"
}
```

### Check Batch Status
```
GET /api/v1/batch/audit/{job_id}
```

Response:
```json
{
  "job_id": "batch-123-456",
  "status": "running",
  "total_items": 2,
  "completed_items": 1,
  "failed_items": 0,
  "started_at": "2025-11-17T03:00:00Z",
  "completed_at": null,
  "results": {...}
}
```

### List All Batch Jobs
```
GET /api/v1/batch/audit
```

## Export

### Export as CSV
```
POST /api/v1/export/csv
```

Request body:
```json
{
  "data": {
    "collectors": {...},
    "analyzers": {...}
  }
}
```

Downloads `audit_report.csv`

### Export as Markdown
```
POST /api/v1/export/markdown
```

Downloads `audit_report.md`

### Export as JSON
```
POST /api/v1/export/json
```

Downloads `audit_report.json`

### List Export Formats
```
GET /api/v1/export/formats
```

## Error Handling

All endpoints return standard HTTP status codes:

- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

Error response format:
```json
{
  "detail": "Error message here"
}
```

## Rate Limiting

**Note:** Implement rate limiting for production:
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
```

Recommended limits:
- Anonymous: 100 requests/hour
- Authenticated: 1000 requests/hour
- Webhooks: No limit (verify signatures)

## Environment Variables

Required for full functionality:

```bash
# AI Features
AI_FEATURES_ENABLED=true
ANTHROPIC_API_KEY=sk-ant-xxxxx
AI_MODEL=claude-sonnet-4-5
AI_MAX_TOKENS=4096

# Webhooks
GITHUB_WEBHOOK_SECRET=your-webhook-secret

# Optional
AI_CACHE_ENABLED=true
AI_CACHE_TTL_SECONDS=3600
```

## Examples

### Python Client

```python
import requests

BASE_URL = "https://your-deployment.vercel.app"

# Run audit
response = requests.post(
    f"{BASE_URL}/api/v1/audit",
    json={
        "collectors": {
            "git_collector": {
                "repo_path": ".",
                "max_commits": 50
            }
        }
    }
)

audit = response.json()
print(f"Audit ID: {audit['audit_id']}")
print(f"Commits: {audit['results']['collectors']['git_collector']['data']['commits_count']}")

# Export results
export_response = requests.post(
    f"{BASE_URL}/api/v1/export/csv",
    json={"data": audit["results"]}
)

with open("report.csv", "wb") as f:
    f.write(export_response.content)
```

### JavaScript Client

```javascript
const BASE_URL = "https://your-deployment.vercel.app";

// Run audit
const response = await fetch(`${BASE_URL}/api/v1/audit`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    collectors: {
      git_collector: {
        repo_path: ".",
        max_commits: 50
      }
    }
  })
});

const audit = await response.json();
console.log(`Audit ID: ${audit.audit_id}`);

// Export as JSON
const exportResponse = await fetch(`${BASE_URL}/api/v1/export/json`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ data: audit.results })
});

const blob = await exportResponse.blob();
const url = window.URL.createObjectURL(blob);
const a = document.createElement("a");
a.href = url;
a.download = "report.json";
a.click();
```

### cURL Examples

```bash
# Health check
curl https://your-deployment.vercel.app/health

# List collectors
curl https://your-deployment.vercel.app/api/v1/collectors

# Run audit
curl -X POST https://your-deployment.vercel.app/api/v1/audit \
  -H "Content-Type: application/json" \
  -d '{"collectors": {"git_collector": {"repo_path": ".", "max_commits": 10}}}'

# Export to CSV
curl -X POST https://your-deployment.vercel.app/api/v1/export/csv \
  -H "Content-Type: application/json" \
  -d '{"data": {...}}' \
  -o report.csv
```

## Support

- **Documentation:** https://github.com/yourusername/omniaudit
- **Issues:** https://github.com/yourusername/omniaudit/issues
- **API Docs:** `/docs` endpoint (Swagger UI)

## Changelog

### v0.3.0 (2025-11-17)
- Added webhook endpoints for GitHub and Slack
- Added batch audit operations
- Added export endpoints (CSV, Markdown, JSON)
- Enhanced API documentation
- Fixed Windows encoding issues
- Fixed Vercel deployment configuration

### v0.2.0
- Added AI-powered insights
- Added code quality analyzer
- Added GitHub collector

### v0.1.0
- Initial release
- Basic Git collector
- REST API endpoints
