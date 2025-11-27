"""GraphQL API validator."""

import re
from pathlib import Path
from typing import List, Optional

from ..types import GraphQLValidation


class GraphQLValidator:
    """Validate GraphQL API implementations."""

    @staticmethod
    def validate_schema(file_path: Path) -> GraphQLValidation:
        """
        Validate GraphQL schema file.

        Args:
            file_path: Path to GraphQL schema file

        Returns:
            GraphQL validation results
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except (IOError, UnicodeDecodeError):
            return GraphQLValidation()

        # Count types
        type_pattern = re.compile(r"type\s+(\w+)", re.MULTILINE)
        types = type_pattern.findall(content)
        total_types = len([t for t in types if t not in ["Query", "Mutation", "Subscription"]])

        # Count queries
        query_pattern = re.compile(r"type Query\s*\{([^}]*)\}", re.DOTALL)
        query_match = query_pattern.search(content)
        queries = []
        if query_match:
            query_content = query_match.group(1)
            queries = re.findall(r"(\w+)\s*(?:\([^)]*\))?\s*:", query_content)
        total_queries = len(queries)

        # Count mutations
        mutation_pattern = re.compile(r"type Mutation\s*\{([^}]*)\}", re.DOTALL)
        mutation_match = mutation_pattern.search(content)
        mutations = []
        if mutation_match:
            mutation_content = mutation_match.group(1)
            mutations = re.findall(r"(\w+)\s*(?:\([^)]*\))?\s*:", mutation_content)
        total_mutations = len(mutations)

        # Check for auth directives
        has_auth_directives = bool(
            re.search(r"@auth|@authenticated|@requireAuth|@isAuthenticated", content)
        )

        # Check for depth limiting (in code, not schema)
        has_depth_limiting = False  # Would need to check resolver code

        # Check for complexity analysis
        has_complexity_analysis = bool(
            re.search(r"@complexity|complexity\s*:", content)
        )

        # Find deprecated fields
        deprecated_pattern = re.compile(r"(\w+)[^@]*@deprecated", re.MULTILINE)
        deprecated_fields = deprecated_pattern.findall(content)

        return GraphQLValidation(
            schema_file=str(file_path),
            total_types=total_types,
            total_queries=total_queries,
            total_mutations=total_mutations,
            has_auth_directives=has_auth_directives,
            has_depth_limiting=has_depth_limiting,
            has_complexity_analysis=has_complexity_analysis,
            deprecated_fields=deprecated_fields,
        )

    @staticmethod
    def validate_resolvers(file_path: Path) -> dict:
        """
        Validate GraphQL resolver implementations.

        Args:
            file_path: Path to resolver file

        Returns:
            Resolver validation results
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except (IOError, UnicodeDecodeError):
            return {}

        # Check for depth limiting
        has_depth_limiting = bool(
            re.search(
                r"depthLimit|queryDepth|depth.*limit",
                content,
                re.IGNORECASE,
            )
        )

        # Check for complexity analysis
        has_complexity = bool(
            re.search(
                r"queryComplexity|complexityLimit|cost.*analysis",
                content,
                re.IGNORECASE,
            )
        )

        # Check for error handling
        has_error_handling = bool(
            re.search(r"try\s*\{|catch|formatError", content, re.IGNORECASE)
        )

        return {
            "has_depth_limiting": has_depth_limiting,
            "has_complexity": has_complexity,
            "has_error_handling": has_error_handling,
        }

    @staticmethod
    def find_schema_files(directory: Path) -> List[Path]:
        """
        Find GraphQL schema files in directory.

        Args:
            directory: Directory path

        Returns:
            List of schema file paths
        """
        schema_files = []

        # Look for .graphql files
        schema_files.extend(directory.glob("**/*.graphql"))
        schema_files.extend(directory.glob("**/*.gql"))

        # Filter out node_modules
        schema_files = [
            f for f in schema_files if "node_modules" not in str(f)
        ]

        return schema_files

    @staticmethod
    def validate_directory(directory: Path) -> Optional[GraphQLValidation]:
        """
        Validate GraphQL in directory.

        Args:
            directory: Directory path

        Returns:
            Combined validation results or None if no GraphQL found
        """
        schema_files = GraphQLValidator.find_schema_files(directory)

        if not schema_files:
            return None

        # Use the first schema file (or combine multiple)
        validation = GraphQLValidator.validate_schema(schema_files[0])

        # Check resolver files for additional validations
        resolver_files = (
            list(directory.glob("**/resolvers/**/*.js"))
            + list(directory.glob("**/resolvers/**/*.ts"))
            + list(directory.glob("**/resolvers/**/*.py"))
        )

        for resolver_file in resolver_files:
            if "node_modules" in str(resolver_file):
                continue

            resolver_info = GraphQLValidator.validate_resolvers(resolver_file)

            if resolver_info.get("has_depth_limiting"):
                validation.has_depth_limiting = True
            if resolver_info.get("has_complexity"):
                validation.has_complexity_analysis = True

        return validation
