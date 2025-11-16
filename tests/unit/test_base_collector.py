"""Unit tests for BaseCollector."""

import pytest
from datetime import datetime
from src.omniaudit.collectors.base import (
    BaseCollector,
    CollectorError,
    ConfigurationError
)


class MockCollector(BaseCollector):
    """Mock collector for testing."""

    @property
    def name(self) -> str:
        return "mock_collector"

    @property
    def version(self) -> str:
        return "1.0.0"

    def _validate_config(self) -> None:
        if "required_field" not in self.config:
            raise ConfigurationError("required_field is missing")

    def collect(self):
        return self._create_response({"test": "data"})


def test_base_collector_initialization():
    """Test collector initializes with valid config."""
    config = {"required_field": "value"}
    collector = MockCollector(config)
    assert collector.config == config


def test_base_collector_validation_error():
    """Test collector raises error on invalid config."""
    with pytest.raises(ConfigurationError):
        MockCollector({})


def test_base_collector_properties():
    """Test collector properties."""
    collector = MockCollector({"required_field": "value"})
    assert collector.name == "mock_collector"
    assert collector.version == "1.0.0"


def test_create_response_format():
    """Test response format is standardized."""
    collector = MockCollector({"required_field": "value"})
    response = collector.collect()

    assert "collector" in response
    assert "version" in response
    assert "timestamp" in response
    assert "data" in response
    assert "metadata" in response

    assert response["collector"] == "mock_collector"
    assert response["version"] == "1.0.0"
    assert response["data"] == {"test": "data"}


def test_timestamp_format():
    """Test timestamp is ISO 8601 format."""
    collector = MockCollector({"required_field": "value"})
    response = collector.collect()

    # Should be parseable as ISO format
    timestamp = datetime.fromisoformat(response["timestamp"].replace("Z", "+00:00"))
    assert isinstance(timestamp, datetime)
