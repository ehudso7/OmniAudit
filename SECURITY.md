# Security Policy

## Supported Versions

Currently supported versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.3.x   | :white_check_mark: |
| < 0.3   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please follow these steps:

### 1. **DO NOT** Open a Public Issue

Security vulnerabilities should not be publicly disclosed until they have been addressed.

### 2. Report Privately

Email security concerns to: **security@omniaudit.dev**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### 3. Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity
  - Critical: 1-7 days
  - High: 7-14 days
  - Medium: 14-30 days
  - Low: 30-90 days

### 4. Disclosure Process

1. Vulnerability reported privately
2. Team investigates and confirms
3. Fix is developed and tested
4. Security advisory is published
5. Fix is released
6. Public disclosure after users have time to update

## Security Best Practices

### API Keys

- **Never commit API keys** to version control
- Use environment variables for all secrets
- Rotate API keys regularly
- Use different keys for development and production

### Environment Variables

```bash
# ❌ BAD - Hardcoded in code
const apiKey = "sk-ant-api03-...";

# ✅ GOOD - From environment
const apiKey = process.env.ANTHROPIC_API_KEY;
```

### Input Validation

All user inputs are validated before processing:

```typescript
// Code analysis endpoint validates:
- Code length (max 100KB)
- Language is supported
- Skill IDs exist
- No malicious patterns
```

### Rate Limiting

**Planned Implementation:**
Rate limiting is planned for future releases:
- Target: 60 requests per minute per IP
- Target: 1000 requests per hour per API key
- Automatic blocking of abusive patterns

**Current Implementation:**
Basic rate limiting in development (100 requests per hour per client).

### CORS Configuration

CORS is configured in serverless functions:
```typescript
// Allow all origins in development, specific origins in production
res.setHeader('Access-Control-Allow-Origin', '*');
res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
```

### Data Privacy

- User code is **processed in-memory** and not persisted
- Analysis results may be cached temporarily (configurable TTL)
- All data encrypted in transit (TLS 1.3+)
- No personal data is collected without consent

### Dependencies

- Dependencies scanned with `npm audit`
- Security updates applied regularly
- Only use actively maintained dependencies

### Built-in Security Analyzers

OmniAudit includes security analysis features:

- **Static Analysis**: AST-based code scanning
- **SQL Injection detection**: Pattern matching for SQL vulnerabilities
- **XSS vulnerability scanning**: Detection of unsafe HTML/DOM manipulation
- **Insecure randomness detection**: Identifies weak RNG usage
- **Hardcoded secrets detection**: Finds exposed API keys and tokens
- **Dangerous function usage**: Flags eval(), Function(), and similar

### Execution Safety

**Current Implementation:**
- Skills execute via static AST analysis (no code execution)
- AI analysis performed via Anthropic Claude API
- Network isolation for analysis processes

**Planned Enhancements:**
- Sandboxed execution environment
- Resource limits (CPU/memory)
- Network request blocking for analyzed code
- File system access restrictions

## Vulnerability Disclosure History

No security vulnerabilities have been reported yet.

## Security Updates

Subscribe to security advisories:
- GitHub Security Advisories
- Email notifications (security@omniaudit.dev)
- RSS feed: https://omniaudit.dev/security.xml

## Contact

For security concerns: security@omniaudit.dev
For general questions: support@omniaudit.dev

## PGP Key

```
-----BEGIN PGP PUBLIC KEY BLOCK-----
[PGP key would go here in production]
-----END PGP PUBLIC KEY BLOCK-----
```

Thank you for helping keep OmniAudit secure!
