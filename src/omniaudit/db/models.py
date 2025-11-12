"""
Database Models

SQLAlchemy models for all entities.
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, Float, JSON,
    ForeignKey, Boolean, Text, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional
import uuid

from .base import Base


class Project(Base):
    """
    Project entity.

    Represents a software project being audited.
    """
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    repository_url = Column(String(512), nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    audits = relationship("Audit", back_populates="project", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="project", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('ix_projects_name', 'name'),
    )

    def __repr__(self):
        return f"<Project(id={self.id}, name={self.name})>"


class Audit(Base):
    """
    Audit run entity.

    Represents a single audit execution with collectors and analyzers.
    """
    __tablename__ = "audits"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)

    status = Column(String(20), nullable=False)  # running, completed, failed
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Configuration
    config = Column(JSON, nullable=True)

    # Results
    results = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="audits")
    metrics = relationship("Metric", back_populates="audit", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('ix_audits_project_id', 'project_id'),
        Index('ix_audits_status', 'status'),
        Index('ix_audits_started_at', 'started_at'),
    )

    def __repr__(self):
        return f"<Audit(id={self.id}, status={self.status})>"


class Metric(Base):
    """
    Time-series metric entity.

    Stores individual metrics from audits for historical tracking.
    Uses TimescaleDB for efficient time-series queries.
    """
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    audit_id = Column(String(36), ForeignKey("audits.id"), nullable=False)

    # Metric details
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(50), nullable=True)

    # Categorization
    category = Column(String(50), nullable=False)  # git, quality, performance
    subcategory = Column(String(50), nullable=True)

    # Tags for filtering
    tags = Column(JSON, nullable=True)

    # Timestamp
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    audit = relationship("Audit", back_populates="metrics")

    # Indexes
    __table_args__ = (
        Index('ix_metrics_audit_id', 'audit_id'),
        Index('ix_metrics_metric_name', 'metric_name'),
        Index('ix_metrics_timestamp', 'timestamp'),
        Index('ix_metrics_category', 'category'),
    )

    def __repr__(self):
        return f"<Metric(name={self.metric_name}, value={self.metric_value})>"


class Alert(Base):
    """
    Alert configuration entity.

    Defines alert rules and notification settings.
    """
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Alert condition
    metric_name = Column(String(100), nullable=False)
    condition = Column(String(20), nullable=False)  # gt, lt, eq, gte, lte
    threshold = Column(Float, nullable=False)

    # Notification settings
    enabled = Column(Boolean, default=True)
    notification_channels = Column(JSON, nullable=False)  # ["email", "slack"]
    notification_config = Column(JSON, nullable=True)

    # Timing
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    last_triggered_at = Column(DateTime, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="alerts")

    # Indexes
    __table_args__ = (
        Index('ix_alerts_project_id', 'project_id'),
        Index('ix_alerts_metric_name', 'metric_name'),
        Index('ix_alerts_enabled', 'enabled'),
    )

    def __repr__(self):
        return f"<Alert(name={self.name}, metric={self.metric_name})>"
