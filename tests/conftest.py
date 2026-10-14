"""Pytest configuration and test runner fixtures for Fresh."""

import io
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fresh.pipeline import run_source


@pytest.fixture
def run_fresh():
    """Fixture to execute Fresh source string and return captured stdout string."""
    def runner(source: str) -> str:
        buffer = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = buffer
            run_source(source, filename="<test>")
        finally:
            sys.stdout = old_stdout
        return buffer.getvalue()

    return runner



