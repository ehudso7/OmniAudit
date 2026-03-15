"""
Database Models

SQLAlchemy models for all OmniAudit entities including
users, organizations, repositories, reviews, browser runs, and release policies.
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, Float, JSON,
    ForeignKey, Boolean, Text, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from .base import Base


# --- User and organization models ---

class User(Base):
    """User account."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(320), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=True)
    role = Column(String(20), nullable=False, default="member")  # admin, member, viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    last_login_at = Column(DateTime, nullable=True)

    # Billing
    plan = Column(String(20), nullable=False, default="free")  # free, pro, team, enterprise
    stripe_customer_id = Column(String(255), nullable=True)
    subscription_status = Column(String(20), nullable=True)  # active, past_due, canceled

    # Notification preferences
    notify_run_complete = Column(Boolean, default=True)
    notify_release_blocked = Column(Boolean, default=True)
    notify_critical_issues = Column(Boolean, default=True)

    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_users_email', 'email'),
    )


class ApiKey(Base):
    """API key for programmatic access."""
    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    key_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False, default="default")
    prefix = Column(String(10), nullable=False)  # First chars for identification
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="api_keys")

    __table_args__ = (
        Index('ix_api_keys_user_id', 'user_id'),
        Index('ix_api_keys_key_hash', 'key_hash'),
    )


# --- Existing models ---

class Project(Base):
    """Software project being audited."""
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    repository_url = Column(String(512), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    audits = relationship("Audit", back_populates="project", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_projects_name', 'name'),
    )


class Audit(Base):
    """Single audit execution with collectors and analyzers."""
    __tablename__ = "audits"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    status = Column(String(20), nullable=False)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    config = Column(JSON, nullable=True)
    results = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)

    project = relationship("Project", back_populates="audits")
    metrics = relationship("Metric", back_populates="audit", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_audits_project_id', 'project_id'),
        Index('ix_audits_status', 'status'),
        Index('ix_audits_started_at', 'started_at'),
    )


class Metric(Base):
    """Time-series metric from audits."""
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    audit_id = Column(String(36), ForeignKey("audits.id"), nullable=False)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(50), nullable=True)
    category = Column(String(50), nullable=False)
    subcategory = Column(String(50), nullable=True)
    tags = Column(JSON, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    audit = relationship("Audit", back_populates="metrics")

    __table_args__ = (
        Index('ix_metrics_audit_id', 'audit_id'),
        Index('ix_metrics_metric_name', 'metric_name'),
        Index('ix_metrics_timestamp', 'timestamp'),
        Index('ix_metrics_category', 'category'),
    )


class Alert(Base):
    """Alert configuration for metric thresholds."""
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    metric_name = Column(String(100), nullable=False)
    condition = Column(String(20), nullable=False)
    threshold = Column(Float, nullable=False)
    enabled = Column(Boolean, default=True)
    notification_channels = Column(JSON, nullable=False)
    notification_config = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    last_triggered_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="alerts")

    __table_args__ = (
        Index('ix_alerts_project_id', 'project_id'),
        Index('ix_alerts_metric_name', 'metric_name'),
        Index('ix_alerts_enabled', 'enabled'),
    )


# --- Repository and review models ---

class Repository(Base):
    """Connected GitHub repository."""
    __tablename__ = "repositories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    owner = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    full_name = Column(String(512), nullable=False, unique=True)
    url = Column(String(512), nullable=False)
    installation_id = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False, default="active")
    default_target_url = Column(String(1024), nullable=True)
    default_environment = Column(String(50), nullable=True, default="preview")
    connected_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    reviews = relationship("Review", back_populates="repository", cascade="all, delete-orphan")
    browser_runs = relationship("BrowserRun", back_populates="repository", cascade="all, delete-orphan")
    release_policies = relationship("ReleasePolicy", back_populates="repository", cascade="all, delete-orphan")
    audit_presets = relationship("AuditPreset", back_populates="repository", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_repositories_full_name', 'full_name'),
        Index('ix_repositories_owner', 'owner'),
        Index('ix_repositories_user_id', 'user_id'),
    )


class Review(Base):
    """PR review record."""
    __tablename__ = "reviews"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String(36), ForeignKey("repositories.id"), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    repo = Column(String(512), nullable=False)
    owner = Column(String(255), nullable=False)
    repo_name = Column(String(255), nullable=False)
    pr_number = Column(Integer, nullable=False)
    title = Column(String(512), nullable=False)
    author = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    issues_found = Column(Integer, default=0)
    security_issues = Column(Integer, default=0)
    performance_issues = Column(Integer, default=0)
    quality_issues = Column(Integer, default=0)
    suggestions = Column(Integer, default=0)
    action = Column(String(30), nullable=False, default="COMMENT")
    comments = Column(JSON, nullable=True)
    reviewed_at = Column(DateTime, server_default=func.now())
    commit_sha = Column(String(40), nullable=True)
    branch = Column(String(255), nullable=True)

    repository = relationship("Repository", back_populates="reviews")

    __table_args__ = (
        Index('ix_reviews_repo', 'repo'),
        Index('ix_reviews_reviewed_at', 'reviewed_at'),
        Index('ix_reviews_repository_id', 'repository_id'),
        Index('ix_reviews_user_id', 'user_id'),
    )


# --- Browser verification models ---

class BrowserRun(Base):
    """Browser verification run."""
    __tablename__ = "browser_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String(36), ForeignKey("repositories.id"), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    target_url = Column(String(1024), nullable=False)
    environment = Column(String(50), nullable=True, default="preview")
    branch = Column(String(255), nullable=True)
    commit_sha = Column(String(40), nullable=True)
    pr_number = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    viewport_width = Column(Integer, default=1280)
    viewport_height = Column(Integer, default=720)
    device = Column(String(100), nullable=True)
    journeys = Column(JSON, nullable=True)
    auth_config = Column(JSON, nullable=True)
    release_gate = Column(Boolean, default=False)
    correlation_id = Column(String(36), nullable=True)

    # Results
    score = Column(Integer, nullable=True)
    summary = Column(Text, nullable=True)
    findings_count = Column(Integer, default=0)
    security_findings = Column(Integer, default=0)
    performance_findings = Column(Integer, default=0)
    accessibility_findings = Column(Integer, default=0)
    console_errors = Column(Integer, default=0)
    network_failures = Column(Integer, default=0)
    blocking_verdict = Column(String(20), nullable=True)
    blocking_reasons = Column(JSON, nullable=True)

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    duration_ms = Column(Integer, nullable=True)
    timeout_ms = Column(Integer, default=60000)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=1)

    repository = relationship("Repository", back_populates="browser_runs")
    checks = relationship("BrowserCheck", back_populates="browser_run", cascade="all, delete-orphan")
    artifacts = relationship("BrowserArtifact", back_populates="browser_run", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_browser_runs_status', 'status'),
        Index('ix_browser_runs_repository_id', 'repository_id'),
        Index('ix_browser_runs_created_at', 'created_at'),
        Index('ix_browser_runs_user_id', 'user_id'),
        Index('ix_browser_runs_correlation_id', 'correlation_id'),
    )


class BrowserCheck(Base):
    """Individual check within a browser run."""
    __tablename__ = "browser_checks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    browser_run_id = Column(String(36), ForeignKey("browser_runs.id"), nullable=False)
    journey = Column(String(255), nullable=False)
    check_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    severity = Column(String(20), nullable=True)
    category = Column(String(50), nullable=True)
    message = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)
    selector = Column(String(512), nullable=True)
    url = Column(String(1024), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    browser_run = relationship("BrowserRun", back_populates="checks")

    __table_args__ = (
        Index('ix_browser_checks_run_id', 'browser_run_id'),
        Index('ix_browser_checks_status', 'status'),
        Index('ix_browser_checks_category', 'category'),
    )


class BrowserArtifact(Base):
    """Artifact from a browser verification run."""
    __tablename__ = "browser_artifacts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    browser_run_id = Column(String(36), ForeignKey("browser_runs.id"), nullable=False)
    artifact_type = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    storage_backend = Column(String(20), nullable=False, default="local")  # local, s3
    file_path = Column(String(1024), nullable=True)
    storage_key = Column(String(1024), nullable=True)  # S3 key or equivalent
    content_type = Column(String(100), nullable=True)
    size_bytes = Column(Integer, nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    browser_run = relationship("BrowserRun", back_populates="artifacts")

    __table_args__ = (
        Index('ix_browser_artifacts_run_id', 'browser_run_id'),
        Index('ix_browser_artifacts_type', 'artifact_type'),
    )


class ReleasePolicy(Base):
    """Release gate policy for a repository."""
    __tablename__ = "release_policies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String(36), ForeignKey("repositories.id"), nullable=False)
    name = Column(String(255), nullable=False)
    enabled = Column(Boolean, default=True)
    min_score = Column(Integer, nullable=True, default=70)
    block_on_security = Column(Boolean, default=True)
    block_on_accessibility = Column(Boolean, default=False)
    block_on_performance = Column(Boolean, default=False)
    max_critical_findings = Column(Integer, default=0)
    max_high_findings = Column(Integer, default=3)
    max_console_errors = Column(Integer, nullable=True)
    max_network_failures = Column(Integer, nullable=True)
    require_browser_run = Column(Boolean, default=False)
    required_journeys = Column(JSON, nullable=True)
    journeys_required = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    repository = relationship("Repository", back_populates="release_policies")

    __table_args__ = (
        Index('ix_release_policies_repository_id', 'repository_id'),
    )


class AuditPreset(Base):
    """Saved browser audit configuration preset."""
    __tablename__ = "audit_presets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String(36), ForeignKey("repositories.id"), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    name = Column(String(255), nullable=False)
    target_url = Column(String(1024), nullable=True)
    environment = Column(String(50), nullable=True, default="preview")
    viewport_width = Column(Integer, default=1280)
    viewport_height = Column(Integer, default=720)
    device = Column(String(100), nullable=True)
    journeys = Column(JSON, nullable=True)
    auth_config = Column(JSON, nullable=True)
    release_gate = Column(Boolean, default=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    repository = relationship("Repository", back_populates="audit_presets")

    __table_args__ = (
        Index('ix_audit_presets_repository_id', 'repository_id'),
        Index('ix_audit_presets_user_id', 'user_id'),
    )


class Notification(Base):
    """In-app notification record."""
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    event_type = Column(String(50), nullable=False)  # run_complete, release_blocked, critical_issue, repo_connected, pr_reviewed
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    severity = Column(String(20), nullable=True)  # info, warning, critical
    metadata = Column(JSON, nullable=True)  # link to related resource
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index('ix_notifications_user_id', 'user_id'),
        Index('ix_notifications_read', 'read'),
        Index('ix_notifications_created_at', 'created_at'),
    )
