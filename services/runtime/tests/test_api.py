import pytest
from fastapi.testclient import TestClient


def test_api_imports():
    """Test that API modules can be imported."""
    from services.runtime.src.api import agents, health
    
    assert agents.router is not None
    assert health.router is not None
    assert agents.executor is not None


def test_main_import():
    """Test that main module can be imported."""
    from services.runtime.src.main import app
    
    assert app is not None
    assert app.title == "Agent Runtime Service"
    assert app.version == "1.0.0"
