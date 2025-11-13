# OmniAudit 🔍

[![CI](https://github.com/yourusername/omniaudit/workflows/CI/badge.svg)](https://github.com/yourusername/omniaudit/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](https://github.com/yourusername/omniaudit)

> **Universal Project Auditing & Monitoring Platform**

Comprehensive, language-agnostic platform for auditing code quality, performance, business metrics, and project health.

## ✨ Features

### 🔌 Data Collection
- **Git Analysis** - Commits, branches, contributors, history
- **GitHub/GitLab** - PRs, issues, workflows, pipelines
- **CI/CD** - Jenkins, CircleCI, GitLab CI integration
- **Business Metrics** - Custom SQL queries for KPIs
- **Custom Collectors** - Extensible plugin architecture

### 📊 Code Analysis
- **Multi-Language** - Python, JavaScript, Go, Java, Ruby, PHP
- **Quality Metrics** - Test coverage, complexity, linting
- **Performance** - Log parsing, response time metrics
- **Dependencies** - Security scanning, version tracking
- **Historical Trends** - Time-series tracking with TimescaleDB

### 🎯 Insights & Reporting
- **Interactive Dashboard** - React-based real-time visualizations
- **Time-Series Tracking** - Historical metrics and trends
- **Alerts** - Email, Slack, webhook notifications
- **Reports** - Markdown, JSON export formats
- **REST API** - Full programmatic access

### 🚀 Production Ready
- **Docker** - Multi-stage optimized builds
- **Kubernetes** - Complete deployment manifests
- **Monitoring** - Prometheus metrics, Grafana dashboards
- **Security** - Rate limiting, authentication, HTTPS
- **Scalable** - Horizontal scaling, load balancing
- **Highly Available** - Health checks, auto-recovery

## 🚀 Quick Start

### Using Docker

```bash
# Clone repository
git clone https://github.com/yourusername/omniaudit.git
cd omniaudit

# Configure environment
cp .env.example .env.prod
# Edit .env.prod with your settings

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Initialize database
docker-compose -f docker-compose.prod.yml run --rm api python scripts/init_db.py

# Access dashboard
open http://localhost
```

### Local Development

```bash
# Install dependencies
pip install -e .

# Start databases (requires Docker)
docker-compose up -d db redis

# Initialize database
python scripts/init_db.py

# Run API
uvicorn src.omniaudit.api.main:app --reload

# Run frontend (in another terminal)
cd frontend
npm install
npm run dev

# Run CLI
omniaudit audit --repo-path .
```

## 📖 Documentation

- [Production Deployment Guide](docs/deployment/production-guide.md)
- [API Documentation](http://localhost:8000/docs)
- [Architecture Overview](#-architecture)

## 🎯 Use Cases

### For Developers
- Track code quality over time
- Identify technical debt hotspots
- Monitor test coverage trends
- Analyze commit patterns

### For Engineering Managers
- Team productivity metrics
- Sprint health tracking
- Resource allocation insights
- Release readiness assessment

### For Executives
- Engineering efficiency KPIs
- Business metrics correlation
- ROI on development investment
- Strategic planning data

## 📊 Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (React)                   │
│  Dashboard • Charts • Reports • Configuration       │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────┐
│                REST API (FastAPI)                    │
│  Endpoints • Validation • Auth • Rate Limiting      │
└────┬───────────────────────────────────────────┬────┘
     │                                           │
┌────┴──────────┐                    ┌──────────┴─────┐
│  Collectors   │                    │   Analyzers    │
│  Git, GitHub  │                    │  Code Quality  │
│  CI/CD, APM   │                    │  Performance   │
└────┬──────────┘                    └──────────┬─────┘
     │                                           │
┌────┴───────────────────────────────────────────┴────┐
│              Database Layer                          │
│  PostgreSQL + TimescaleDB + Redis                   │
└─────────────────────────────────────────────────────┘
```

## 🛠️ Technology Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, Alembic
- **Frontend:** React 18, TypeScript, Vite, Recharts
- **Database:** PostgreSQL 15, TimescaleDB, Redis
- **Deployment:** Docker, Kubernetes, nginx
- **Monitoring:** Prometheus, Grafana
- **CI/CD:** GitHub Actions

## 📈 Project Status

**Phase 3 Complete** ✅
- ✅ Multi-language code analysis (6 languages)
- ✅ CI/CD platform integrations (GitLab, Jenkins, CircleCI)
- ✅ Database persistence with TimescaleDB
- ✅ Production Docker & Kubernetes configs
- ✅ Monitoring & observability (Prometheus/Grafana)
- ✅ Security hardening (rate limiting, auth)
- ✅ Performance optimization
- ✅ Complete documentation

## 🔧 CLI Usage

```bash
# Run full audit
omniaudit audit --repo-path .

# Collect Git data
omniaudit collect-git --repo-path . --max-commits 1000

# Analyze code quality
omniaudit analyze-quality --project-path . --languages python javascript

# Get help
omniaudit --help
```

## 🐳 Docker Deployment

### Production

```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Start all services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down
```

## ☸️ Kubernetes Deployment

```bash
# Create secrets
kubectl create secret generic omniaudit-secrets \
  --from-literal=database-url=postgresql://... \
  --from-literal=redis-url=redis://... \
  --from-literal=secret-key=...

# Deploy
kubectl apply -f kubernetes/deployment.yaml

# Check status
kubectl get pods -l app=omniaudit
kubectl logs -f deployment/omniaudit-api
```

## 📊 Monitoring

### Metrics Endpoint

```bash
curl http://localhost:8000/metrics
```

### Key Metrics
- `omniaudit_requests_total` - Request count by endpoint
- `omniaudit_request_duration_seconds` - Request latency
- `omniaudit_audits_total` - Total audits executed
- `omniaudit_collector_success_total` - Collector success count
- `omniaudit_db_connections` - Database connection pool size

## 🔒 Security

- **Authentication:** JWT token-based (configurable)
- **Rate Limiting:** Per-IP request limits
- **HTTPS:** SSL/TLS support with Let's Encrypt
- **Secrets Management:** Environment-based configuration
- **SQL Injection:** Protected via SQLAlchemy ORM
- **XSS Protection:** Security headers configured

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

Built with inspiration from SonarQube, New Relic, Grafana, and Lighthouse.

---

**Built with ❤️ for developers, by developers**

