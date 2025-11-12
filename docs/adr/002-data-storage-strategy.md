# ADR-002: Data Storage Strategy

**Status:** Accepted
**Date:** 2025-10-05
**Deciders:** Core Team

## Context

OmniAudit needs to store:

- Raw collected data from various sources
- Analysis results and metrics
- Historical trends
- Configuration and metadata

Requirements:

- Support for time-series data
- Flexible schema (different collectors produce different data)
- Fast queries for dashboards
- Long-term archival
- Easy backup and restore

## Decision

Multi-tier storage strategy:

1. **PostgreSQL** - Primary relational data
   - Audit metadata, runs, configurations
   - User accounts and permissions
   - Structured analysis results

2. **MongoDB** - Document storage for flexible schemas
   - Raw collector output (JSON documents)
   - Plugin configurations
   - Unstructured analysis data

3. **TimescaleDB** - Time-series metrics (PostgreSQL extension)
   - Commit frequency over time
   - Build success rates
   - Performance metrics

4. **File System** - Archival and exports
   - JSON/YAML exports
   - Generated reports (PDF, HTML)
   - Long-term cold storage

## Consequences

### Positive

- PostgreSQL provides ACID guarantees for critical data
- MongoDB handles varying collector schemas naturally
- TimescaleDB optimized for time-series queries
- Can query across databases via application layer
- Each storage optimized for its use case

### Negative

- Multiple databases increase operational complexity
- Need to maintain consistency across stores
- More backup strategies required
- Higher resource requirements
- Need expertise in multiple database systems

## Alternatives Considered

### Single PostgreSQL with JSONB

**Rejected:** While PostgreSQL JSONB is powerful, it doesn't match MongoDB's flexibility for deeply nested documents and schema evolution.

### Time-series Database Only (InfluxDB)

**Rejected:** Not suitable for relational data like users, permissions, configurations.

### All-MongoDB Solution

**Rejected:** MongoDB not optimal for structured relational data and complex joins needed for reporting.

## Implementation Notes

- Phase 1: JSON file exports (MVP)
- Phase 2: PostgreSQL + TimescaleDB
- Phase 3: Add MongoDB for scalability
- Use SQLAlchemy ORM for PostgreSQL
- Use PyMongo for MongoDB access

## Migration Path

1. Start with JSON file storage (Phase 1 - MVP)
2. Add PostgreSQL for metadata and core data
3. Add TimescaleDB extension for metrics
4. Add MongoDB when collector diversity requires flexibility

## References

- PLANNING.md - Data Storage section
- PRD.md - Non-functional requirements
