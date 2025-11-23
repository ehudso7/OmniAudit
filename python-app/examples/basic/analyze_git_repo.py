#!/usr/bin/env python3
"""
Example: Analyze a Git repository

This example demonstrates how to use the GitCollector to analyze
a Git repository and display basic statistics.
"""

import sys
import json
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from omniaudit.collectors.git_collector import GitCollector


def main():
    """Run Git analysis example."""
    # Get repository path from command line or use current directory
    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."

    print(f"Analyzing Git repository: {repo_path}\n")

    # Configure collector
    config = {
        "repo_path": repo_path,
        "max_commits": 100  # Limit for demo
    }

    # Create and run collector
    try:
        collector = GitCollector(config)
        result = collector.collect()

        # Display results
        data = result["data"]
        print("=" * 60)
        print("GIT REPOSITORY ANALYSIS")
        print("=" * 60)
        print(f"Repository: {data['repository_path']}")
        print(f"Current Branch: {data['current_branch']}")
        print(f"\nCommits Analyzed: {data['commits_count']}")
        print(f"Total Branches: {data['branches_count']}")
        print(f"Contributors: {data['contributors_count']}")

        # Show top contributors
        print("\n" + "=" * 60)
        print("TOP CONTRIBUTORS")
        print("=" * 60)
        for i, contributor in enumerate(data['contributors'][:5], 1):
            print(f"{i}. {contributor['name']}")
            print(f"   Commits: {contributor['commits']}")
            print(f"   Lines Changed: {contributor['lines_changed']}")
            print()

        # Save full results
        output_file = "git_analysis.json"
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Full results saved to: {output_file}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
