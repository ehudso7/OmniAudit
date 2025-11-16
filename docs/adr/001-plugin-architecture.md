# ADR-001: Plugin Architecture

**Status:** Accepted
**Date:** 2025-10-05
**Deciders:** Core Team

## Context

OmniAudit needs to support multiple data sources (Git, CI/CD, logs, databases, APIs) and analysis methods. We need an architecture that allows:

- Independent development of collectors and analyzers
- Easy addition of new data sources without modifying core
- Community contributions
- Version management and compatibility

## Decision

Implement a plugin-based architecture where:

1. All collectors, analyzers, and reporters inherit from base interfaces
2. Plugins are discovered dynamically at runtime
3. Each plugin declares its dependencies and configuration schema
4. Core engine manages plugin lifecycle (load, validate, execute, unload)

## Consequences

### Positive

- Easy to add new features without touching core
- Parallel development by multiple teams
- Clear separation of concerns
- Community can contribute plugins
- Plugins can be versioned independently

### Negative

- Overhead of plugin management system
- Need to maintain backward compatibility
- Version conflicts between plugins
- More complex testing (need to test plugin interactions)

## Alternatives Considered

### Monolithic Architecture

**Rejected:** All features in one codebase. Simple initially but becomes unmaintainable as features grow. Hard to add new data sources.

### Microservices

**Deferred:** Each collector/analyzer as separate service. Over-engineering for MVP. Consider for Phase 3 (enterprise scale).

## Implementation Notes

- Base interfaces defined in `src/omniaudit/collectors/base.py`
- Plugin discovery via Python entry points (Phase 2)
- Configuration schemas using JSON Schema
- Dependency injection for plugin context

## References

- PLANNING.md - Architecture section
- src/omniaudit/collectors/base.py - Base interface
