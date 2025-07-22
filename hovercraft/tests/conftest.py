"""Pytest configuration and fixtures."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir)
        
        # Create .vscode directory
        vscode_dir = workspace_path / ".vscode"
        vscode_dir.mkdir()
        
        # Create .data directory
        data_dir = workspace_path / ".data"
        data_dir.mkdir()
        
        yield workspace_path


@pytest.fixture
def sample_csv_content():
    """Sample CSV content for testing."""
    return """keyword,description,category,example
print,Python print function,function,print("hello")
list,Python list type,type,my_list = []
dict,Python dictionary type,type,my_dict = {}
test_.*,Test function pattern,function,test_something(),true"""


@pytest.fixture
def sample_json_content():
    """Sample JSON content for testing."""
    return [
        {
            "keyword": "console",
            "description": "JavaScript console object",
            "category": "object",
            "example": "console.log('hello')"
        },
        {
            "keyword": "function",
            "description": "JavaScript function keyword",
            "category": "keyword"
        },
        {
            "keyword": "var.*",
            "description": "Variable declaration pattern",
            "category": "pattern",
            "is_regex": True
        }
    ]