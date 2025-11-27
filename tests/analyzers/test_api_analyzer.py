"""Tests for APIAnalyzer."""

import pytest
from pathlib import Path
from omniaudit.analyzers.api import APIAnalyzer, APIType
from omniaudit.analyzers.api.validators import RESTValidator, GraphQLValidator, OpenAPIValidator
from omniaudit.analyzers.base import AnalyzerError


class TestAPIAnalyzer:
    """Test APIAnalyzer class."""

    def test_analyzer_properties(self, tmp_path):
        """Test analyzer properties."""
        config = {"project_path": str(tmp_path)}
        analyzer = APIAnalyzer(config)

        assert analyzer.name == "api_analyzer"
        assert analyzer.version == "1.0.0"

    def test_analyze_empty_project(self, tmp_path):
        """Test analysis of project without APIs."""
        config = {"project_path": str(tmp_path)}
        analyzer = APIAnalyzer(config)

        result = analyzer.analyze({})

        assert result["analyzer"] == "api_analyzer"
        metrics = result["data"]["metrics"]
        assert len(metrics["api_types_detected"]) == 0

    def test_detect_rest_api(self, tmp_path):
        """Test REST API detection."""
        api_dir = tmp_path / "api"
        api_dir.mkdir()

        api_file = api_dir / "routes.py"
        api_file.write_text('''
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
def get_users():
    return []
''')

        config = {"project_path": str(tmp_path)}
        analyzer = APIAnalyzer(config)

        result = analyzer.analyze({})
        metrics = result["data"]["metrics"]

        assert APIType.REST in metrics["api_types_detected"]

    def test_detect_graphql(self, tmp_path):
        """Test GraphQL detection."""
        schema_file = tmp_path / "schema.graphql"
        schema_file.write_text('''
type Query {
  users: [User]
}

type User {
  id: ID!
  name: String!
}
''')

        config = {"project_path": str(tmp_path)}
        analyzer = APIAnalyzer(config)

        result = analyzer.analyze({})
        metrics = result["data"]["metrics"]

        assert APIType.GRAPHQL in metrics["api_types_detected"]


class TestRESTValidator:
    """Test RESTValidator class."""

    def test_validate_fastapi_route(self, tmp_path):
        """Test validating FastAPI route."""
        api_file = tmp_path / "routes.py"
        api_file.write_text('''
from fastapi import FastAPI, Depends

app = FastAPI()

@app.get("/users")
async def get_users(current_user = Depends(get_current_user)):
    """Get all users."""
    return []

@app.post("/users")
async def create_user():
    return {}
''')

        validation = RESTValidator.validate_file(api_file)

        assert validation.total_endpoints == 2
        # GET endpoint should have auth
        assert validation.authenticated_endpoints > 0

    def test_validate_flask_route(self, tmp_path):
        """Test validating Flask route."""
        api_file = tmp_path / "routes.py"
        api_file.write_text('''
from flask import Flask
app = Flask(__name__)

@app.route("/api/users", methods=["GET", "POST"])
def users():
    """Get or create users."""
    return []
''')

        validation = RESTValidator.validate_file(api_file)

        assert validation.total_endpoints == 2  # GET and POST

    def test_detect_versioning(self, tmp_path):
        """Test API versioning detection."""
        api_file = tmp_path / "routes.py"
        api_file.write_text('''
@app.get("/api/v1/users")
def get_users():
    return []

@app.get("/api/v1/posts")
def get_posts():
    return []
''')

        validation = RESTValidator.validate_file(api_file)

        assert validation.versioning_detected is True
        assert "path" in validation.versioning_strategy.lower()


class TestGraphQLValidator:
    """Test GraphQLValidator class."""

    def test_validate_schema(self, tmp_path):
        """Test validating GraphQL schema."""
        schema_file = tmp_path / "schema.graphql"
        schema_file.write_text('''
type Query {
  users: [User] @authenticated
  posts: [Post]
}

type Mutation {
  createUser(name: String!): User @authenticated
}

type User {
  id: ID!
  name: String!
  email: String @deprecated
}
''')

        validation = GraphQLValidator.validate_schema(schema_file)

        assert validation.total_queries == 2
        assert validation.total_mutations == 1
        assert validation.has_auth_directives is True
        assert len(validation.deprecated_fields) > 0

    def test_find_schema_files(self, tmp_path):
        """Test finding GraphQL schema files."""
        schema_file = tmp_path / "schema.graphql"
        schema_file.write_text("type Query { test: String }")

        files = GraphQLValidator.find_schema_files(tmp_path)

        assert len(files) == 1
        assert files[0] == schema_file


class TestOpenAPIValidator:
    """Test OpenAPIValidator class."""

    def test_validate_openapi_spec(self, tmp_path):
        """Test validating OpenAPI specification."""
        spec_file = tmp_path / "openapi.json"
        spec_file.write_text('''{
  "openapi": "3.0.0",
  "paths": {
    "/users": {
      "get": {
        "summary": "Get users"
      },
      "post": {
        "requestBody": {
          "content": {
            "application/json": {}
          }
        }
      }
    }
  },
  "components": {
    "securitySchemes": {
      "bearerAuth": {
        "type": "http",
        "scheme": "bearer"
      }
    }
  }
}''')

        validation = OpenAPIValidator.validate_spec(spec_file)

        assert validation.version == "3.0.0"
        assert validation.total_paths == 1
        assert validation.total_operations == 2
        assert validation.has_security_schemes is True

    def test_find_missing_descriptions(self, tmp_path):
        """Test finding missing descriptions."""
        spec_file = tmp_path / "openapi.json"
        spec_file.write_text('''{
  "openapi": "3.0.0",
  "paths": {
    "/users": {
      "get": {}
    }
  }
}''')

        validation = OpenAPIValidator.validate_spec(spec_file)

        assert len(validation.missing_descriptions) > 0

    def test_find_spec_files(self, tmp_path):
        """Test finding OpenAPI spec files."""
        spec_file = tmp_path / "openapi.yaml"
        spec_file.write_text("openapi: 3.0.0")

        files = OpenAPIValidator.find_spec_files(tmp_path)

        assert len(files) == 1
        assert files[0] == spec_file
