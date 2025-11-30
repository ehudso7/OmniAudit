"""Unit tests for PluginManager."""

import pytest
from omniaudit.core.plugin_manager import PluginManager
from omniaudit.core.exceptions import PluginError, PluginLoadError
from omniaudit.collectors.git_collector import GitCollector


def test_plugin_manager_initialization():
    """Test plugin manager initializes correctly."""
    manager = PluginManager()
    assert len(manager._plugins) == 0
    assert len(manager._loaded_instances) == 0


def test_register_plugin_success():
    """Test successful plugin registration."""
    manager = PluginManager()
    manager.register_plugin(GitCollector)

    plugins = manager.list_plugins()
    assert len(plugins) >= 1
    assert any(p["name"] == "git_collector" for p in plugins)


def test_register_invalid_plugin():
    """Test registration fails for invalid plugin."""
    manager = PluginManager()

    with pytest.raises(PluginError):
        manager.register_plugin("not_a_class")


def test_load_plugin_success(tmp_path):
    """Test plugin loads successfully."""
    manager = PluginManager()
    manager.register_plugin(GitCollector)

    # Create temporary git repo for testing
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    (repo_path / ".git").mkdir()

    config = {"repo_path": str(repo_path)}
    manager.load_plugin("git_collector", config)

    assert manager.is_loaded("git_collector")


def test_load_unregistered_plugin():
    """Test loading unregistered plugin fails."""
    manager = PluginManager()

    with pytest.raises(PluginLoadError):
        manager.load_plugin("nonexistent", {})


def test_list_plugins():
    """Test listing registered plugins."""
    manager = PluginManager()
    manager.register_plugin(GitCollector)

    plugins = manager.list_plugins()

    assert len(plugins) >= 1
    git_plugin = next((p for p in plugins if p["name"] == "git_collector"), None)
    assert git_plugin is not None
    assert "version" in git_plugin
    assert "class" in git_plugin


def test_unload_plugin(tmp_path):
    """Test unloading a plugin."""
    manager = PluginManager()
    manager.register_plugin(GitCollector)

    # Create temporary git repo
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    (repo_path / ".git").mkdir()

    config = {"repo_path": str(repo_path)}
    manager.load_plugin("git_collector", config)
    assert manager.is_loaded("git_collector")

    manager.unload_plugin("git_collector")
    assert not manager.is_loaded("git_collector")
