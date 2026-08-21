"""Integration test suite executing all official Fresh example programs."""

from pathlib import Path

import pytest

from fresh.pipeline import run_source

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
EXAMPLE_FILES = sorted(list(EXAMPLES_DIR.glob("*.fresh")))


@pytest.mark.parametrize("example_path", EXAMPLE_FILES, ids=lambda p: p.name)
def test_official_example_execution(example_path: Path):
    """Ensure every official example parses, type checks, and executes without errors."""
    source = example_path.read_text(encoding="utf-8")
    run_source(source, filename=str(example_path))
