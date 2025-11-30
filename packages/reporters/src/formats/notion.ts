import type { AuditResult, Reporter, ReporterOptions, Finding } from '../types.js';

// Notion database entry format
// https://developers.notion.com/reference/page

interface NotionPage {
  parent: {
    database_id: string;
  };
  properties: {
    Name: {
      title: Array<{
        text: {
          content: string;
        };
      }>;
    };
    Severity: {
      select: {
        name: string;
      };
    };
    Category: {
      select: {
        name: string;
      };
    };
    File: {
      rich_text: Array<{
        text: {
          content: string;
        };
      }>;
    };
    Line: {
      number?: number;
    };
    Status: {
      select: {
        name: string;
      };
    };
    [key: string]: unknown;
  };
  children: Array<{
    object: 'block';
    type: string;
    [key: string]: unknown;
  }>;
}

export class NotionReporter implements Reporter {
  name = 'Notion Reporter';
  format = 'notion';

  private findingToNotionPage(finding: Finding, databaseId: string): NotionPage {
    const page: NotionPage = {
      parent: {
        database_id: databaseId,
      },
      properties: {
        Name: {
          title: [
            {
              text: {
                content: finding.title,
              },
            },
          ],
        },
        Severity: {
          select: {
            name: finding.severity.charAt(0).toUpperCase() + finding.severity.slice(1),
          },
        },
        Category: {
          select: {
            name: finding.category,
          },
        },
        File: {
          rich_text: [
            {
              text: {
                content: finding.file,
              },
            },
          ],
        },
        Line: {
          number: finding.line,
        },
        Status: {
          select: {
            name: 'Open',
          },
        },
      },
      children: [
        {
          object: 'block',
          type: 'heading_2',
          heading_2: {
            rich_text: [
              {
                text: {
                  content: 'Message',
                },
              },
            ],
          },
        },
        {
          object: 'block',
          type: 'paragraph',
          paragraph: {
            rich_text: [
              {
                text: {
                  content: finding.message,
                },
              },
            ],
          },
        },
      ],
    };

    if (finding.description) {
      page.children.push(
        {
          object: 'block',
          type: 'heading_2',
          heading_2: {
            rich_text: [
              {
                text: {
                  content: 'Description',
                },
              },
            ],
          },
        },
        {
          object: 'block',
          type: 'paragraph',
          paragraph: {
            rich_text: [
              {
                text: {
                  content: finding.description,
                },
              },
            ],
          },
        }
      );
    }

    if (finding.code_snippet) {
      page.children.push({
        object: 'block',
        type: 'code',
        code: {
          rich_text: [
            {
              text: {
                content: finding.code_snippet,
              },
            },
          ],
          language: 'javascript',
        },
      });
    }

    if (finding.recommendation) {
      page.children.push(
        {
          object: 'block',
          type: 'heading_2',
          heading_2: {
            rich_text: [
              {
                text: {
                  content: 'Recommendation',
                },
              },
            ],
          },
        },
        {
          object: 'block',
          type: 'callout',
          callout: {
            icon: {
              emoji: '💡',
            },
            rich_text: [
              {
                text: {
                  content: finding.recommendation,
                },
              },
            ],
          },
        }
      );
    }

    return page;
  }

  async generate(result: AuditResult, options?: ReporterOptions): Promise<string> {
    const databaseId = options?.template || 'DATABASE_ID';

    const pages = result.findings.map(f => this.findingToNotionPage(f, databaseId));

    const output = {
      database_id: databaseId,
      pages,
      metadata: {
        project: result.project,
        timestamp: result.timestamp,
        total_findings: result.total_findings,
        findings_by_severity: result.findings_by_severity,
      },
    };

    return options?.pretty
      ? JSON.stringify(output, null, 2)
      : JSON.stringify(output);
  }
}
