"""CLI integration test suite for Fresh."""

import sys
from unittest.mock import patch

import pytest

from fresh.cli import main


def test_cli_check_valid_file(tmp_path):
    f = tmp_path / "valid.fresh"
    f.write_text("let x = 42; println(x);", encoding="utf-8")

    with patch.object(sys, "argv", ["fresh", "check", str(f)]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 0


def test_cli_check_invalid_file(tmp_path):
    f = tmp_path / "invalid.fresh"
    f.write_text("let x: int = \"hello\";", encoding="utf-8")

    with patch.object(sys, "argv", ["fresh", "check", str(f)]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1


def test_cli_fmt_check_mode(tmp_path):
    f = tmp_path / "unformatted.fresh"
    f.write_text("let   x =   42 ;", encoding="utf-8")

    # Should exit 1 in --check mode
    with patch.object(sys, "argv", ["fresh", "fmt", str(f), "--check"]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1

    # Should format file in normal mode
    with patch.object(sys, "argv", ["fresh", "fmt", str(f)]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 0

    assert f.read_text(encoding="utf-8").strip() == "let x = 42;"


def test_cli_panic_boundary_ice(tmp_path, capsys):
    f = tmp_path / "test.fresh"
    f.write_text("let x = 1;", encoding="utf-8")

    with patch("fresh.cli.run_source", side_effect=TypeError("Unexpected compiler crash")):
        with patch.object(sys, "argv", ["fresh", "run", str(f)]):
            with pytest.raises(SystemExit) as excinfo:
                main()
            assert excinfo.value.code == 70

        captured = capsys.readouterr()
        assert "internal compiler error (ICE)" in captured.err

