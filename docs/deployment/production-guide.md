# Production Deployment Guide

## Prerequisites

- Docker & Docker Compose
- PostgreSQL 15+ with TimescaleDB
- Redis 7+
- SSL certificates (for HTTPS)
- Domain name

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/omniaudit.git
cd omniaudit
```

### 2. Configure Environment

```bash
cp .env.example .env.prod
```

Edit `.env.prod`:
```bash
# Database
POSTGRES_USER=omniaudit
POSTGRES_PASSWORD=<secure-password>
POSTGRES_DB=omniaudit

# Redis
REDIS_PASSWORD=<secure-password>

# Application
SECRET_KEY=<generate-with-openssl-rand-hex-32>
ENVIRONMENT=production

# Optional: External services
GITHUB_TOKEN=<your-token>
```

### 3. Initialize Database

```bash
docker-compose -f docker-compose.prod.yml up -d db redis
docker-compose -f docker-compose.prod.yml run --rm api python scripts/init_db.py
```

### 4. Start Services

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 5. Verify Deployment

```bash
# Check health
curl http://localhost/health

# Check API
curl http://localhost/api/v1/collectors

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

## Kubernetes Deployment

### 1. Create Secrets

```bash
kubectl create secret generic omniaudit-secrets \
  --from-literal=database-url=postgresql://user:pass@db:5432/omniaudit \
  --from-literal=redis-url=redis://:pass@redis:6379/0 \
  --from-literal=secret-key=<your-secret-key>
```

### 2. Apply Configurations

```bash
kubectl apply -f kubernetes/deployment.yaml
```

### 3. Verify

```bash
kubectl get pods
kubectl get services
kubectl logs -f deployment/omniaudit-api
```

## Monitoring

### Prometheus

Access: http://localhost:9090

Key metrics:
- `omniaudit_requests_total` - Request count
- `omniaudit_request_duration_seconds` - Request latency
- `omniaudit_audits_total` - Audit count

### Grafana

Access: http://localhost:3001
Default credentials: admin / admin

Import dashboard: `grafana/dashboards/omniaudit.json`

## Backup & Recovery

### Database Backup

```bash
# Backup
docker-compose exec db pg_dump -U omniaudit omniaudit > backup.sql

# Restore
docker-compose exec -T db psql -U omniaudit omniaudit < backup.sql
```

## Troubleshooting

### API not responding

```bash
# Check logs
docker-compose logs api

# Restart service
docker-compose restart api
```

### Database connection issues

```bash
# Check database
docker-compose exec db psql -U omniaudit -d omniaudit -c "SELECT 1"
```

## Security Checklist

- [ ] Change all default passwords
- [ ] Enable HTTPS with valid SSL certificates
- [ ] Configure firewall rules
- [ ] Enable rate limiting
- [ ] Set up log aggregation
- [ ] Configure automated backups
- [ ] Enable monitoring alerts
- [ ] Review and update dependencies

## Performance Optimization

### Database

```sql
-- Create indexes
CREATE INDEX CONCURRENTLY idx_metrics_timestamp ON metrics(timestamp DESC);
CREATE INDEX CONCURRENTLY idx_audits_project_status ON audits(project_id, status);
```

### API Response Caching

Add HTTP caching headers for frequently accessed data.

## Scaling

### Horizontal Scaling

```bash
# Scale API
docker-compose up -d --scale api=3

# Kubernetes
kubectl scale deployment omniaudit-api --replicas=5
```
