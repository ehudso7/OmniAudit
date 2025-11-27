import type { AuditResult, Reporter, ReporterOptions, Finding, Severity } from '../types.js';

// JIRA issue creation format
// https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/

interface JiraIssue {
  fields: {
    project: {
      key: string;
    };
    summary: string;
    description: {
      type: 'doc';
      version: 1;
      content: Array<{
        type: string;
        content?: unknown[];
        attrs?: unknown;
      }>;
    };
    issuetype: {
      name: string;
    };
    priority?: {
      name: string;
    };
    labels?: string[];
  };
}

export class JIRAReporter implements Reporter {
  name = 'JIRA Reporter';
  format = 'jira';

  private severityToPriority(severity: Severity): string {
    const mapping: Record<Severity, string> = {
      critical: 'Highest',
      high: 'High',
      medium: 'Medium',
      low: 'Low',
      info: 'Lowest',
    };
    return mapping[severity];
  }

  private findingToJiraIssue(finding: Finding, projectKey: string): JiraIssue {
    const location = finding.line
      ? `${finding.file}:${finding.line}`
      : finding.file;

    return {
      fields: {
        project: {
          key: projectKey,
        },
        summary: `[${finding.severity.toUpperCase()}] ${finding.title}`,
        description: {
          type: 'doc',
          version: 1,
          content: [
            {
              type: 'paragraph',
              content: [
                {
                  type: 'text',
                  text: finding.message,
                },
              ],
            },
            {
              type: 'heading',
              attrs: { level: 3 },
              content: [
                {
                  type: 'text',
                  text: 'Details',
                },
              ],
            },
            {
              type: 'paragraph',
              content: [
                {
                  type: 'text',
                  text: `File: ${location}`,
                  marks: [{ type: 'code' }],
                },
              ],
            },
            {
              type: 'paragraph',
              content: [
                {
                  type: 'text',
                  text: `Category: ${finding.category}`,
                },
              ],
            },
            {
              type: 'paragraph',
              content: [
                {
                  type: 'text',
                  text: `Rule: ${finding.rule_id}`,
                },
              ],
            },
            ...(finding.description ? [{
              type: 'heading',
              attrs: { level: 3 },
              content: [
                {
                  type: 'text',
                  text: 'Description',
                },
              ],
            }, {
              type: 'paragraph',
              content: [
                {
                  type: 'text',
                  text: finding.description,
                },
              ],
            }] : []),
            ...(finding.recommendation ? [{
              type: 'heading',
              attrs: { level: 3 },
              content: [
                {
                  type: 'text',
                  text: 'Recommendation',
                },
              ],
            }, {
              type: 'paragraph',
              content: [
                {
                  type: 'text',
                  text: finding.recommendation,
                },
              ],
            }] : []),
            ...(finding.code_snippet ? [{
              type: 'codeBlock',
              content: [
                {
                  type: 'text',
                  text: finding.code_snippet,
                },
              ],
            }] : []),
          ],
        },
        issuetype: {
          name: 'Bug',
        },
        priority: {
          name: this.severityToPriority(finding.severity),
        },
        labels: [
          'omniaudit',
          `severity-${finding.severity}`,
          `category-${finding.category}`,
          finding.rule_id,
        ],
      },
    };
  }

  async generate(result: AuditResult, options?: ReporterOptions): Promise<string> {
    const projectKey = options?.template || 'PROJ';

    const issues = result.findings.map(f => this.findingToJiraIssue(f, projectKey));

    const output = {
      issueUpdates: issues,
    };

    return options?.pretty
      ? JSON.stringify(output, null, 2)
      : JSON.stringify(output);
  }
}
