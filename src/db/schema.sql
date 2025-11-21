-- OmniAudit Database Schema for Turso (LibSQL)

-- Users table
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  avatar_url TEXT,
  github_id TEXT UNIQUE,
  tier TEXT DEFAULT 'free' CHECK(tier IN ('free', 'pro', 'enterprise')),
  credits INTEGER DEFAULT 1000,
  api_key TEXT UNIQUE,
  settings JSON DEFAULT '{}',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  last_login_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_github_id ON users(github_id);
CREATE INDEX IF NOT EXISTS idx_users_api_key ON users(api_key);

-- Skills table
CREATE TABLE IF NOT EXISTS skills (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  skill_id TEXT NOT NULL,
  version TEXT NOT NULL,
  user_id TEXT NOT NULL,
  definition JSON NOT NULL,
  is_public INTEGER DEFAULT 0,
  is_verified INTEGER DEFAULT 0,
  downloads_count INTEGER DEFAULT 0,
  rating_avg REAL DEFAULT 0.0,
  rating_count INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  UNIQUE(skill_id, version)
);

CREATE INDEX IF NOT EXISTS idx_skills_skill_id ON skills(skill_id);
CREATE INDEX IF NOT EXISTS idx_skills_user_id ON skills(user_id);
CREATE INDEX IF NOT EXISTS idx_skills_public ON skills(is_public) WHERE is_public = 1;
CREATE INDEX IF NOT EXISTS idx_skills_downloads ON skills(downloads_count DESC);
CREATE INDEX IF NOT EXISTS idx_skills_rating ON skills(rating_avg DESC);

-- Skill executions table
CREATE TABLE IF NOT EXISTS skill_executions (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  execution_id TEXT UNIQUE NOT NULL,
  skill_id TEXT NOT NULL,
  user_id TEXT,
  success INTEGER NOT NULL,
  execution_time_ms INTEGER NOT NULL,
  input_hash TEXT,
  result JSON,
  error_message TEXT,
  metadata JSON DEFAULT '{}',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_executions_skill_id ON skill_executions(skill_id);
CREATE INDEX IF NOT EXISTS idx_executions_user_id ON skill_executions(user_id);
CREATE INDEX IF NOT EXISTS idx_executions_created_at ON skill_executions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_executions_success ON skill_executions(success);

-- Skill analytics table (aggregated data)
CREATE TABLE IF NOT EXISTS skill_analytics (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  skill_id TEXT NOT NULL,
  date TEXT NOT NULL,
  executions_count INTEGER DEFAULT 0,
  success_count INTEGER DEFAULT 0,
  failure_count INTEGER DEFAULT 0,
  avg_execution_time_ms REAL DEFAULT 0.0,
  total_execution_time_ms INTEGER DEFAULT 0,
  unique_users_count INTEGER DEFAULT 0,
  issues_found_count INTEGER DEFAULT 0,
  fixes_applied_count INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE,
  UNIQUE(skill_id, date)
);

CREATE INDEX IF NOT EXISTS idx_analytics_skill_date ON skill_analytics(skill_id, date DESC);

-- Skill ratings and reviews
CREATE TABLE IF NOT EXISTS skill_reviews (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  skill_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
  review TEXT,
  helpful_count INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  UNIQUE(skill_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_reviews_skill_id ON skill_reviews(skill_id);
CREATE INDEX IF NOT EXISTS idx_reviews_user_id ON skill_reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_reviews_rating ON skill_reviews(rating DESC);

-- Projects table (for user projects)
CREATE TABLE IF NOT EXISTS projects (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  user_id TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  repository_url TEXT,
  language TEXT,
  framework TEXT,
  active_skills JSON DEFAULT '[]',
  config JSON DEFAULT '{}',
  last_analyzed_at TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);

-- Analysis results table
CREATE TABLE IF NOT EXISTS analysis_results (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  project_id TEXT NOT NULL,
  execution_id TEXT NOT NULL,
  commit_sha TEXT,
  branch TEXT,
  files_analyzed INTEGER DEFAULT 0,
  issues_found INTEGER DEFAULT 0,
  warnings_found INTEGER DEFAULT 0,
  suggestions_found INTEGER DEFAULT 0,
  optimizations JSON DEFAULT '[]',
  metrics JSON DEFAULT '{}',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_analysis_project_id ON analysis_results(project_id);
CREATE INDEX IF NOT EXISTS idx_analysis_created_at ON analysis_results(created_at DESC);

-- API keys table
CREATE TABLE IF NOT EXISTS api_keys (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  user_id TEXT NOT NULL,
  key_hash TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  last_used_at TEXT,
  expires_at TEXT,
  is_active INTEGER DEFAULT 1,
  scopes JSON DEFAULT '["read", "execute"]',
  rate_limit_per_hour INTEGER DEFAULT 100,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);

-- Usage tracking table
CREATE TABLE IF NOT EXISTS usage_tracking (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  user_id TEXT NOT NULL,
  resource_type TEXT NOT NULL CHECK(resource_type IN ('execution', 'api_call', 'storage')),
  credits_used INTEGER DEFAULT 1,
  metadata JSON DEFAULT '{}',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_usage_user_id ON usage_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_created_at ON usage_tracking(created_at DESC);

-- Skill dependencies table
CREATE TABLE IF NOT EXISTS skill_dependencies (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  skill_id TEXT NOT NULL,
  dependency_skill_id TEXT NOT NULL,
  version_constraint TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE,
  UNIQUE(skill_id, dependency_skill_id)
);

CREATE INDEX IF NOT EXISTS idx_dependencies_skill_id ON skill_dependencies(skill_id);

-- Cache table (for caching analysis results)
CREATE TABLE IF NOT EXISTS cache (
  id TEXT PRIMARY KEY,
  skill_id TEXT NOT NULL,
  input_hash TEXT NOT NULL,
  result JSON NOT NULL,
  expires_at TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(skill_id, input_hash)
);

CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_cache_skill_hash ON cache(skill_id, input_hash);

-- Webhooks table
CREATE TABLE IF NOT EXISTS webhooks (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  user_id TEXT NOT NULL,
  project_id TEXT,
  url TEXT NOT NULL,
  secret TEXT NOT NULL,
  events JSON NOT NULL,
  is_active INTEGER DEFAULT 1,
  last_triggered_at TEXT,
  failure_count INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_webhooks_user_id ON webhooks(user_id);
CREATE INDEX IF NOT EXISTS idx_webhooks_project_id ON webhooks(project_id);

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  user_id TEXT NOT NULL,
  type TEXT NOT NULL,
  title TEXT NOT NULL,
  message TEXT NOT NULL,
  data JSON DEFAULT '{}',
  is_read INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read, created_at DESC);

-- Audit log table
CREATE TABLE IF NOT EXISTS audit_log (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  user_id TEXT,
  action TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  resource_id TEXT,
  changes JSON,
  ip_address TEXT,
  user_agent TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_log(resource_type, resource_id);

-- Triggers for updated_at
CREATE TRIGGER IF NOT EXISTS update_users_timestamp
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
  UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_skills_timestamp
AFTER UPDATE ON skills
FOR EACH ROW
BEGIN
  UPDATE skills SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_projects_timestamp
AFTER UPDATE ON projects
FOR EACH ROW
BEGIN
  UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_skill_reviews_timestamp
AFTER UPDATE ON skill_reviews
FOR EACH ROW
BEGIN
  UPDATE skill_reviews SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger to update skill rating average
CREATE TRIGGER IF NOT EXISTS update_skill_rating
AFTER INSERT ON skill_reviews
FOR EACH ROW
BEGIN
  UPDATE skills
  SET
    rating_avg = (
      SELECT AVG(rating)
      FROM skill_reviews
      WHERE skill_id = NEW.skill_id
    ),
    rating_count = (
      SELECT COUNT(*)
      FROM skill_reviews
      WHERE skill_id = NEW.skill_id
    )
  WHERE skill_id = NEW.skill_id;
END;
