# REST API

FastAPI-based REST API for OmniAudit.

## Planned Endpoints (Phase 3)

- `POST /api/v1/collect` - Trigger data collection
- `GET /api/v1/audits` - List audit results
- `GET /api/v1/audits/{id}` - Get specific audit
- `POST /api/v1/analyze` - Run analysis on collected data
- `GET /api/v1/reports/{id}` - Download report

## Technology Stack

- FastAPI for API framework
- Pydantic for request/response validation
- SQLAlchemy for database ORM
