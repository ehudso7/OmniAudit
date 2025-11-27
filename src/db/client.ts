import { type Client, type InValue, createClient } from '@libsql/client';
import * as dotenv from 'dotenv';

dotenv.config();

export class DatabaseClient {
  private client: Client;
  private static instance: DatabaseClient;

  private constructor() {
    this.client = createClient({
      url: process.env.TURSO_URL!,
      authToken: process.env.TURSO_TOKEN!,
    });
  }

  static getInstance(): DatabaseClient {
    if (!DatabaseClient.instance) {
      DatabaseClient.instance = new DatabaseClient();
    }
    return DatabaseClient.instance;
  }

  getClient(): Client {
    return this.client;
  }

  async close(): Promise<void> {
    this.client.close();
  }

  // User operations
  async createUser(data: {
    email: string;
    name?: string;
    github_id?: string;
    tier?: 'free' | 'pro' | 'enterprise';
  }) {
    const result = await this.client.execute({
      sql: `
        INSERT INTO users (email, name, github_id, tier)
        VALUES (?, ?, ?, ?)
        RETURNING *
      `,
      args: [data.email, data.name || null, data.github_id || null, data.tier || 'free'],
    });
    return result.rows[0];
  }

  async getUserByEmail(email: string) {
    const result = await this.client.execute({
      sql: 'SELECT * FROM users WHERE email = ?',
      args: [email],
    });
    return result.rows[0];
  }

  async getUserById(id: string) {
    const result = await this.client.execute({
      sql: 'SELECT * FROM users WHERE id = ?',
      args: [id],
    });
    return result.rows[0];
  }

  async updateUserCredits(userId: string, credits: number) {
    await this.client.execute({
      sql: 'UPDATE users SET credits = credits + ? WHERE id = ?',
      args: [credits, userId],
    });
  }

  // Skill operations
  async createSkill(data: {
    skill_id: string;
    version: string;
    user_id: string;
    definition: Record<string, unknown>;
    is_public?: boolean;
  }) {
    const result = await this.client.execute({
      sql: `
        INSERT INTO skills (skill_id, version, user_id, definition, is_public)
        VALUES (?, ?, ?, ?, ?)
        RETURNING *
      `,
      args: [
        data.skill_id,
        data.version,
        data.user_id,
        JSON.stringify(data.definition),
        data.is_public ? 1 : 0,
      ],
    });
    return result.rows[0];
  }

  async getSkill(skill_id: string, version?: string) {
    const sql = version
      ? 'SELECT * FROM skills WHERE skill_id = ? AND version = ?'
      : 'SELECT * FROM skills WHERE skill_id = ? ORDER BY created_at DESC LIMIT 1';
    const args = version ? [skill_id, version] : [skill_id];

    const result = await this.client.execute({ sql, args });
    return result.rows[0];
  }

  async listSkills(filters?: {
    is_public?: boolean;
    user_id?: string;
    category?: string;
    language?: string;
    limit?: number;
    offset?: number;
  }) {
    const conditions: string[] = [];
    const args: InValue[] = [];

    if (filters?.is_public !== undefined) {
      conditions.push('is_public = ?');
      args.push(filters.is_public ? 1 : 0);
    }

    if (filters?.user_id) {
      conditions.push('user_id = ?');
      args.push(filters.user_id);
    }

    if (filters?.category) {
      conditions.push("json_extract(definition, '$.metadata.category') = ?");
      args.push(filters.category);
    }

    if (filters?.language) {
      conditions.push("json_extract(definition, '$.metadata.language') LIKE ?");
      args.push(`%${filters.language}%`);
    }

    const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';
    const limit = filters?.limit || 50;
    const offset = filters?.offset || 0;

    args.push(limit, offset);

    const result = await this.client.execute({
      sql: `
        SELECT * FROM skills
        ${whereClause}
        ORDER BY downloads_count DESC, rating_avg DESC
        LIMIT ? OFFSET ?
      `,
      args,
    });

    return result.rows;
  }

  async incrementSkillDownloads(skill_id: string) {
    await this.client.execute({
      sql: 'UPDATE skills SET downloads_count = downloads_count + 1 WHERE skill_id = ?',
      args: [skill_id],
    });
  }

  // Execution operations
  async createExecution(data: {
    execution_id: string;
    skill_id: string;
    user_id?: string;
    success: boolean;
    execution_time_ms: number;
    input_hash?: string;
    result?: Record<string, unknown>;
    error_message?: string;
    metadata?: Record<string, unknown>;
  }) {
    const result = await this.client.execute({
      sql: `
        INSERT INTO skill_executions (
          execution_id, skill_id, user_id, success, execution_time_ms,
          input_hash, result, error_message, metadata
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        RETURNING *
      `,
      args: [
        data.execution_id,
        data.skill_id,
        data.user_id || null,
        data.success ? 1 : 0,
        data.execution_time_ms,
        data.input_hash || null,
        data.result ? JSON.stringify(data.result) : null,
        data.error_message || null,
        data.metadata ? JSON.stringify(data.metadata) : '{}',
      ],
    });
    return result.rows[0];
  }

  async getExecutionHistory(skill_id: string, limit = 100) {
    const result = await this.client.execute({
      sql: `
        SELECT * FROM skill_executions
        WHERE skill_id = ?
        ORDER BY created_at DESC
        LIMIT ?
      `,
      args: [skill_id, limit],
    });
    return result.rows;
  }

  // Analytics operations
  async updateAnalytics(
    skill_id: string,
    data: {
      executions_count?: number;
      success_count?: number;
      failure_count?: number;
      avg_execution_time_ms?: number;
      total_execution_time_ms?: number;
    },
  ) {
    const date = new Date().toISOString().split('T')[0];

    await this.client.execute({
      sql: `
        INSERT INTO skill_analytics (
          skill_id, date, executions_count, success_count, failure_count,
          avg_execution_time_ms, total_execution_time_ms
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(skill_id, date) DO UPDATE SET
          executions_count = executions_count + excluded.executions_count,
          success_count = success_count + excluded.success_count,
          failure_count = failure_count + excluded.failure_count,
          avg_execution_time_ms = (
            (avg_execution_time_ms * executions_count + excluded.avg_execution_time_ms * excluded.executions_count)
            / (executions_count + excluded.executions_count)
          ),
          total_execution_time_ms = total_execution_time_ms + excluded.total_execution_time_ms
      `,
      args: [
        skill_id,
        date,
        data.executions_count || 1,
        data.success_count || 0,
        data.failure_count || 0,
        data.avg_execution_time_ms || 0,
        data.total_execution_time_ms || 0,
      ],
    });
  }

  // Cache operations
  async getCache(skill_id: string, input_hash: string) {
    const result = await this.client.execute({
      sql: `
        SELECT * FROM cache
        WHERE skill_id = ? AND input_hash = ? AND expires_at > datetime('now')
      `,
      args: [skill_id, input_hash],
    });
    return result.rows[0];
  }

  async setCache(
    skill_id: string,
    input_hash: string,
    result: Record<string, unknown>,
    ttl_seconds: number,
  ) {
    const expires_at = new Date(Date.now() + ttl_seconds * 1000).toISOString();

    await this.client.execute({
      sql: `
        INSERT INTO cache (id, skill_id, input_hash, result, expires_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(skill_id, input_hash) DO UPDATE SET
          result = excluded.result,
          expires_at = excluded.expires_at
      `,
      args: [`${skill_id}:${input_hash}`, skill_id, input_hash, JSON.stringify(result), expires_at],
    });
  }

  async cleanExpiredCache() {
    await this.client.execute({
      sql: "DELETE FROM cache WHERE expires_at <= datetime('now')",
      args: [],
    });
  }

  // Project operations
  async createProject(data: {
    user_id: string;
    name: string;
    description?: string;
    repository_url?: string;
    language?: string;
    framework?: string;
  }) {
    const result = await this.client.execute({
      sql: `
        INSERT INTO projects (user_id, name, description, repository_url, language, framework)
        VALUES (?, ?, ?, ?, ?, ?)
        RETURNING *
      `,
      args: [
        data.user_id,
        data.name,
        data.description || null,
        data.repository_url || null,
        data.language || null,
        data.framework || null,
      ],
    });
    return result.rows[0];
  }

  async listProjects(user_id: string) {
    const result = await this.client.execute({
      sql: `
        SELECT * FROM projects
        WHERE user_id = ?
        ORDER BY updated_at DESC
      `,
      args: [user_id],
    });
    return result.rows;
  }

  // Audit log
  async createAuditLog(data: {
    user_id?: string;
    action: string;
    resource_type: string;
    resource_id?: string;
    changes?: Record<string, unknown>;
    ip_address?: string;
    user_agent?: string;
  }) {
    await this.client.execute({
      sql: `
        INSERT INTO audit_log (
          user_id, action, resource_type, resource_id, changes, ip_address, user_agent
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
      `,
      args: [
        data.user_id || null,
        data.action,
        data.resource_type,
        data.resource_id || null,
        data.changes ? JSON.stringify(data.changes) : null,
        data.ip_address || null,
        data.user_agent || null,
      ],
    });
  }
}

export const db = DatabaseClient.getInstance();
