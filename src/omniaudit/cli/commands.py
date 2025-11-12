"""
CLI Commands

Comprehensive command-line interface for OmniAudit.
"""

import click
import json
import sys
from pathlib import Path
from typing import Optional

from ..collectors.git_collector import GitCollector
from ..collectors.github_collector import GitHubCollector
from ..analyzers.code_quality import CodeQualityAnalyzer
from ..utils.logger import get_logger

logger = get_logger(__name__)


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """OmniAudit - Universal Project Auditing & Monitoring Platform"""
    pass


@cli.command()
@click.option('--repo-path', '-r', default='.',
              help='Path to Git repository')
@click.option('--max-commits', '-m', default=1000,
              help='Maximum commits to collect')
@click.option('--output', '-o', type=click.Path(),
              help='Output file path')
@click.option('--format', '-f', type=click.Choice(['json', 'summary']),
              default='summary', help='Output format')
def collect_git(repo_path: str, max_commits: int, output: Optional[str], format: str):
    """Collect data from Git repository."""
    click.echo(f"Collecting Git data from: {repo_path}")

    try:
        config = {
            "repo_path": repo_path,
            "max_commits": max_commits
        }

        collector = GitCollector(config)
        result = collector.collect()

        if format == 'json':
            output_data = json.dumps(result, indent=2)
            if output:
                Path(output).write_text(output_data)
                click.echo(f"Results saved to: {output}")
            else:
                click.echo(output_data)
        else:
            # Summary format
            data = result['data']
            click.echo("\n" + "="*60)
            click.echo("GIT REPOSITORY ANALYSIS")
            click.echo("="*60)
            click.echo(f"Repository: {data['repository_path']}")
            click.echo(f"Current Branch: {data['current_branch']}")
            click.echo(f"\nCommits: {data['commits_count']}")
            click.echo(f"Contributors: {data['contributors_count']}")
            click.echo(f"Branches: {data['branches_count']}")

            click.echo("\nTop 5 Contributors:")
            for i, contrib in enumerate(data['contributors'][:5], 1):
                click.echo(f"  {i}. {contrib['name']} - {contrib['commits']} commits")

        click.echo(f"\n✓ Collection completed successfully")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--owner', required=True, help='Repository owner')
@click.option('--repo', required=True, help='Repository name')
@click.option('--token', envvar='GITHUB_TOKEN',
              help='GitHub token (or set GITHUB_TOKEN env var)')
@click.option('--since-days', default=30,
              help='Collect data from last N days')
@click.option('--output', '-o', type=click.Path(),
              help='Output file path')
def collect_github(owner: str, repo: str, token: str, since_days: int, output: Optional[str]):
    """Collect data from GitHub API."""
    if not token:
        click.echo("Error: GitHub token required. Set GITHUB_TOKEN or use --token", err=True)
        sys.exit(1)

    click.echo(f"Collecting GitHub data: {owner}/{repo}")

    try:
        config = {
            "owner": owner,
            "repo": repo,
            "token": token,
            "since_days": since_days
        }

        collector = GitHubCollector(config)
        result = collector.collect()

        data = result['data']

        click.echo("\n" + "="*60)
        click.echo("GITHUB REPOSITORY ANALYSIS")
        click.echo("="*60)
        click.echo(f"Repository: {owner}/{repo}")
        click.echo(f"\nPull Requests: {data['pull_requests_count']}")
        click.echo(f"Issues: {data['issues_count']}")
        click.echo(f"Workflows: {data['workflows_count']}")
        click.echo(f"Stars: {data['repository_stats']['stars']}")
        click.echo(f"Forks: {data['repository_stats']['forks']}")

        if output:
            Path(output).write_text(json.dumps(result, indent=2))
            click.echo(f"\n✓ Full results saved to: {output}")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--project-path', '-p', default='.',
              help='Path to project root')
@click.option('--languages', '-l', multiple=True,
              default=['python', 'javascript'],
              help='Languages to analyze')
@click.option('--output', '-o', type=click.Path(),
              help='Output file path')
def analyze_quality(project_path: str, languages: tuple, output: Optional[str]):
    """Analyze code quality."""
    click.echo(f"Analyzing code quality: {project_path}")

    try:
        config = {
            "project_path": project_path,
            "languages": list(languages)
        }

        analyzer = CodeQualityAnalyzer(config)
        result = analyzer.analyze({})

        data = result['data']

        click.echo("\n" + "="*60)
        click.echo("CODE QUALITY ANALYSIS")
        click.echo("="*60)
        click.echo(f"Project: {data['project_path']}")
        click.echo(f"Overall Score: {data['overall_score']:.1f}/100")

        for lang, metrics in data['metrics'].items():
            click.echo(f"\n{lang.upper()}:")
            if metrics.get('coverage'):
                click.echo(f"  Coverage: {metrics['coverage']:.1f}%")
            if metrics.get('lines_of_code'):
                click.echo(f"  Lines of Code: {metrics['lines_of_code']:,}")
            if metrics.get('complexity'):
                click.echo(f"  Avg Complexity: {metrics['complexity']['average']}")

        if output:
            Path(output).write_text(json.dumps(result, indent=2))
            click.echo(f"\n✓ Results saved to: {output}")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--repo-path', '-r', default='.',
              help='Path to repository')
@click.option('--output-dir', '-o', default='./audit-results',
              help='Output directory')
@click.option('--format', '-f',
              type=click.Choice(['json', 'markdown']),
              default='json', help='Report format')
def audit(repo_path: str, output_dir: str, format: str):
    """Run complete audit (collectors + analyzers)."""
    click.echo("Running full audit...")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    results = {}

    # Run Git collector
    click.echo("\n[1/2] Collecting Git data...")
    try:
        git_collector = GitCollector({"repo_path": repo_path})
        results['git'] = git_collector.collect()
        click.echo("✓ Git collection complete")
    except Exception as e:
        click.echo(f"✗ Git collection failed: {e}", err=True)
        results['git'] = {"error": str(e)}

    # Run code quality analyzer
    click.echo("\n[2/2] Analyzing code quality...")
    try:
        analyzer = CodeQualityAnalyzer({"project_path": repo_path})
        results['code_quality'] = analyzer.analyze({})
        click.echo("✓ Code quality analysis complete")
    except Exception as e:
        click.echo(f"✗ Code quality analysis failed: {e}", err=True)
        results['code_quality'] = {"error": str(e)}

    # Save results
    output_file = output_path / f"audit-results.{format}"

    if format == 'json':
        output_file.write_text(json.dumps(results, indent=2))
    elif format == 'markdown':
        md_content = generate_markdown_report(results)
        output_file.write_text(md_content)

    click.echo(f"\n✓ Audit complete! Results saved to: {output_file}")


def generate_markdown_report(results: dict) -> str:
    """Generate Markdown report from audit results."""
    from datetime import datetime

    lines = [
        "# OmniAudit Report",
        "",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        ""
    ]

    if 'git' in results and 'data' in results['git']:
        git_data = results['git']['data']
        lines.extend([
            "### Git Analysis",
            f"- **Commits**: {git_data.get('commits_count', 0)}",
            f"- **Contributors**: {git_data.get('contributors_count', 0)}",
            f"- **Branches**: {git_data.get('branches_count', 0)}",
            ""
        ])

    if 'code_quality' in results and 'data' in results['code_quality']:
        quality_data = results['code_quality']['data']
        lines.extend([
            "### Code Quality",
            f"- **Overall Score**: {quality_data.get('overall_score', 0):.1f}/100",
            ""
        ])

    return "\n".join(lines)


if __name__ == '__main__':
    cli()
