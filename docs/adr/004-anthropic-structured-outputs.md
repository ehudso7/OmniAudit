# ADR-004: Anthropic Structured Outputs for AI-Enhanced Features

**Status:** Accepted
**Date:** 2025-11-16
**Deciders:** Core Team

## Context

OmniAudit's roadmap includes AI-powered features for:
- Code quality insights and recommendations
- Anomaly detection in metrics
- Natural language query interface
- Automated root cause analysis
- Executive summary generation

Traditional LLM integrations face reliability challenges:
- Inconsistent response formats requiring retry logic
- JSON parsing errors from malformed outputs
- Type safety issues when integrating with statically-typed code
- Complex validation logic for every AI response

Anthropic released Structured Outputs (public beta as of November 14, 2025), which guarantees schema-compliant JSON responses through constrained decoding.

## Decision

Adopt Anthropic's Structured Outputs feature as the foundation for all AI-enhanced features in OmniAudit.

**Implementation approach:**

1. **Use Pydantic models** to define all AI output schemas (already aligned with our FastAPI stack)
2. **Two integration modes:**
   - `output_format` for data extraction and analysis
   - `strict: true` for agentic workflows and tool use
3. **Progressive rollout:**
   - Phase 0: Add anthropic SDK dependency, design model hierarchy
   - Phase 1: Implement basic AI features (report summarization, config validation)
   - Phase 2: Add natural language queries and anomaly detection
   - Phase 3: Full AI insights integration with root cause analysis

## Consequences

### Positive

- **Elimination of retry logic** - Guaranteed schema compliance means no parsing errors
- **Type safety** - Pydantic models provide compile-time and runtime type checking
- **Consistent data contracts** - AI and non-AI components share the same schemas
- **Production reliability** - No malformed JSON responses in production
- **Developer experience** - Clear type hints and autocomplete for AI responses
- **Aligned with existing stack** - We already use Pydantic extensively with FastAPI
- **Future-proof** - As Anthropic improves the feature, we automatically benefit

### Negative

- **Public beta risk** - May have breaking changes before stable release
- **Schema complexity limits** - Very complex nested schemas may not be supported
- **Token overhead** - Small additional cost for injected system prompt (~100 tokens)
- **First-request latency** - Initial schema compilation adds ~1-2s (cached for 24h)
- **Vendor lock-in** - Tight coupling to Anthropic's API (mitigated by abstraction layer)
- **Cost** - Claude API usage costs (mitigated by batch processing discounts)

## Alternatives Considered

### OpenAI Function Calling
**Rejected:** Less reliable schema compliance, requires manual validation, doesn't guarantee JSON structure.

### JSON Schema + Prompt Engineering
**Rejected:** Unreliable, requires extensive retry logic, increases latency, complex error handling.

### Custom Fine-Tuned Models
**Rejected:** Expensive to train and maintain, requires large datasets, long iteration cycles, doesn't solve JSON parsing issues.

### Rule-Based Systems
**Rejected:** Cannot handle nuanced code analysis, requires extensive manual rules, not scalable across languages.

## Implementation Strategy

### Phase 0: Foundation (Current)

```python
# Add to pyproject.toml
dependencies = [
    # ... existing
    "anthropic>=0.39.0",  # Structured Outputs support
]

# Define base models in src/omniaudit/models/ai_models.py
from pydantic import BaseModel, Field
from typing import List

class CodeSmell(BaseModel):
    """Structured output for code quality issues."""
    file_path: str
    line_number: int
    severity: str  # "critical", "high", "medium", "low"
    smell_type: str
    description: str
    recommendation: str
```

### Phase 1: Basic AI Features

- Report summarization endpoint
- Configuration validation assistance
- Trend analysis with natural language explanations

### Phase 2: Advanced Analysis

- Natural language query interface for audit data
- Anomaly detection with structured alerts
- Intelligent project setup wizard

### Phase 3: Full AI Insights

- Root cause analysis for failures
- Predictive analytics for quality trends
- AI-powered code review recommendations
- Business impact correlation analysis

## Performance Considerations

**Cache warming strategy:**
```python
# Pre-warm common schemas during app startup
@app.on_event("startup")
async def warm_ai_schemas():
    """Pre-compile frequently used schemas to reduce first-request latency."""
    from omniaudit.models.ai_models import (
        AIInsightsResult,
        AnomalyReport,
        ExecutiveSummary
    )
    # Schemas are compiled and cached for 24h
```

**Batch processing for cost optimization:**
- Use Claude batch API (50% discount) for non-real-time analysis
- Process multiple files/repos in single batch job
- Schedule during off-peak hours

**Rate limiting:**
- Implement exponential backoff for API errors
- Cache AI results with Redis (configurable TTL)
- Provide fallback to rule-based analysis when AI unavailable

## Security and Privacy

- **API key management:** Store in environment variables, never commit to repo
- **Data privacy:** Sanitize sensitive data before sending to API (PII, credentials)
- **Audit logging:** Log all AI interactions for compliance
- **Cost controls:** Set monthly budget limits and rate limits

## Migration Path

1. **No breaking changes** - AI features are additive, existing functionality unchanged
2. **Feature flags** - AI features can be disabled via configuration
3. **Gradual rollout** - Enable AI features per-user or per-project
4. **Fallback modes** - Graceful degradation when AI unavailable

## Success Metrics

- **Reliability:** 99.9% schema compliance rate (validated in tests)
- **Performance:** <3s p95 latency for AI-enhanced endpoints
- **Quality:** User satisfaction score >4.5/5 for AI insights
- **Adoption:** >50% of users enable AI features within 3 months
- **Cost:** <$0.10 per audit with AI features enabled

## References

- [Anthropic Structured Outputs Documentation](https://docs.anthropic.com/en/docs/build-with-claude/structured-outputs)
- [Pydantic Models](https://docs.pydantic.dev/latest/)
- OmniAudit PRD Phase 3: AI-Powered Insights
- ADR-001: Plugin Architecture (complementary design)

## Review Schedule

- **3 months:** Evaluate beta stability and breaking changes
- **6 months:** Assess cost vs. value, consider alternative providers
- **12 months:** Decide on continued investment or pivot to alternatives
