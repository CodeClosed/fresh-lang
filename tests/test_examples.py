"""Integration test suite executing all official Fresh example programs."""

from pathlib import Path

import pytest

from fresh.pipeline import run_source

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
EXAMPLE_FILES = sorted(list(EXAMPLES_DIR.glob("*.fresh")))
if not EXAMPLE_FILES:
    root_fresh = Path(__file__).parent.parent / "all_features.fresh"
    if root_fresh.exists():
        EXAMPLE_FILES = [root_fresh]


@pytest.mark.parametrize("example_path", EXAMPLE_FILES, ids=lambda p: p.name)
def test_official_example_execution(example_path: Path):
    """Ensure every official example parses, type checks, and executes without errors."""
    source = example_path.read_text(encoding="utf-8")
    run_source(source, filename=str(example_path))


def test_stress_suite_shows_distinct_operator_precedence(tmp_path, monkeypatch, capsys):
    """The live example must show the difference made by parentheses."""
    monkeypatch.chdir(tmp_path)
    example_path = EXAMPLES_DIR / "07_stress_suite.fresh"
    run_source(example_path.read_text(encoding="utf-8"), filename=str(example_path))
    output = capsys.readouterr().out
    assert "1 + 2 * 3 = 7" in output
    assert "(1 + 2) * 3 = 9" in output
