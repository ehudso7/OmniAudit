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

API endpoints are rate-limited:
- 60 requests per minute per IP
- 1000 requests per hour per API key
- Automatic blocking of abusive patterns

### CORS Configuration

Strict CORS policy:
```typescript
// Only specific origins allowed
allowedOrigins: [
  'https://omniaudit.dev',
  'https://app.omniaudit.dev'
]
```

### Data Privacy

- User code is **never stored** permanently
- Analysis results cached for 1 hour only
- All data encrypted in transit (TLS 1.3)
- Database encrypted at rest

### Dependencies

- Dependencies scanned daily with `npm audit`
- Automated updates for security patches
- Only use dependencies with active maintenance

## Security Features

### Built-in Security Analyzers

OmniAudit includes security analysis:

- SQL Injection detection
- XSS vulnerability scanning
- CSRF protection validation
- Insecure randomness detection
- Hardcoded secrets detection
- Dangerous function usage

### Secure Defaults

- All skills run in sandboxed environment
- No file system access from analyzed code
- Network requests blocked during analysis
- CPU and memory limits enforced

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
