import json
import subprocess
import sys
from halo_research_gateway import __version__


def test_package_imports():
    """Test that the package imports correctly"""
    import halo_research_gateway
    assert halo_research_gateway.__version__ == "0.1.0"


def test_main_module():
    """Test that the main module prints correct JSON"""
    result = subprocess.run(
        [sys.executable, "-m", "halo_research_gateway"],
        capture_output=True,
        text=True,
        check=True
    )
    
    # Parse the output as JSON
    data = json.loads(result.stdout.strip())
    
    assert data["service"] == "halo-research-gateway"
    assert data["version"] == "0.1.0" 
    assert data["status"] == "scaffold"


def test_version_matches_pyproject():
    """Test that the version in __init__.py matches pyproject.toml"""
    assert __version__ == "0.1.0"
