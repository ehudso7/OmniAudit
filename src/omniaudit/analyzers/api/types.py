"""Type definitions for API analyzer."""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class APIType(str, Enum):
    """API types."""

    REST = "rest"
    GRAPHQL = "graphql"
    GRPC = "grpc"
    WEBSOCKET = "websocket"


class HTTPMethod(str, Enum):
    """HTTP methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class Endpoint(BaseModel):
    """API endpoint information."""

    path: str
    method: HTTPMethod
    file_path: str
    line_number: int
    has_auth: bool = False
    has_validation: bool = False
    has_rate_limiting: bool = False
    has_documentation: bool = False
    security_issues: List[str] = Field(default_factory=list)


class RESTValidation(BaseModel):
    """REST API validation results."""

    total_endpoints: int = 0
    documented_endpoints: int = 0
    authenticated_endpoints: int = 0
    rate_limited_endpoints: int = 0
    endpoints: List[Endpoint] = Field(default_factory=list)
    versioning_detected: bool = False
    versioning_strategy: Optional[str] = None
    cors_configured: bool = False
    https_enforced: bool = False


class GraphQLValidation(BaseModel):
    """GraphQL API validation results."""

    schema_file: Optional[str] = None
    total_types: int = 0
    total_queries: int = 0
    total_mutations: int = 0
    has_auth_directives: bool = False
    has_depth_limiting: bool = False
    has_complexity_analysis: bool = False
    deprecated_fields: List[str] = Field(default_factory=list)


class OpenAPISpec(BaseModel):
    """OpenAPI/Swagger specification analysis."""

    spec_file: Optional[str] = None
    version: Optional[str] = None
    total_paths: int = 0
    total_operations: int = 0
    has_security_schemes: bool = False
    missing_descriptions: List[str] = Field(default_factory=list)
    missing_examples: List[str] = Field(default_factory=list)


class SecurityPattern(BaseModel):
    """API security pattern detection."""

    pattern_name: str
    detected: bool = False
    file_path: Optional[str] = None
    recommendation: Optional[str] = None


class APIMetrics(BaseModel):
    """Overall API metrics."""

    api_types_detected: List[APIType] = Field(default_factory=list)
    rest_validation: Optional[RESTValidation] = None
    graphql_validation: Optional[GraphQLValidation] = None
    openapi_spec: Optional[OpenAPISpec] = None
    security_patterns: List[SecurityPattern] = Field(default_factory=list)
    total_endpoints: int = 0
    security_score: float = 0.0
    best_practices_score: float = 0.0
    overall_score: float = 0.0
    files_analyzed: int = 0


class APIFinding(BaseModel):
    """Individual API finding."""

    severity: str = Field(description="critical, warning, or info")
    category: str = Field(
        description="security, documentation, versioning, or best_practice"
    )
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    endpoint: Optional[str] = None
    suggestion: Optional[str] = None
