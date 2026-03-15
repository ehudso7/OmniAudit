"""
Browser Runner Service

Playwright-based browser verification execution service.
Runs browser journeys, captures artifacts, and normalizes results.
"""

import asyncio
import json
import os
import uuid
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)

# Artifacts storage directory
ARTIFACTS_DIR = os.getenv("OMNIAUDIT_ARTIFACTS_DIR", "artifacts/browser_runs")


def _ensure_artifacts_dir(run_id: str) -> Path:
    """Create and return artifacts directory for a run."""
    path = Path(ARTIFACTS_DIR) / run_id
    path.mkdir(parents=True, exist_ok=True)
    return path


# Default journeys if none specified
DEFAULT_JOURNEYS = [
    {
        "name": "page_load",
        "description": "Verify page loads successfully",
        "steps": [{"action": "navigate", "url": "{target_url}"}],
    },
    {
        "name": "console_errors",
        "description": "Check for JavaScript console errors",
        "steps": [{"action": "check_console"}],
    },
    {
        "name": "network_check",
        "description": "Check for failed network requests",
        "steps": [{"action": "check_network"}],
    },
    {
        "name": "accessibility",
        "description": "Basic accessibility checks",
        "steps": [{"action": "check_a11y"}],
    },
    {
        "name": "screenshot",
        "description": "Capture page screenshot",
        "steps": [{"action": "screenshot"}],
    },
]


class BrowserRunnerService:
    """Executes browser verification runs using Playwright."""

    def __init__(self):
        self._playwright = None
        self._browser = None

    async def execute_run(
        self,
        run_id: str,
        target_url: str,
        journeys: Optional[List[Dict]] = None,
        viewport_width: int = 1280,
        viewport_height: int = 720,
        device: Optional[str] = None,
        auth_config: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Execute a browser verification run.

        Returns structured results with findings, artifacts, and scores.
        """
        start_time = datetime.utcnow()
        artifacts_dir = _ensure_artifacts_dir(run_id)
        results = {
            "status": "running",
            "findings": [],
            "artifacts": [],
            "console_errors": [],
            "network_failures": [],
            "a11y_findings": [],
            "score": 100,
            "summary": "",
        }

        selected_journeys = journeys or DEFAULT_JOURNEYS

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error("Playwright not installed. Install with: pip install playwright && playwright install chromium")
            return {
                "status": "failed",
                "findings": [],
                "artifacts": [],
                "console_errors": [],
                "network_failures": [],
                "a11y_findings": [],
                "score": 0,
                "summary": "Playwright is not installed. Run: pip install playwright && playwright install chromium",
                "error": "playwright_not_installed",
            }

        console_messages = []
        network_errors = []

        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)

                context_opts = {
                    "viewport": {"width": viewport_width, "height": viewport_height},
                    "ignore_https_errors": True,
                }

                if device and hasattr(pw.devices, device):
                    device_config = pw.devices[device]
                    context_opts.update(device_config)

                context = await browser.new_context(**context_opts)

                # Enable tracing
                await context.tracing.start(screenshots=True, snapshots=True)

                page = await context.new_page()

                # Capture console messages
                page.on("console", lambda msg: console_messages.append({
                    "type": msg.type,
                    "text": msg.text,
                    "url": msg.location.get("url", "") if hasattr(msg, "location") else "",
                }))

                # Capture network failures
                page.on("requestfailed", lambda req: network_errors.append({
                    "url": req.url,
                    "method": req.method,
                    "failure": req.failure,
                    "resource_type": req.resource_type,
                }))

                # Execute journeys
                for journey in selected_journeys:
                    journey_name = journey.get("name", "unnamed")
                    try:
                        await self._execute_journey(
                            page, journey, target_url, artifacts_dir, run_id, results
                        )
                    except Exception as e:
                        results["findings"].append({
                            "journey": journey_name,
                            "check_type": "journey_error",
                            "severity": "high",
                            "category": "functional",
                            "message": f"Journey '{journey_name}' failed: {str(e)}",
                            "status": "failed",
                        })

                # Save trace
                trace_path = str(artifacts_dir / "trace.zip")
                await context.tracing.stop(path=trace_path)
                results["artifacts"].append({
                    "type": "trace",
                    "name": "trace.zip",
                    "path": trace_path,
                    "content_type": "application/zip",
                })

                await browser.close()

        except Exception as e:
            logger.error(f"Browser run {run_id} failed: {e}\n{traceback.format_exc()}")
            results["status"] = "failed"
            results["summary"] = f"Browser execution error: {str(e)}"
            results["score"] = 0
            return results

        # Process console errors
        error_messages = [m for m in console_messages if m["type"] in ("error", "warning")]
        results["console_errors"] = error_messages
        results["network_failures"] = network_errors

        # Calculate score
        results["score"] = self._calculate_score(results)
        results["status"] = "completed"
        results["summary"] = self._generate_summary(results)

        end_time = datetime.utcnow()
        results["duration_ms"] = int((end_time - start_time).total_seconds() * 1000)

        return results

    async def _execute_journey(
        self,
        page,
        journey: Dict,
        target_url: str,
        artifacts_dir: Path,
        run_id: str,
        results: Dict,
    ):
        """Execute a single journey."""
        journey_name = journey.get("name", "unnamed")
        steps = journey.get("steps", [])

        for step in steps:
            action = step.get("action", "")

            if action == "navigate":
                url = step.get("url", target_url).replace("{target_url}", target_url)
                response = await page.goto(url, wait_until="networkidle", timeout=30000)

                status = response.status if response else 0
                if status >= 400:
                    results["findings"].append({
                        "journey": journey_name,
                        "check_type": "navigation",
                        "severity": "critical" if status >= 500 else "high",
                        "category": "functional",
                        "message": f"Page returned HTTP {status}",
                        "status": "failed",
                        "url": url,
                    })
                else:
                    results["findings"].append({
                        "journey": journey_name,
                        "check_type": "navigation",
                        "severity": "info",
                        "category": "functional",
                        "message": f"Page loaded successfully (HTTP {status})",
                        "status": "passed",
                        "url": url,
                    })

            elif action == "screenshot":
                screenshot_name = step.get("name", f"screenshot_{journey_name}.png")
                screenshot_path = str(artifacts_dir / screenshot_name)
                await page.screenshot(path=screenshot_path, full_page=True)
                results["artifacts"].append({
                    "type": "screenshot",
                    "name": screenshot_name,
                    "path": screenshot_path,
                    "content_type": "image/png",
                })

            elif action == "check_console":
                # Console messages are collected passively; we evaluate here
                pass  # Processed after run completes

            elif action == "check_network":
                # Network errors are collected passively; we evaluate here
                pass  # Processed after run completes

            elif action == "check_a11y":
                a11y_findings = await self._check_accessibility(page)
                results["a11y_findings"].extend(a11y_findings)
                for finding in a11y_findings:
                    results["findings"].append({
                        "journey": journey_name,
                        "check_type": "accessibility",
                        "severity": finding.get("severity", "medium"),
                        "category": "accessibility",
                        "message": finding.get("message", ""),
                        "status": "failed",
                        "selector": finding.get("selector", ""),
                    })

            elif action == "click":
                selector = step.get("selector", "")
                if selector:
                    await page.click(selector, timeout=10000)

            elif action == "fill":
                selector = step.get("selector", "")
                value = step.get("value", "")
                if selector:
                    await page.fill(selector, value)

            elif action == "wait":
                ms = step.get("ms", 1000)
                await page.wait_for_timeout(ms)

            elif action == "assert_visible":
                selector = step.get("selector", "")
                try:
                    await page.wait_for_selector(selector, state="visible", timeout=5000)
                    results["findings"].append({
                        "journey": journey_name,
                        "check_type": "assertion",
                        "severity": "info",
                        "category": "functional",
                        "message": f"Element '{selector}' is visible",
                        "status": "passed",
                    })
                except Exception:
                    results["findings"].append({
                        "journey": journey_name,
                        "check_type": "assertion",
                        "severity": "high",
                        "category": "functional",
                        "message": f"Element '{selector}' not visible",
                        "status": "failed",
                    })

            elif action == "assert_text":
                selector = step.get("selector", "")
                expected = step.get("text", "")
                try:
                    element = await page.wait_for_selector(selector, timeout=5000)
                    actual = await element.text_content()
                    if expected in (actual or ""):
                        results["findings"].append({
                            "journey": journey_name,
                            "check_type": "assertion",
                            "severity": "info",
                            "category": "functional",
                            "message": f"Text '{expected}' found in '{selector}'",
                            "status": "passed",
                        })
                    else:
                        results["findings"].append({
                            "journey": journey_name,
                            "check_type": "assertion",
                            "severity": "high",
                            "category": "functional",
                            "message": f"Expected '{expected}' in '{selector}', got '{actual}'",
                            "status": "failed",
                        })
                except Exception:
                    results["findings"].append({
                        "journey": journey_name,
                        "check_type": "assertion",
                        "severity": "high",
                        "category": "functional",
                        "message": f"Could not find element '{selector}' for text assertion",
                        "status": "failed",
                    })

    async def _check_accessibility(self, page) -> List[Dict]:
        """Run basic accessibility checks via injected JS."""
        a11y_script = """
        () => {
            const findings = [];

            // Check images without alt text
            document.querySelectorAll('img').forEach(img => {
                if (!img.alt && !img.getAttribute('aria-label') && !img.getAttribute('role')) {
                    findings.push({
                        severity: 'medium',
                        message: 'Image missing alt text',
                        selector: img.tagName + (img.className ? '.' + img.className.split(' ')[0] : ''),
                        rule: 'img-alt'
                    });
                }
            });

            // Check form inputs without labels
            document.querySelectorAll('input, select, textarea').forEach(input => {
                const id = input.id;
                const hasLabel = id && document.querySelector(`label[for="${id}"]`);
                const hasAria = input.getAttribute('aria-label') || input.getAttribute('aria-labelledby');
                if (!hasLabel && !hasAria && input.type !== 'hidden' && input.type !== 'submit') {
                    findings.push({
                        severity: 'medium',
                        message: 'Form input missing associated label',
                        selector: input.tagName + '#' + (id || 'unnamed'),
                        rule: 'label'
                    });
                }
            });

            // Check for empty buttons/links
            document.querySelectorAll('button, a').forEach(el => {
                const text = (el.textContent || '').trim();
                const ariaLabel = el.getAttribute('aria-label');
                if (!text && !ariaLabel && el.querySelectorAll('img, svg').length === 0) {
                    findings.push({
                        severity: 'medium',
                        message: 'Interactive element has no accessible text',
                        selector: el.tagName + (el.className ? '.' + el.className.split(' ')[0] : ''),
                        rule: 'button-name'
                    });
                }
            });

            // Check heading hierarchy
            const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'));
            let prevLevel = 0;
            headings.forEach(h => {
                const level = parseInt(h.tagName[1]);
                if (level > prevLevel + 1 && prevLevel > 0) {
                    findings.push({
                        severity: 'low',
                        message: `Heading level skipped: h${prevLevel} to h${level}`,
                        selector: h.tagName,
                        rule: 'heading-order'
                    });
                }
                prevLevel = level;
            });

            // Check color contrast on text elements (basic check)
            document.querySelectorAll('p, span, a, button, h1, h2, h3, h4, h5, h6, li, td, th, label').forEach(el => {
                const style = window.getComputedStyle(el);
                const color = style.color;
                const bg = style.backgroundColor;
                if (color === bg && color !== 'rgba(0, 0, 0, 0)') {
                    findings.push({
                        severity: 'high',
                        message: 'Text color matches background color',
                        selector: el.tagName,
                        rule: 'color-contrast'
                    });
                }
            });

            return findings;
        }
        """
        try:
            findings = await page.evaluate(a11y_script)
            return findings if isinstance(findings, list) else []
        except Exception as e:
            logger.warning(f"Accessibility check failed: {e}")
            return []

    def _calculate_score(self, results: Dict) -> int:
        """Calculate overall score from findings."""
        score = 100
        severity_penalties = {
            "critical": 25,
            "high": 15,
            "medium": 5,
            "low": 2,
            "info": 0,
        }

        failed_findings = [f for f in results["findings"] if f.get("status") == "failed"]
        for finding in failed_findings:
            severity = finding.get("severity", "medium")
            score -= severity_penalties.get(severity, 5)

        # Console errors penalty
        error_count = len([m for m in results.get("console_errors", []) if m.get("type") == "error"])
        score -= error_count * 3

        # Network failures penalty
        score -= len(results.get("network_failures", [])) * 5

        return max(0, min(100, score))

    def _generate_summary(self, results: Dict) -> str:
        """Generate human-readable summary."""
        failed = [f for f in results["findings"] if f.get("status") == "failed"]
        passed = [f for f in results["findings"] if f.get("status") == "passed"]
        console_errors = len([m for m in results.get("console_errors", []) if m.get("type") == "error"])
        network_fails = len(results.get("network_failures", []))
        a11y_count = len(results.get("a11y_findings", []))

        parts = []
        parts.append(f"{len(passed)} checks passed, {len(failed)} failed.")
        if console_errors:
            parts.append(f"{console_errors} console errors.")
        if network_fails:
            parts.append(f"{network_fails} network failures.")
        if a11y_count:
            parts.append(f"{a11y_count} accessibility issues.")
        parts.append(f"Score: {results['score']}/100.")

        return " ".join(parts)
