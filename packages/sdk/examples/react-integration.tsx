/**
 * React Integration Example
 *
 * Demonstrates how to integrate OmniAudit SDK with React applications.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  createClient,
  runAuditWithHooks,
  type AuditProgress,
  type AuditResult,
  type Finding,
} from '@omniaudit/sdk';

// Custom hook for OmniAudit
function useOmniAudit(apiUrl: string, apiKey?: string) {
  const [client] = useState(() => createClient({ apiUrl, apiKey }));
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState<AuditProgress | null>(null);
  const [result, setResult] = useState<AuditResult | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [error, setError] = useState<Error | null>(null);

  const runAudit = useCallback(
    async (path: string) => {
      setIsRunning(true);
      setProgress(null);
      setResult(null);
      setFindings([]);
      setError(null);

      try {
        const auditResult = await runAuditWithHooks(
          { path },
          {
            onProgress: (p) => setProgress(p),
            onFinding: (f) => setFindings((prev) => [...prev, f]),
            onComplete: (r) => {
              setResult(r);
              setIsRunning(false);
            },
            onError: (e) => {
              setError(e);
              setIsRunning(false);
            },
          },
          apiUrl,
          apiKey
        );

        return auditResult;
      } catch (e) {
        const err = e instanceof Error ? e : new Error('Unknown error');
        setError(err);
        setIsRunning(false);
        throw err;
      }
    },
    [apiUrl, apiKey]
  );

  return {
    client,
    runAudit,
    isRunning,
    progress,
    result,
    findings,
    error,
  };
}

// Progress Bar Component
function ProgressBar({ value, max = 100 }: { value: number; max?: number }) {
  const percentage = Math.round((value / max) * 100);

  return (
    <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
      <div
        className="bg-blue-600 h-full transition-all duration-300 ease-out"
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
}

// Severity Badge Component
function SeverityBadge({ severity }: { severity: Finding['severity'] }) {
  const colors = {
    critical: 'bg-red-600 text-white',
    high: 'bg-orange-500 text-white',
    medium: 'bg-yellow-500 text-black',
    low: 'bg-blue-500 text-white',
    info: 'bg-gray-500 text-white',
  };

  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${colors[severity]}`}>
      {severity.toUpperCase()}
    </span>
  );
}

// Finding Card Component
function FindingCard({ finding }: { finding: Finding }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border rounded-lg p-4 mb-2 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <SeverityBadge severity={finding.severity} />
            <span className="text-sm text-gray-500">{finding.rule_id}</span>
          </div>
          <h3 className="font-semibold text-lg">{finding.title}</h3>
          <p className="text-sm text-gray-600">
            {finding.file}:{finding.line}
          </p>
        </div>
        <button onClick={() => setExpanded(!expanded)} className="text-blue-600 hover:underline">
          {expanded ? 'Hide' : 'Show'} details
        </button>
      </div>

      {expanded && (
        <div className="mt-4 pt-4 border-t">
          <p className="text-gray-700 mb-2">{finding.description}</p>
          {finding.code_snippet && (
            <pre className="bg-gray-100 p-3 rounded text-sm overflow-x-auto mb-2">
              {finding.code_snippet}
            </pre>
          )}
          {finding.recommendation && (
            <div className="bg-blue-50 p-3 rounded">
              <strong className="text-blue-800">Recommendation:</strong>
              <p className="text-blue-700">{finding.recommendation}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Stats Card Component
function StatsCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className={`rounded-lg p-4 ${color}`}>
      <div className="text-3xl font-bold">{value}</div>
      <div className="text-sm opacity-75">{label}</div>
    </div>
  );
}

// Main Audit Dashboard Component
export function AuditDashboard() {
  const [projectPath, setProjectPath] = useState('./src');
  const { runAudit, isRunning, progress, result, findings, error } = useOmniAudit(
    process.env.REACT_APP_OMNIAUDIT_API_URL || 'http://localhost:8000',
    process.env.REACT_APP_OMNIAUDIT_API_KEY
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await runAudit(projectPath);
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">OmniAudit Code Scanner</h1>

      {/* Audit Form */}
      <form onSubmit={handleSubmit} className="mb-8">
        <div className="flex gap-4">
          <input
            type="text"
            value={projectPath}
            onChange={(e) => setProjectPath(e.target.value)}
            placeholder="Enter project path..."
            className="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            disabled={isRunning}
          />
          <button
            type="submit"
            disabled={isRunning || !projectPath}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isRunning ? 'Scanning...' : 'Start Audit'}
          </button>
        </div>
      </form>

      {/* Progress */}
      {isRunning && progress && (
        <div className="mb-8 p-4 bg-gray-50 rounded-lg">
          <div className="flex justify-between mb-2">
            <span className="font-medium">{progress.message}</span>
            <span className="text-gray-600">{progress.progress}%</span>
          </div>
          <ProgressBar value={progress.progress} />
          {progress.filesScanned !== undefined && (
            <p className="text-sm text-gray-500 mt-2">
              Files: {progress.filesScanned}/{progress.totalFiles} | Findings:{' '}
              {progress.findingsCount || 0}
            </p>
          )}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mb-8 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          <strong>Error:</strong> {error.message}
        </div>
      )}

      {/* Results */}
      {result && (
        <>
          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
            <StatsCard
              label="Critical"
              value={result.findings_by_severity.critical}
              color="bg-red-100 text-red-800"
            />
            <StatsCard
              label="High"
              value={result.findings_by_severity.high}
              color="bg-orange-100 text-orange-800"
            />
            <StatsCard
              label="Medium"
              value={result.findings_by_severity.medium}
              color="bg-yellow-100 text-yellow-800"
            />
            <StatsCard
              label="Low"
              value={result.findings_by_severity.low}
              color="bg-blue-100 text-blue-800"
            />
            <StatsCard
              label="Info"
              value={result.findings_by_severity.info}
              color="bg-gray-100 text-gray-800"
            />
          </div>

          {/* Summary */}
          <div className="bg-green-50 p-4 rounded-lg mb-8">
            <h2 className="font-semibold text-green-800">Audit Complete</h2>
            <p className="text-green-700">
              Analyzed {result.total_files} files in {result.duration_ms}ms. Found{' '}
              {result.total_findings} issues.
            </p>
          </div>

          {/* Findings List */}
          <div>
            <h2 className="text-xl font-semibold mb-4">Findings ({findings.length})</h2>
            {findings.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No issues found!</p>
            ) : (
              <div>
                {findings.map((finding) => (
                  <FindingCard key={finding.id} finding={finding} />
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

// Export the hook for use in other components
export { useOmniAudit };
