"""API best practices analyzer."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import BaseAnalyzer, AnalyzerError
from .validators import GraphQLValidator, OpenAPIValidator, RESTValidator
from .types import APIFinding, APIMetrics, APIType, SecurityPattern

logger = logging.getLogger(__name__)

# Security limits for filesystem operations
MAX_FILES_TO_SCAN = 5000  # Maximum number of files to scan
MAX_DIRECTORY_DEPTH = 15  # Maximum directory depth to prevent traversal attacks


class APIAnalyzer(BaseAnalyzer):
    """
    Analyze API implementations for best practices and security.

    Supports:
    - REST API validation
    - GraphQL schema and resolver analysis
    - OpenAPI/Swagger specification validation
    - Security pattern detection (auth, rate limiting, etc.)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize API analyzer."""
        super().__init__(config)
        self.project_path = Path(self.config["project_path"])

    @property
    def name(self) -> str:
        """Return analyzer name."""
        return "api_analyzer"

    @property
    def version(self) -> str:
        """Return analyzer version."""
        return "1.0.0"

    def _validate_config(self) -> None:
        """Validate configuration."""
        if "project_path" not in self.config:
            raise AnalyzerError("project_path is required in configuration")

        path = Path(self.config["project_path"])
        if not path.exists():
            raise AnalyzerError(f"Project path {path} does not exist")

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze API implementation with comprehensive audit logging.

        Args:
            data: Input data (file patterns, exclusions, etc.)

        Returns:
            Analysis results with metrics and findings
        """
        import time

        start_time = time.time()

        # Log audit trail: Analysis started
        logger.info(
            "API analysis started",
            extra={
                "analyzer": self.name,
                "version": self.version,
                "project_path": str(self.project_path),
                "timestamp": time.time(),
            },
        )

        try:
            # Detect API types
            api_types = self._detect_api_types()

            # Log detected API types for audit trail
            logger.info(
                "API types detected",
                extra={
                    "api_types": [t.value for t in api_types],
                    "count": len(api_types),
                },
            )

            # Validate REST APIs
            rest_validation = None
            if APIType.REST in api_types:
                logger.debug("Validating REST APIs")
                rest_validation = RESTValidator.validate_directory(self.project_path)
                if rest_validation:
                    logger.info(
                        "REST validation complete",
                        extra={
                            "total_endpoints": rest_validation.total_endpoints,
                            "authenticated_endpoints": rest_validation.authenticated_endpoints,
                        },
                    )

            # Validate GraphQL
            graphql_validation = None
            if APIType.GRAPHQL in api_types:
                logger.debug("Validating GraphQL APIs")
                graphql_validation = GraphQLValidator.validate_directory(self.project_path)
                if graphql_validation:
                    logger.info(
                        "GraphQL validation complete",
                        extra={
                            "total_queries": graphql_validation.total_queries,
                            "total_mutations": graphql_validation.total_mutations,
                        },
                    )

            # Validate OpenAPI specs
            logger.debug("Validating OpenAPI specifications")
            openapi_spec = OpenAPIValidator.validate_directory(self.project_path)

            # Detect security patterns
            security_patterns = self._detect_security_patterns(rest_validation)

            # Log security findings for audit trail
            detected_patterns = [p.pattern_name for p in security_patterns if p.detected]
            missing_patterns = [p.pattern_name for p in security_patterns if not p.detected]

            logger.info(
                "Security pattern analysis complete",
                extra={
                    "detected_patterns": detected_patterns,
                    "missing_patterns": missing_patterns,
                },
            )

            # Calculate scores
            security_score = self._calculate_security_score(
                rest_validation, graphql_validation, security_patterns
            )
            best_practices_score = self._calculate_best_practices_score(
                rest_validation, graphql_validation, openapi_spec
            )
            overall_score = (security_score + best_practices_score) / 2

            # Count total endpoints
            total_endpoints = 0
            if rest_validation:
                total_endpoints += rest_validation.total_endpoints
            if graphql_validation:
                total_endpoints += graphql_validation.total_queries + graphql_validation.total_mutations

            metrics = APIMetrics(
                api_types_detected=api_types,
                rest_validation=rest_validation,
                graphql_validation=graphql_validation,
                openapi_spec=openapi_spec,
                security_patterns=security_patterns,
                total_endpoints=total_endpoints,
                security_score=security_score,
                best_practices_score=best_practices_score,
                overall_score=overall_score,
                files_analyzed=self._count_analyzed_files(),
            )

            findings = self._generate_findings(metrics)

            # Log audit trail: Analysis complete with results
            duration = time.time() - start_time
            logger.info(
                "API analysis completed successfully",
                extra={
                    "duration_seconds": round(duration, 2),
                    "total_endpoints": total_endpoints,
                    "security_score": round(security_score, 2),
                    "best_practices_score": round(best_practices_score, 2),
                    "overall_score": round(overall_score, 2),
                    "findings_count": len(findings),
                    "critical_findings": len([f for f in findings if f.severity == "critical"]),
                    "warning_findings": len([f for f in findings if f.severity == "warning"]),
                },
            )

            return self._create_response(
                {
                    "metrics": metrics.model_dump(),
                    "findings": [f.model_dump() for f in findings],
                    "summary": self._generate_summary(metrics),
                }
            )

        except Exception as e:
            # Log audit trail: Analysis failed
            duration = time.time() - start_time
            logger.error(
                "API analysis failed",
                extra={
                    "duration_seconds": round(duration, 2),
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
                exc_info=True,
            )
            raise

    def _detect_api_types(self) -> List[APIType]:
        """
        Detect API types used in project with security bounds.

        Returns:
            List of detected API types
        """
        api_types = []

        # Check for REST APIs (common route files)
        rest_indicators = [
            "**/routes/**/*.py",
            "**/routes/**/*.js",
            "**/routes/**/*.ts",
            "**/api/**/*.py",
            "**/api/**/*.js",
            "**/api/**/*.ts",
        ]

        for pattern in rest_indicators:
            # Use safe_glob with a small limit since we only need to know if files exist
            if self._safe_glob(pattern, max_results=1):
                api_types.append(APIType.REST)
                break

        # Check for GraphQL
        graphql_files = self._safe_glob("**/*.graphql", max_results=1)
        if not graphql_files:
            graphql_files = self._safe_glob("**/*.gql", max_results=1)
        if graphql_files:
            api_types.append(APIType.GRAPHQL)

        # Check for gRPC
        if self._safe_glob("**/*.proto", max_results=1):
            api_types.append(APIType.GRPC)

        # Check for WebSocket
        ws_files = self._safe_glob("**/websocket*.py", max_results=1)
        if not ws_files:
            ws_files = self._safe_glob("**/ws*.py", max_results=1)
        if ws_files:
            api_types.append(APIType.WEBSOCKET)

        logger.info(f"Detected API types: {[t.value for t in api_types]}")
        return api_types

    def _detect_security_patterns(
        self, rest_validation: Optional[RESTValidator]
    ) -> List[SecurityPattern]:
        """Detect security patterns in API implementation."""
        patterns = []

        # Authentication
        auth_pattern = SecurityPattern(
            pattern_name="Authentication",
            recommendation="Implement authentication for all non-public endpoints",
        )

        if rest_validation:
            if rest_validation.authenticated_endpoints > 0:
                auth_pattern.detected = True
                auth_percentage = (
                    rest_validation.authenticated_endpoints / rest_validation.total_endpoints * 100
                    if rest_validation.total_endpoints > 0
                    else 0
                )
                if auth_percentage < 80:
                    auth_pattern.recommendation = f"Only {auth_percentage:.1f}% of endpoints are authenticated"

        patterns.append(auth_pattern)

        # Rate Limiting
        rate_limit_pattern = SecurityPattern(
            pattern_name="Rate Limiting",
            recommendation="Implement rate limiting to prevent abuse",
        )

        if rest_validation and rest_validation.rate_limited_endpoints > 0:
            rate_limit_pattern.detected = True

        patterns.append(rate_limit_pattern)

        # CORS Configuration
        cors_pattern = SecurityPattern(
            pattern_name="CORS Configuration",
            recommendation="Configure CORS properly to prevent unauthorized access",
        )

        if rest_validation and rest_validation.cors_configured:
            cors_pattern.detected = True

        patterns.append(cors_pattern)

        # HTTPS Enforcement
        https_pattern = SecurityPattern(
            pattern_name="HTTPS Enforcement",
            recommendation="Enforce HTTPS for all API endpoints",
        )

        if rest_validation and rest_validation.https_enforced:
            https_pattern.detected = True

        patterns.append(https_pattern)

        # Input Validation
        validation_pattern = SecurityPattern(
            pattern_name="Input Validation",
            recommendation="Validate all input data to prevent injection attacks",
        )

        if rest_validation:
            validated_count = sum(1 for e in rest_validation.endpoints if e.has_validation)
            if validated_count > 0:
                validation_pattern.detected = True

        patterns.append(validation_pattern)

        return patterns

    def _calculate_security_score(
        self, rest_validation, graphql_validation, security_patterns
    ) -> float:
        """Calculate security score (0-100)."""
        score = 0.0
        weight_sum = 0.0

        # REST security (40%)
        if rest_validation and rest_validation.total_endpoints > 0:
            auth_percentage = (
                rest_validation.authenticated_endpoints / rest_validation.total_endpoints * 100
            )
            rate_limit_percentage = (
                rest_validation.rate_limited_endpoints / rest_validation.total_endpoints * 100
            )

            rest_score = (auth_percentage * 0.6 + rate_limit_percentage * 0.4)
            score += rest_score * 0.4
            weight_sum += 0.4

        # GraphQL security (30%)
        if graphql_validation:
            graphql_score = 0
            if graphql_validation.has_auth_directives:
                graphql_score += 40
            if graphql_validation.has_depth_limiting:
                graphql_score += 30
            if graphql_validation.has_complexity_analysis:
                graphql_score += 30

            score += graphql_score * 0.3
            weight_sum += 0.3

        # Security patterns (30%)
        detected_patterns = sum(1 for p in security_patterns if p.detected)
        pattern_score = (detected_patterns / len(security_patterns) * 100) if security_patterns else 0
        score += pattern_score * 0.3
        weight_sum += 0.3

        return round(score / weight_sum if weight_sum > 0 else 0, 2)

    def _calculate_best_practices_score(
        self, rest_validation, graphql_validation, openapi_spec
    ) -> float:
        """Calculate best practices score (0-100)."""
        score = 0.0
        components = 0

        # Documentation score
        if rest_validation and rest_validation.total_endpoints > 0:
            doc_percentage = (
                rest_validation.documented_endpoints / rest_validation.total_endpoints * 100
            )
            score += doc_percentage
            components += 1

        # Versioning
        if rest_validation and rest_validation.versioning_detected:
            score += 100
            components += 1
        elif rest_validation:
            components += 1

        # OpenAPI spec
        if openapi_spec:
            spec_score = 100
            # Deduct for missing descriptions
            if openapi_spec.missing_descriptions:
                spec_score -= min(30, len(openapi_spec.missing_descriptions) * 2)
            # Deduct for missing examples
            if openapi_spec.missing_examples:
                spec_score -= min(20, len(openapi_spec.missing_examples))

            score += max(0, spec_score)
            components += 1

        return round(score / components if components > 0 else 0, 2)

    def _generate_findings(self, metrics: APIMetrics) -> List[APIFinding]:
        """Generate findings from metrics."""
        findings = []

        # REST findings
        if metrics.rest_validation:
            rest = metrics.rest_validation

            # Authentication
            if rest.total_endpoints > 0:
                auth_percentage = rest.authenticated_endpoints / rest.total_endpoints * 100

                if auth_percentage < 50:
                    findings.append(
                        APIFinding(
                            severity="critical",
                            category="security",
                            message=f"Only {auth_percentage:.1f}% of endpoints have authentication",
                            suggestion="Add authentication to all non-public endpoints",
                        )
                    )
                elif auth_percentage < 80:
                    findings.append(
                        APIFinding(
                            severity="warning",
                            category="security",
                            message=f"{auth_percentage:.1f}% of endpoints have authentication",
                            suggestion="Ensure all sensitive endpoints require authentication",
                        )
                    )

            # Rate limiting
            if rest.rate_limited_endpoints == 0:
                findings.append(
                    APIFinding(
                        severity="warning",
                        category="security",
                        message="No rate limiting detected on API endpoints",
                        suggestion="Implement rate limiting to prevent abuse and DDoS attacks",
                    )
                )

            # Documentation
            if rest.total_endpoints > 0:
                doc_percentage = rest.documented_endpoints / rest.total_endpoints * 100
                if doc_percentage < 50:
                    findings.append(
                        APIFinding(
                            severity="warning",
                            category="documentation",
                            message=f"Only {doc_percentage:.1f}% of endpoints are documented",
                            suggestion="Add documentation to all API endpoints",
                        )
                    )

            # Versioning
            if not rest.versioning_detected:
                findings.append(
                    APIFinding(
                        severity="info",
                        category="versioning",
                        message="API versioning not detected",
                        suggestion="Implement API versioning to manage breaking changes",
                    )
                )

            # HTTPS
            if not rest.https_enforced:
                findings.append(
                    APIFinding(
                        severity="warning",
                        category="security",
                        message="HTTPS enforcement not detected",
                        suggestion="Enforce HTTPS for all API traffic",
                    )
                )

        # GraphQL findings
        if metrics.graphql_validation:
            gql = metrics.graphql_validation

            if not gql.has_auth_directives:
                findings.append(
                    APIFinding(
                        severity="warning",
                        category="security",
                        message="GraphQL schema missing authentication directives",
                        suggestion="Add @auth or similar directives to protect queries/mutations",
                    )
                )

            if not gql.has_depth_limiting:
                findings.append(
                    APIFinding(
                        severity="warning",
                        category="security",
                        message="GraphQL missing query depth limiting",
                        suggestion="Implement depth limiting to prevent deep nested queries",
                    )
                )

            if not gql.has_complexity_analysis:
                findings.append(
                    APIFinding(
                        severity="info",
                        category="best_practice",
                        message="GraphQL missing complexity analysis",
                        suggestion="Add query complexity analysis to prevent expensive queries",
                    )
                )

        # OpenAPI spec findings
        if metrics.openapi_spec:
            if not metrics.openapi_spec.has_security_schemes:
                findings.append(
                    APIFinding(
                        severity="warning",
                        category="security",
                        message="OpenAPI spec missing security schemes definition",
                        suggestion="Define security schemes in OpenAPI specification",
                    )
                )

            if metrics.openapi_spec.missing_descriptions:
                findings.append(
                    APIFinding(
                        severity="info",
                        category="documentation",
                        message=f"{len(metrics.openapi_spec.missing_descriptions)} endpoints missing descriptions",
                        suggestion="Add descriptions to all API operations in OpenAPI spec",
                    )
                )

        # No API detected
        if not metrics.api_types_detected:
            findings.append(
                APIFinding(
                    severity="info",
                    category="best_practice",
                    message="No API implementation detected",
                    suggestion="Implement RESTful or GraphQL API with proper documentation",
                )
            )

        return findings

    def _generate_summary(self, metrics: APIMetrics) -> str:
        """Generate summary text."""
        if not metrics.api_types_detected:
            return "No API implementation detected in project."

        api_types = ", ".join([t.value.upper() for t in metrics.api_types_detected])
        return (
            f"API Analysis: Overall Score {metrics.overall_score:.1f}/100. "
            f"Detected: {api_types}. "
            f"Security Score: {metrics.security_score:.1f}, "
            f"Best Practices: {metrics.best_practices_score:.1f}. "
            f"Total Endpoints: {metrics.total_endpoints}."
        )

    def _safe_glob(self, pattern: str, max_results: int = MAX_FILES_TO_SCAN) -> List[Path]:
        """
        Safely glob files with bounds to prevent resource exhaustion.

        Args:
            pattern: Glob pattern
            max_results: Maximum number of results to return

        Returns:
            List of matching file paths (bounded)
        """
        try:
            files = []
            excluded_dirs = {"node_modules", "vendor", ".git", "dist", "build", "__pycache__"}

            for file_path in self.project_path.glob(pattern):
                # Check if we've hit the limit
                if len(files) >= max_results:
                    logger.warning(
                        f"Reached file scan limit ({max_results}) for pattern {pattern}"
                    )
                    break

                # Validate path depth to prevent deep directory traversal
                try:
                    relative_path = file_path.relative_to(self.project_path)
                    depth = len(relative_path.parts)

                    if depth > MAX_DIRECTORY_DEPTH:
                        logger.debug(f"Skipping file due to excessive depth: {file_path}")
                        continue
                except ValueError:
                    # Path is outside project root - skip it
                    logger.warning(f"Skipping file outside project root: {file_path}")
                    continue

                # Exclude common third-party and generated directories
                path_str = str(file_path)
                if any(excluded_dir in path_str for excluded_dir in excluded_dirs):
                    continue

                # Exclude test files
                if "test" in path_str.lower():
                    continue

                files.append(file_path)

            return files

        except Exception as e:
            logger.error(f"Error during glob operation for pattern {pattern}: {e}")
            return []

    def _count_analyzed_files(self) -> int:
        """
        Count total files analyzed with security bounds.

        Returns:
            Number of files that will be analyzed
        """
        patterns = [
            "**/routes/**/*.py",
            "**/routes/**/*.js",
            "**/routes/**/*.ts",
            "**/api/**/*.py",
            "**/api/**/*.js",
            "**/api/**/*.ts",
            "**/*.graphql",
            "**/*.gql",
        ]

        total = 0
        for pattern in patterns:
            files = self._safe_glob(pattern, max_results=MAX_FILES_TO_SCAN - total)
            total += len(files)

            # Stop if we've reached the global limit
            if total >= MAX_FILES_TO_SCAN:
                logger.warning(
                    f"Reached maximum file scan limit ({MAX_FILES_TO_SCAN}). "
                    "Some files may not be analyzed."
                )
                break

        logger.info(f"Will analyze {total} API-related files")
        return total
