# OmniAudit Quick Start Guide

Get started with OmniAudit in 5 minutes!

## 🚀 Try the Live API

Visit our deployed API: https://omni-audit-c1oeztkup-everton-hudsons-projects.vercel.app

### 1. Check Health
```bash
curl https://omni-audit-c1oeztkup-everton-hudsons-projects.vercel.app/health
```

### 2. Explore Interactive Docs
Open in browser: https://omni-audit-c1oeztkup-everton-hudsons-projects.vercel.app/docs

### 3. Run Your First Audit

```bash
curl -X POST https://omni-audit-c1oeztkup-everton-hudsons-projects.vercel.app/api/v1/audit \
  -H "Content-Type: application/json" \
  -d '{
    "collectors": {
      "git_collector": {
        "repo_path": "/path/to/your/repo",
        "max_commits": 10
      }
    }
  }'
```

## 📦 Local Installation

### Prerequisites
- Python 3.10+
- Git

### Install

```bash
# Clone repository
git clone https://github.com/yourusername/omniaudit.git
cd omniaudit

# Install dependencies
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

### Run Locally

```bash
# Start API server
python -m omniaudit.api.main

# Or use uvicorn
uvicorn omniaudit.api.main:app --reload --port 8000
```

Visit: http://localhost:8000/docs

## 🎯 Common Use Cases

### Use Case 1: Audit a Git Repository

```python
from omniaudit.collectors.git_collector import GitCollector

collector = GitCollector({
    'repo_path': '.',
    'max_commits': 100
})

result = collector.collect()
print(f"Found {result['data']['commits_count']} commits")
print(f"Contributors: {result['data']['contributors_count']}")
```

### Use Case 2: Analyze Code Quality

```python
from omniaudit.analyzers.code_quality import CodeQualityAnalyzer

analyzer = CodeQualityAnalyzer({
    'project_path': '.',
    'languages': ['python']
})

result = analyzer.analyze({})
print(f"Quality Score: {result['data']['overall_score']}/100")
```

### Use Case 3: Generate Report

```python
from omniaudit.reporters import MarkdownReporter

# Prepare audit data
audit_data = {
    'collectors': {'git_collector': {...}},
    'analyzers': {'code_quality': {...}}
}

# Generate Markdown report
reporter = MarkdownReporter()
reporter.generate(audit_data, 'audit_report.md')
```

### Use Case 4: Batch Audit Multiple Repos

```bash
curl -X POST http://localhost:8000/api/v1/batch/audit \
  -H "Content-Type: application/json" \
  -d '{
    "repositories": [
      {"name": "repo1", "repo_path": "/path/to/repo1"},
      {"name": "repo2", "repo_path": "/path/to/repo2"}
    ],
    "collectors": ["git_collector"]
  }'
```

Response:
```json
{
  "job_id": "abc-123",
  "status": "pending"
}
```

Check status:
```bash
curl http://localhost:8000/api/v1/batch/audit/abc-123
```

### Use Case 5: Export Results

```bash
# Export as CSV
curl -X POST http://localhost:8000/api/v1/export/csv \
  -H "Content-Type: application/json" \
  -d '{"data": {...}}' \
  -o report.csv

# Export as Markdown
curl -X POST http://localhost:8000/api/v1/export/markdown \
  -H "Content-Type: application/json" \
  -d '{"data": {...}}' \
  -o report.md
```

## 🔗 Integrations

### GitHub Webhook

1. Go to your repo → Settings → Webhooks → Add webhook
2. **Payload URL:** `https://your-deployment.vercel.app/api/v1/webhooks/github`
3. **Content type:** `application/json`
4. **Secret:** Generate a secret token
5. **Events:** Select `push`, `pull_request`
6. Set environment variable: `GITHUB_WEBHOOK_SECRET=your-secret`

### Slack Integration

1. Create Slack slash command
2. **Command:** `/omniaudit`
3. **Request URL:** `https://your-deployment.vercel.app/api/v1/webhooks/slack`
4. Available commands:
   - `/omniaudit status`
   - `/omniaudit help`

## 🤖 AI Features (Optional)

Enable AI-powered insights:

```bash
# Set environment variables
export AI_FEATURES_ENABLED=true
export ANTHROPIC_API_KEY=sk-ant-xxxxx

# Use AI insights
curl -X POST http://localhost:8000/api/v1/ai/insights \
  -H "Content-Type: application/json" \
  -d '{
    "project_path": ".",
    "files": [],
    "metrics": {},
    "enable_cache": true
  }'
```

## 📊 Dashboard (Coming Soon)

A React-based frontend dashboard is being developed to visualize:
- Repository statistics
- Code quality trends
- Contributor analytics
- Real-time audit results

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/unit/
pytest tests/integration/

# With coverage
pytest --cov=src/omniaudit --cov-report=html
```

## 🚢 Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set environment variables in Vercel dashboard
# - AI_FEATURES_ENABLED
# - ANTHROPIC_API_KEY
# - GITHUB_WEBHOOK_SECRET
```

## 📖 Next Steps

- Read [Full API Documentation](./API.md)
- Explore [Examples](../examples/)
- Check [Architecture Guide](./ARCHITECTURE.md)
- Join our [Community](https://github.com/yourusername/omniaudit/discussions)

## 🆘 Need Help?

- **Documentation:** `/docs` endpoint
- **Issues:** GitHub Issues
- **Discussions:** GitHub Discussions

## 🎉 You're Ready!

You now have OmniAudit running. Try these next:

1. ✅ Audit your first repository
2. ✅ Set up a GitHub webhook
3. ✅ Generate your first report
4. ✅ Explore the AI features
5. ✅ Build something awesome!

Happy auditing! 🔍
