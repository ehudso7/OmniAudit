import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './App.css';

interface DashboardData {
  commits: any[];
  contributors: any[];
  codeQuality: any;
  summary: {
    totalCommits: number;
    totalContributors: number;
    qualityScore: number;
    coverage: number;
  };
}

function App() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);

      // Run audit via API
      const response = await fetch('/api/v1/audit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          collectors: {
            git_collector: { repo_path: '.', max_commits: 100 }
          },
          analyzers: {
            code_quality: { project_path: '.', languages: ['python'] }
          }
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch: ${response.statusText}`);
      }

      const result = await response.json();

      // Transform data for dashboard
      const gitData = result.results.collectors.git_collector?.data || {};
      const qualityData = result.results.analyzers.code_quality?.data || {};

      setData({
        commits: gitData.commits || [],
        contributors: gitData.contributors || [],
        codeQuality: qualityData.metrics || {},
        summary: {
          totalCommits: gitData.commits_count || 0,
          totalContributors: gitData.contributors_count || 0,
          qualityScore: qualityData.overall_score || 0,
          coverage: qualityData.metrics?.python?.coverage || 0
        }
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error">
        <h2>Error Loading Dashboard</h2>
        <p>{error}</p>
        <button onClick={fetchDashboardData}>Retry</button>
      </div>
    );
  }

  if (!data) return null;

  // Prepare commit timeline data
  const commitTimeline = data.commits
    .reduce((acc: any[], commit) => {
      const date = new Date(commit.date).toLocaleDateString();
      const existing = acc.find(item => item.date === date);
      if (existing) {
        existing.commits += 1;
      } else {
        acc.push({ date, commits: 1 });
      }
      return acc;
    }, [])
    .slice(-14); // Last 14 days

  return (
    <div className="App">
      <header>
        <h1>🔍 OmniAudit Dashboard</h1>
        <p>Universal Project Auditing & Monitoring</p>
      </header>

      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="card">
          <div className="card-icon">📊</div>
          <div>
            <h3>{data.summary.totalCommits}</h3>
            <p>Total Commits</p>
          </div>
        </div>
        <div className="card">
          <div className="card-icon">👥</div>
          <div>
            <h3>{data.summary.totalContributors}</h3>
            <p>Contributors</p>
          </div>
        </div>
        <div className="card">
          <div className="card-icon">⭐</div>
          <div>
            <h3>{data.summary.qualityScore.toFixed(1)}</h3>
            <p>Quality Score</p>
          </div>
        </div>
        <div className="card">
          <div className="card-icon">✅</div>
          <div>
            <h3>{data.summary.coverage > 0 ? data.summary.coverage.toFixed(1) + '%' : 'N/A'}</h3>
            <p>Test Coverage</p>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="charts">
        <div className="chart-container">
          <h2>Commit Activity (Last 14 Days)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={commitTimeline}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="commits" stroke="#8884d8" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-container">
          <h2>Top Contributors</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.contributors.slice(0, 10)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="commits" fill="#82ca9d" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Contributors Table */}
      <div className="table-container">
        <h2>Contributors</h2>
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Commits</th>
              <th>Insertions</th>
              <th>Deletions</th>
              <th>Lines Changed</th>
            </tr>
          </thead>
          <tbody>
            {data.contributors.slice(0, 10).map((contributor, idx) => (
              <tr key={idx}>
                <td>{contributor.name}</td>
                <td>{contributor.commits}</td>
                <td className="text-success">+{contributor.insertions}</td>
                <td className="text-danger">-{contributor.deletions}</td>
                <td>{contributor.lines_changed}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <footer>
        <button onClick={fetchDashboardData}>Refresh Data</button>
      </footer>
    </div>
  );
}

export default App;
