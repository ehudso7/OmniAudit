"""REST API validator."""

import re
from pathlib import Path
from typing import List

from ..types import Endpoint, HTTPMethod, RESTValidation


class RESTValidator:
    """Validate REST API implementations."""

    # Framework patterns
    FRAMEWORK_PATTERNS = {
        "express": {
            "route": r"(?:app|router)\.(get|post|put|patch|delete)\(['\"]([^'\"]+)['\"]",
            "auth": r"(?:authenticate|requireAuth|isAuthenticated)",
            "rate_limit": r"rateLimit|rateLimiter",
        },
        "fastapi": {
            "route": r"@(?:app|router)\.(get|post|put|patch|delete)\(['\"]([^'\"]+)['\"]",
            "auth": r"Depends\(.*(?:auth|get_current_user)",
            "rate_limit": r"@limiter\.limit",
        },
        "flask": {
            "route": r"@(?:app|bp)\.route\(['\"]([^'\"]+)['\"].*methods=\[([^\]]+)\]",
            "auth": r"@(?:login_required|auth_required|token_required)",
            "rate_limit": r"@limiter\.limit",
        },
    }

    @staticmethod
    def validate_file(file_path: Path) -> RESTValidation:
        """
        Validate REST API in file.

        Args:
            file_path: Path to API file

        Returns:
            REST validation results
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except (IOError, UnicodeDecodeError):
            return RESTValidation()

        endpoints = []
        versioning_detected = False
        versioning_strategy = None
        cors_configured = False
        https_enforced = False

        # Detect framework
        framework = RESTValidator._detect_framework(content)

        if framework:
            patterns = RESTValidator.FRAMEWORK_PATTERNS[framework]

            # Extract endpoints
            route_pattern = patterns["route"]
            auth_pattern = patterns["auth"]
            rate_limit_pattern = patterns["rate_limit"]

            # Find all route definitions
            for match in re.finditer(route_pattern, content, re.MULTILINE):
                if framework == "flask":
                    path = match.group(1)
                    methods_str = match.group(2)
                    methods = [
                        m.strip().strip("'\"")
                        for m in methods_str.split(",")
                    ]
                else:
                    method = match.group(1).upper()
                    path = match.group(2)
                    methods = [method]

                line_number = content[: match.start()].count("\n") + 1

                # Get context around the endpoint
                start_pos = max(0, match.start() - 500)
                end_pos = min(len(content), match.end() + 500)
                context = content[start_pos:end_pos]

                # Check for authentication
                has_auth = bool(re.search(auth_pattern, context, re.IGNORECASE))

                # Check for rate limiting
                has_rate_limiting = bool(
                    re.search(rate_limit_pattern, context, re.IGNORECASE)
                )

                # Check for validation (simplified)
                has_validation = bool(
                    re.search(
                        r"(?:validate|validator|schema|pydantic|joi)",
                        context,
                        re.IGNORECASE,
                    )
                )

                # Check for documentation
                has_documentation = bool(
                    re.search(r'""".*?"""', context, re.DOTALL)
                    or re.search(r"summary=|description=", context)
                )

                # Create endpoint for each method
                for method_str in methods:
                    try:
                        method = HTTPMethod(method_str)

                        endpoint = Endpoint(
                            path=path,
                            method=method,
                            file_path=str(file_path),
                            line_number=line_number,
                            has_auth=has_auth,
                            has_validation=has_validation,
                            has_rate_limiting=has_rate_limiting,
                            has_documentation=has_documentation,
                        )

                        # Check for security issues
                        if not has_auth and method != HTTPMethod.GET:
                            endpoint.security_issues.append("Missing authentication")

                        if not has_validation and method in [
                            HTTPMethod.POST,
                            HTTPMethod.PUT,
                            HTTPMethod.PATCH,
                        ]:
                            endpoint.security_issues.append("Missing input validation")

                        endpoints.append(endpoint)
                    except ValueError:
                        # Invalid HTTP method
                        pass

        # Check for versioning
        if re.search(r"/v\d+/|/api/v\d+/", content):
            versioning_detected = True
            versioning_strategy = "URL path versioning"
        elif re.search(r"version\s*=\s*['\"]v?\d+", content, re.IGNORECASE):
            versioning_detected = True
            versioning_strategy = "Header versioning"

        # Check for CORS configuration
        cors_configured = bool(
            re.search(r"cors|CORS|cross-origin", content, re.IGNORECASE)
        )

        # Check for HTTPS enforcement
        https_enforced = bool(
            re.search(
                r"ssl_context|SSLContext|force_ssl|require_https",
                content,
                re.IGNORECASE,
            )
        )

        # Calculate metrics
        total_endpoints = len(endpoints)
        documented = sum(1 for e in endpoints if e.has_documentation)
        authenticated = sum(1 for e in endpoints if e.has_auth)
        rate_limited = sum(1 for e in endpoints if e.has_rate_limiting)

        return RESTValidation(
            total_endpoints=total_endpoints,
            documented_endpoints=documented,
            authenticated_endpoints=authenticated,
            rate_limited_endpoints=rate_limited,
            endpoints=endpoints,
            versioning_detected=versioning_detected,
            versioning_strategy=versioning_strategy,
            cors_configured=cors_configured,
            https_enforced=https_enforced,
        )

    @staticmethod
    def _detect_framework(content: str) -> str:
        """Detect web framework used."""
        if re.search(r"from flask import|import flask", content):
            return "flask"
        elif re.search(r"from fastapi import|import fastapi", content):
            return "fastapi"
        elif re.search(r"express\(\)|require\(['\"]express['\"]", content):
            return "express"

        return None

    @staticmethod
    def validate_directory(directory: Path) -> RESTValidation:
        """
        Validate REST APIs in directory.

        Args:
            directory: Directory path

        Returns:
            Combined validation results
        """
        # Look for API files
        api_files = (
            list(directory.glob("**/routes/**/*.py"))
            + list(directory.glob("**/api/**/*.py"))
            + list(directory.glob("**/routes/**/*.js"))
            + list(directory.glob("**/api/**/*.js"))
            + list(directory.glob("**/routes/**/*.ts"))
            + list(directory.glob("**/api/**/*.ts"))
        )

        combined = RESTValidation()

        for api_file in api_files:
            if "node_modules" in str(api_file) or "test" in str(api_file).lower():
                continue

            validation = RESTValidator.validate_file(api_file)

            combined.total_endpoints += validation.total_endpoints
            combined.documented_endpoints += validation.documented_endpoints
            combined.authenticated_endpoints += validation.authenticated_endpoints
            combined.rate_limited_endpoints += validation.rate_limited_endpoints
            combined.endpoints.extend(validation.endpoints)

            if validation.versioning_detected:
                combined.versioning_detected = True
                combined.versioning_strategy = validation.versioning_strategy

            if validation.cors_configured:
                combined.cors_configured = True

            if validation.https_enforced:
                combined.https_enforced = True

        return combined
