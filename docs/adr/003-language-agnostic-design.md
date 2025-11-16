# ADR-003: Language-Agnostic Design

**Status:** Accepted
**Date:** 2025-10-05
**Deciders:** Core Team

## Context

OmniAudit must audit projects using various programming languages and tech stacks:

- Backend: Python, Node.js, Go, Java, Ruby, PHP
- Frontend: React, Vue, Angular, vanilla JS
- Mobile: Swift, Kotlin, React Native
- Infrastructure: Terraform, Kubernetes manifests

Requirements:

- Support any programming language
- Analyze projects regardless of tech stack
- Avoid language-specific assumptions
- Enable cross-language insights

## Decision

Design OmniAudit as a language-agnostic platform:

1. **Data Collection via Plugins**
   - Collectors work with language-neutral data sources (Git, CI/CD, APIs)
   - No source code parsing in core platform
   - Language-specific collectors as optional plugins

2. **Language-Specific Collectors** (Optional)
   - Python: AST analysis via `ast` module
   - JavaScript: Parse with Babel or ESLint
   - Go: Parse with `go/parser`
   - Deployable as separate containers/services

3. **Common Metrics Framework**
   - Universal metrics: commit frequency, team velocity, build success rate
   - Language-agnostic code quality: complexity, duplication, test coverage
   - Normalize metrics across languages for comparison

4. **Standard Data Format**
   - All collectors output standardized JSON format
   - Common fields: timestamp, source, metadata, data
   - Extensible schema for language-specific data

## Consequences

### Positive

- Works with any project regardless of language
- Easy to add new language support
- Core platform remains simple and maintainable
- Can compare metrics across different tech stacks
- No need to update core when new languages emerge

### Negative

- Language-specific insights require additional plugins
- May miss some language-specific best practices
- Each language analyzer needs separate development
- Generic analysis may be less deep than specialized tools

## Alternatives Considered

### Language-Specific Platform

**Rejected:** Would limit adoption to specific tech stacks. Would require separate tools for each language.

### Deep AST Analysis in Core

**Rejected:** Would make core complex and fragile. Would require expertise in all languages. Hard to maintain as languages evolve.

### Integration with Existing Tools

**Partially Accepted:** Integrate with existing language-specific tools (ESLint, Pylint, SonarQube) via collectors, but don't depend on them for core functionality.

## Implementation Notes

- Phase 1: Git collector (language-agnostic)
- Phase 2: CI/CD collectors (language-agnostic)
- Phase 3: Optional language-specific collectors
- Use subprocess calls to language-specific analyzers
- Standard format defined in `collectors/base.py`

## Universal Metrics

These metrics work across all languages:

- **Version Control**: Commit frequency, author activity, branch patterns
- **Build Health**: Success rate, build duration, failure patterns
- **Testing**: Test count, coverage trends (via CI/CD)
- **Deployment**: Deployment frequency, lead time, failure rate
- **Team**: Velocity, throughput, collaboration patterns

## Language-Specific Metrics

Optional collectors can provide:

- Code complexity (cyclomatic complexity)
- Dependency analysis
- Security vulnerabilities
- Style guide compliance
- Framework-specific patterns

## References

- PRD.md - Language support requirements
- PLANNING.md - Extensibility section
