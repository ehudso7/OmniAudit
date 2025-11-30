"""Unit tests for ConfigLoader."""

import pytest
import yaml
import json
from pathlib import Path
from omniaudit.core.config_loader import ConfigLoader
from omniaudit.core.exceptions import ConfigurationError


def test_config_loader_initialization():
    """Test config loader initializes."""
    loader = ConfigLoader()
    assert loader._config == {}


def test_load_yaml_config(tmp_path):
    """Test loading YAML configuration."""
    config_file = tmp_path / "config.yaml"
    config_data = {
        "database": {
            "host": "localhost",
            "port": 5432
        }
    }

    with open(config_file, 'w') as f:
        yaml.dump(config_data, f)

    loader = ConfigLoader()
    loaded = loader.load(str(config_file))

    assert loaded == config_data
    assert loader.get("database.host") == "localhost"


def test_load_json_config(tmp_path):
    """Test loading JSON configuration."""
    config_file = tmp_path / "config.json"
    config_data = {"api": {"port": 8000}}

    with open(config_file, 'w') as f:
        json.dump(config_data, f)

    loader = ConfigLoader()
    loaded = loader.load(str(config_file))

    assert loaded == config_data


def test_load_nonexistent_file():
    """Test loading nonexistent file raises error."""
    loader = ConfigLoader()

    with pytest.raises(ConfigurationError, match="not found"):
        loader.load("nonexistent.yaml")


def test_get_with_dot_notation():
    """Test getting nested values with dot notation."""
    loader = ConfigLoader()
    loader._config = {
        "database": {
            "host": "localhost",
            "credentials": {
                "username": "admin"
            }
        }
    }

    assert loader.get("database.host") == "localhost"
    assert loader.get("database.credentials.username") == "admin"
    assert loader.get("nonexistent", "default") == "default"


def test_get_from_environment(monkeypatch):
    """Test getting values from environment variables."""
    monkeypatch.setenv("DATABASE_HOST", "prod.example.com")

    loader = ConfigLoader()
    loader._config = {"database": {"host": "localhost"}}

    # Environment variable should override config
    assert loader.get("database.host") == "prod.example.com"


def test_set_value():
    """Test setting configuration values."""
    loader = ConfigLoader()
    loader.set("database.host", "newhost")

    assert loader.get("database.host") == "newhost"


def test_save_config(tmp_path):
    """Test saving configuration to file."""
    output_file = tmp_path / "output.yaml"

    loader = ConfigLoader()
    loader.set("test.value", 123)
    loader.save(str(output_file))

    # Verify file was created
    assert output_file.exists()

    # Verify content
    with open(output_file) as f:
        data = yaml.safe_load(f)

    assert data["test"]["value"] == 123


def test_to_dict():
    """Test converting config to dictionary."""
    loader = ConfigLoader()
    loader.set("key1", "value1")
    loader.set("key2", "value2")

    config_dict = loader.to_dict()
    assert "key1" in config_dict
    assert "key2" in config_dict
