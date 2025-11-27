"""OpenAPI/Swagger validator."""

import json
from pathlib import Path
from typing import List, Optional

try:
    import yaml
except ImportError:
    yaml = None

from ..types import OpenAPISpec


class OpenAPIValidator:
    """Validate OpenAPI/Swagger specifications."""

    @staticmethod
    def validate_spec(file_path: Path) -> OpenAPISpec:
        """
        Validate OpenAPI specification file.

        Args:
            file_path: Path to OpenAPI spec file

        Returns:
            OpenAPI spec analysis
        """
        try:
            content = file_path.read_text(encoding="utf-8")

            # Parse YAML or JSON
            if file_path.suffix in [".yaml", ".yml"]:
                if yaml is None:
                    return OpenAPISpec(spec_file=str(file_path))
                spec = yaml.safe_load(content)
            else:
                spec = json.loads(content)

        except (IOError, yaml.YAMLError if yaml else Exception, json.JSONDecodeError, UnicodeDecodeError):
            return OpenAPISpec(spec_file=str(file_path))

        # Extract version
        version = spec.get("openapi") or spec.get("swagger")

        # Count paths and operations
        paths = spec.get("paths", {})
        total_paths = len(paths)
        total_operations = sum(
            len([k for k in path_spec.keys() if k in ["get", "post", "put", "patch", "delete"]])
            for path_spec in paths.values()
        )

        # Check for security schemes
        has_security_schemes = bool(
            spec.get("securityDefinitions") or spec.get("components", {}).get("securitySchemes")
        )

        # Find missing descriptions
        missing_descriptions = []
        for path, path_spec in paths.items():
            for method, operation in path_spec.items():
                if method not in ["get", "post", "put", "patch", "delete"]:
                    continue

                if not isinstance(operation, dict):
                    continue

                if "description" not in operation and "summary" not in operation:
                    missing_descriptions.append(f"{method.upper()} {path}")

        # Find missing examples
        missing_examples = []
        for path, path_spec in paths.items():
            for method, operation in path_spec.items():
                if method not in ["get", "post", "put", "patch", "delete"]:
                    continue

                if not isinstance(operation, dict):
                    continue

                # Check request body examples
                request_body = operation.get("requestBody", {})
                if request_body:
                    content = request_body.get("content", {})
                    for media_type, media_spec in content.items():
                        if "example" not in media_spec and "examples" not in media_spec:
                            missing_examples.append(f"{method.upper()} {path} request")

                # Check response examples
                responses = operation.get("responses", {})
                for status, response_spec in responses.items():
                    if not isinstance(response_spec, dict):
                        continue

                    content = response_spec.get("content", {})
                    for media_type, media_spec in content.items():
                        if "example" not in media_spec and "examples" not in media_spec:
                            missing_examples.append(f"{method.upper()} {path} response {status}")

        return OpenAPISpec(
            spec_file=str(file_path),
            version=version,
            total_paths=total_paths,
            total_operations=total_operations,
            has_security_schemes=has_security_schemes,
            missing_descriptions=missing_descriptions[:20],  # Limit to 20
            missing_examples=missing_examples[:20],
        )

    @staticmethod
    def find_spec_files(directory: Path) -> List[Path]:
        """
        Find OpenAPI spec files in directory.

        Args:
            directory: Directory path

        Returns:
            List of spec file paths
        """
        spec_files = []

        # Common OpenAPI file names
        patterns = [
            "**/openapi.yaml",
            "**/openapi.yml",
            "**/openapi.json",
            "**/swagger.yaml",
            "**/swagger.yml",
            "**/swagger.json",
            "**/api-spec.yaml",
            "**/api-spec.yml",
        ]

        for pattern in patterns:
            spec_files.extend(directory.glob(pattern))

        # Filter out node_modules
        spec_files = [f for f in spec_files if "node_modules" not in str(f)]

        return spec_files

    @staticmethod
    def validate_directory(directory: Path) -> Optional[OpenAPISpec]:
        """
        Validate OpenAPI specs in directory.

        Args:
            directory: Directory path

        Returns:
            Spec validation or None if no spec found
        """
        spec_files = OpenAPIValidator.find_spec_files(directory)

        if not spec_files:
            return None

        # Validate the first spec file found
        return OpenAPIValidator.validate_spec(spec_files[0])
