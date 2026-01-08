"""
Smoke tests for DIET_APP
Verifies basic imports and package structure.
"""
import sys
from pathlib import Path


def test_core_package_exists():
    """Test that core package can be imported."""
    import core
    assert core is not None


def test_app_package_exists():
    """Test that app package can be imported."""
    import app
    assert app is not None


def test_app_main_imports():
    """Test that app.main module can be imported."""
    from app import main
    assert main is not None
    assert hasattr(main, "APP_VERSION")
    assert hasattr(main, "APP_TITLE")
    assert hasattr(main, "main")


def test_app_version():
    """Test that app version is defined."""
    from app.main import APP_VERSION
    assert APP_VERSION == "0.10.0"


def test_app_title():
    """Test that app title is defined."""
    from app.main import APP_TITLE
    assert APP_TITLE == "DIET_APP"


def test_project_structure():
    """Test that required directories exist."""
    project_root = Path(__file__).parent.parent

    required_dirs = [
        "app",
        "core",
        "tests",
        "configs",
        "data",
        "docs",
        "scripts"
    ]

    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"Directory '{dir_name}' should exist"
        assert dir_path.is_dir(), f"'{dir_name}' should be a directory"
