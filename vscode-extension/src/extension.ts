import * as vscode from 'vscode';
import axios from 'axios';

interface OmniAuditConfig {
  apiKey: string;
  enabledSkills: string[];
  analyzeOnSave: boolean;
  analyzeOnType: boolean;
  autoFix: boolean;
  maxIssues: number;
  severityFilter: ('error' | 'warning' | 'info')[];
  useCache: boolean;
  endpoint: string;
}

interface AnalysisResult {
  execution_id: string;
  skill_id: string;
  success: boolean;
  optimizations?: Optimization[];
  transformed_code?: string;
  metrics?: {
    issues_found: number;
    warnings_found: number;
    suggestions_found: number;
  };
}

interface Optimization {
  id: string;
  type: string;
  severity: 'error' | 'warning' | 'info';
  title: string;
  description: string;
  location: {
    file: string;
    line: number;
    column?: number;
    length?: number;
  };
  suggested_fix: string | null;
  auto_fixable: boolean;
}

class OmniAuditExtension {
  private diagnosticCollection: vscode.DiagnosticCollection;
  private statusBarItem: vscode.StatusBarItem;
  private issuesTreeProvider: IssuesTreeProvider;
  private skillsTreeProvider: SkillsTreeProvider;
  private analysisCache: Map<string, AnalysisResult[]> = new Map();
  private typingTimeout?: NodeJS.Timeout;

  constructor(private context: vscode.ExtensionContext) {
    this.diagnosticCollection = vscode.languages.createDiagnosticCollection('omniaudit');
    this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    this.issuesTreeProvider = new IssuesTreeProvider();
    this.skillsTreeProvider = new SkillsTreeProvider();

    this.setupStatusBar();
    this.registerCommands();
    this.registerEventListeners();
    this.registerTreeProviders();
  }

  private setupStatusBar(): void {
    this.statusBarItem.text = '$(search) OmniAudit';
    this.statusBarItem.tooltip = 'Click to analyze current file';
    this.statusBarItem.command = 'omniaudit.analyzeFile';
    this.statusBarItem.show();
  }

  private registerCommands(): void {
    this.context.subscriptions.push(
      vscode.commands.registerCommand('omniaudit.analyzeFile', () => this.analyzeCurrentFile()),
      vscode.commands.registerCommand('omniaudit.analyzeSelection', () =>
        this.analyzeSelection(),
      ),
      vscode.commands.registerCommand('omniaudit.analyzeWorkspace', () =>
        this.analyzeWorkspace(),
      ),
      vscode.commands.registerCommand('omniaudit.fixIssue', (optimization: Optimization) =>
        this.fixIssue(optimization),
      ),
      vscode.commands.registerCommand('omniaudit.showSkills', () => this.showSkills()),
      vscode.commands.registerCommand('omniaudit.configureSkills', () => this.configureSkills()),
      vscode.commands.registerCommand('omniaudit.clearCache', () => this.clearCache()),
    );
  }

  private registerEventListeners(): void {
    const config = this.getConfig();

    // Analyze on save
    if (config.analyzeOnSave) {
      this.context.subscriptions.push(
        vscode.workspace.onDidSaveTextDocument((document) => {
          if (this.isSupported(document.languageId)) {
            this.analyzeDocument(document);
          }
        }),
      );
    }

    // Analyze on type (with debounce)
    if (config.analyzeOnType) {
      this.context.subscriptions.push(
        vscode.workspace.onDidChangeTextDocument((event) => {
          if (this.isSupported(event.document.languageId)) {
            if (this.typingTimeout) {
              clearTimeout(this.typingTimeout);
            }
            this.typingTimeout = setTimeout(() => {
              this.analyzeDocument(event.document);
            }, 2000); // 2 second debounce
          }
        }),
      );
    }

    // Clear diagnostics when document is closed
    this.context.subscriptions.push(
      vscode.workspace.onDidCloseTextDocument((document) => {
        this.diagnosticCollection.delete(document.uri);
      }),
    );
  }

  private registerTreeProviders(): void {
    this.context.subscriptions.push(
      vscode.window.registerTreeDataProvider('omniaudit.issues', this.issuesTreeProvider),
      vscode.window.registerTreeDataProvider('omniaudit.skills', this.skillsTreeProvider),
    );
  }

  private async analyzeCurrentFile(): Promise<void> {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      vscode.window.showWarningMessage('No active editor');
      return;
    }

    await this.analyzeDocument(editor.document);
  }

  private async analyzeSelection(): Promise<void> {
    const editor = vscode.window.activeTextEditor;
    if (!editor || !editor.selection) {
      vscode.window.showWarningMessage('No text selected');
      return;
    }

    const selection = editor.selection;
    const code = editor.document.getText(selection);

    await this.analyze(code, editor.document.languageId, editor.document.fileName);
  }

  private async analyzeWorkspace(): Promise<void> {
    await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: 'OmniAudit: Analyzing workspace',
        cancellable: true,
      },
      async (progress, token) => {
        const files = await vscode.workspace.findFiles(
          '**/*.{ts,tsx,js,jsx}',
          '**/node_modules/**',
        );

        let completed = 0;
        const total = files.length;

        for (const file of files) {
          if (token.isCancellationRequested) {
            break;
          }

          const document = await vscode.workspace.openTextDocument(file);
          await this.analyzeDocument(document, false);

          completed++;
          progress.report({
            increment: (100 / total),
            message: `${completed}/${total} files`,
          });
        }

        vscode.window.showInformationMessage(
          `OmniAudit: Analyzed ${completed} files`,
        );
      },
    );
  }

  private async analyzeDocument(
    document: vscode.TextDocument,
    showProgress = true,
  ): Promise<void> {
    if (!this.isSupported(document.languageId)) {
      return;
    }

    const code = document.getText();
    await this.analyze(code, document.languageId, document.fileName, showProgress);
  }

  private async analyze(
    code: string,
    language: string,
    filePath: string,
    showProgress = true,
  ): Promise<void> {
    const config = this.getConfig();

    if (!config.apiKey) {
      vscode.window.showErrorMessage(
        'OmniAudit: API key not configured. Please set omniaudit.apiKey in settings.',
      );
      return;
    }

    const cacheKey = `${filePath}:${this.hashCode(code)}`;
    if (config.useCache && this.analysisCache.has(cacheKey)) {
      const cached = this.analysisCache.get(cacheKey)!;
      this.displayResults(filePath, cached);
      return;
    }

    const analyzeFunc = async () => {
      try {
        this.statusBarItem.text = '$(sync~spin) OmniAudit: Analyzing...';

        const response = await axios.post(
          `${config.endpoint}/api/v1/analyze`,
          {
            code,
            language,
            file_path: filePath,
            skills: config.enabledSkills,
            options: {
              skipCache: !config.useCache,
              maxIssues: config.maxIssues,
              severityFilter: config.severityFilter,
            },
          },
          {
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${config.apiKey}`,
            },
            timeout: 60000,
          },
        );

        if (response.data.success) {
          const results: AnalysisResult[] = response.data.results;

          // Cache results
          if (config.useCache) {
            this.analysisCache.set(cacheKey, results);
          }

          this.displayResults(filePath, results);

          const totalIssues = results.reduce(
            (sum, r) => sum + (r.metrics?.issues_found || 0),
            0,
          );
          this.statusBarItem.text = `$(check) OmniAudit: ${totalIssues} issues`;

          vscode.window.showInformationMessage(
            `OmniAudit: Found ${totalIssues} issues`,
          );
        } else {
          throw new Error('Analysis failed');
        }
      } catch (error) {
        this.statusBarItem.text = '$(error) OmniAudit: Failed';
        vscode.window.showErrorMessage(
          `OmniAudit: ${error instanceof Error ? error.message : 'Unknown error'}`,
        );
      }
    };

    if (showProgress) {
      await vscode.window.withProgress(
        {
          location: vscode.ProgressLocation.Notification,
          title: 'OmniAudit: Analyzing code...',
          cancellable: false,
        },
        analyzeFunc,
      );
    } else {
      await analyzeFunc();
    }
  }

  private displayResults(filePath: string, results: AnalysisResult[]): void {
    const uri = vscode.Uri.file(filePath);
    const diagnostics: vscode.Diagnostic[] = [];

    for (const result of results) {
      if (!result.optimizations) continue;

      for (const optimization of result.optimizations) {
        const range = new vscode.Range(
          optimization.location.line - 1,
          optimization.location.column || 0,
          optimization.location.line - 1,
          (optimization.location.column || 0) + (optimization.location.length || 100),
        );

        const severity =
          optimization.severity === 'error'
            ? vscode.DiagnosticSeverity.Error
            : optimization.severity === 'warning'
              ? vscode.DiagnosticSeverity.Warning
              : vscode.DiagnosticSeverity.Information;

        const diagnostic = new vscode.Diagnostic(
          range,
          optimization.title,
          severity,
        );

        diagnostic.source = 'OmniAudit';
        diagnostic.code = optimization.id;

        if (optimization.suggested_fix) {
          diagnostic.relatedInformation = [
            new vscode.DiagnosticRelatedInformation(
              new vscode.Location(uri, range),
              `Suggested fix: ${optimization.suggested_fix}`,
            ),
          ];
        }

        diagnostics.push(diagnostic);
      }
    }

    this.diagnosticCollection.set(uri, diagnostics);

    // Update issues tree
    this.issuesTreeProvider.setIssues(results);
  }

  private async fixIssue(optimization: Optimization): Promise<void> {
    if (!optimization.auto_fixable || !optimization.suggested_fix) {
      vscode.window.showWarningMessage('This issue cannot be auto-fixed');
      return;
    }

    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      return;
    }

    const edit = new vscode.WorkspaceEdit();
    const range = new vscode.Range(
      optimization.location.line - 1,
      optimization.location.column || 0,
      optimization.location.line - 1,
      (optimization.location.column || 0) + (optimization.location.length || 100),
    );

    edit.replace(editor.document.uri, range, optimization.suggested_fix);

    await vscode.workspace.applyEdit(edit);
    vscode.window.showInformationMessage('Fix applied');
  }

  private async showSkills(): Promise<void> {
    const config = this.getConfig();

    try {
      const response = await axios.get(`${config.endpoint}/api/v1/skills`);
      const skills = response.data.skills;

      const items = skills.map((skill: any) => ({
        label: skill.metadata.name,
        description: skill.skill_id,
        detail: skill.metadata.description,
        picked: config.enabledSkills.includes(skill.skill_id),
      }));

      const selected = await vscode.window.showQuickPick(items, {
        canPickMany: true,
        placeHolder: 'Select skills to enable',
      });

      if (selected) {
        const skillIds = selected.map((item) => item.description);
        await vscode.workspace
          .getConfiguration('omniaudit')
          .update('enabledSkills', skillIds, vscode.ConfigurationTarget.Global);

        vscode.window.showInformationMessage('Skills configuration updated');
      }
    } catch (error) {
      vscode.window.showErrorMessage('Failed to fetch skills');
    }
  }

  private async configureSkills(): Promise<void> {
    await vscode.commands.executeCommand(
      'workbench.action.openSettings',
      'omniaudit.enabledSkills',
    );
  }

  private clearCache(): void {
    this.analysisCache.clear();
    vscode.window.showInformationMessage('OmniAudit: Cache cleared');
  }

  private isSupported(languageId: string): boolean {
    return ['typescript', 'javascript', 'typescriptreact', 'javascriptreact'].includes(
      languageId,
    );
  }

  private getConfig(): OmniAuditConfig {
    const config = vscode.workspace.getConfiguration('omniaudit');
    return {
      apiKey: config.get<string>('apiKey') || '',
      enabledSkills: config.get<string[]>('enabledSkills') || ['performance-optimizer-pro'],
      analyzeOnSave: config.get<boolean>('analyzeOnSave') || false,
      analyzeOnType: config.get<boolean>('analyzeOnType') || false,
      autoFix: config.get<boolean>('autoFix') || false,
      maxIssues: config.get<number>('maxIssues') || 50,
      severityFilter: config.get<('error' | 'warning' | 'info')[]>('severityFilter') || [
        'error',
        'warning',
        'info',
      ],
      useCache: config.get<boolean>('useCache') !== false,
      endpoint: config.get<string>('endpoint') || 'https://api.omniaudit.dev',
    };
  }

  private hashCode(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash = hash & hash;
    }
    return hash;
  }

  dispose(): void {
    this.diagnosticCollection.dispose();
    this.statusBarItem.dispose();
  }
}

// Tree Data Providers
class IssuesTreeProvider implements vscode.TreeDataProvider<IssueTreeItem> {
  private _onDidChangeTreeData: vscode.EventEmitter<IssueTreeItem | undefined | null | void> =
    new vscode.EventEmitter<IssueTreeItem | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<IssueTreeItem | undefined | null | void> =
    this._onDidChangeTreeData.event;

  private issues: AnalysisResult[] = [];

  setIssues(issues: AnalysisResult[]): void {
    this.issues = issues;
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: IssueTreeItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: IssueTreeItem): Thenable<IssueTreeItem[]> {
    if (!element) {
      return Promise.resolve(
        this.issues.flatMap((result) =>
          result.optimizations?.map(
            (opt) =>
              new IssueTreeItem(
                opt.title,
                opt.severity,
                vscode.TreeItemCollapsibleState.None,
                opt,
              ),
          ) || [],
        ),
      );
    }
    return Promise.resolve([]);
  }
}

class IssueTreeItem extends vscode.TreeItem {
  constructor(
    public readonly label: string,
    public readonly severity: string,
    public readonly collapsibleState: vscode.TreeItemCollapsibleState,
    public readonly optimization: Optimization,
  ) {
    super(label, collapsibleState);
    this.tooltip = optimization.description;
    this.description = `Line ${optimization.location.line}`;
    this.iconPath = this.getIcon();
  }

  private getIcon(): vscode.ThemeIcon {
    switch (this.severity) {
      case 'error':
        return new vscode.ThemeIcon('error');
      case 'warning':
        return new vscode.ThemeIcon('warning');
      default:
        return new vscode.ThemeIcon('info');
    }
  }
}

class SkillsTreeProvider implements vscode.TreeDataProvider<SkillTreeItem> {
  private _onDidChangeTreeData: vscode.EventEmitter<SkillTreeItem | undefined | null | void> =
    new vscode.EventEmitter<SkillTreeItem | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<SkillTreeItem | undefined | null | void> =
    this._onDidChangeTreeData.event;

  getTreeItem(element: SkillTreeItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: SkillTreeItem): Thenable<SkillTreeItem[]> {
    if (!element) {
      const config = vscode.workspace.getConfiguration('omniaudit');
      const enabledSkills = config.get<string[]>('enabledSkills') || [];

      return Promise.resolve(
        enabledSkills.map(
          (skill) =>
            new SkillTreeItem(skill, vscode.TreeItemCollapsibleState.None),
        ),
      );
    }
    return Promise.resolve([]);
  }
}

class SkillTreeItem extends vscode.TreeItem {
  constructor(
    public readonly label: string,
    public readonly collapsibleState: vscode.TreeItemCollapsibleState,
  ) {
    super(label, collapsibleState);
    this.iconPath = new vscode.ThemeIcon('extensions');
  }
}

export function activate(context: vscode.ExtensionContext): void {
  const extension = new OmniAuditExtension(context);
  context.subscriptions.push(extension);

  vscode.window.showInformationMessage('OmniAudit extension activated!');
}

export function deactivate(): void {
  // Cleanup if needed
}
