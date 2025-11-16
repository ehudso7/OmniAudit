# Reporters

Reporters generate output from analyzed data in various formats.

## Planned Reporters (Phase 2)

- **JSONReporter** - Export as JSON
- **HTMLReporter** - Generate HTML reports
- **PDFReporter** - Generate PDF reports
- **SlackReporter** - Send notifications to Slack
- **EmailReporter** - Email reports to stakeholders

## Creating a Reporter

```python
from omniaudit.reporters.base import BaseReporter

class MyReporter(BaseReporter):
    def generate(self, analysis: Dict[str, Any]) -> str:
        # Generate and return report
        return report_content
```
