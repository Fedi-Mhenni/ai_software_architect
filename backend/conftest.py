"""Pytest configuration and fixtures."""
import sys
from pathlib import Path

# Add backend directory to Python path so modules can be imported
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))
