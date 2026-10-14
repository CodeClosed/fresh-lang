"""Test suite for Fresh project initialization and package build."""

import sys
from unittest.mock import patch

import pytest

from fresh.cli import main
from fresh.package import PackageManager


def test_package_init(tmp_path):
    project_dir = PackageManager.init_project("sample_app", tmp_path)
    assert (project_dir / "fresh.toml").exists()
    assert (project_dir / "src" / "main.fresh").exists()
    assert (project_dir / "tests" / "test_basic.fresh").exists()

    manifest = (project_dir / "fresh.toml").read_text(encoding="utf-8")
    assert 'name = "sample_app"' in manifest
    assert 'version = "0.1.0"' in manifest


def test_package_build(tmp_path):
    project_dir = PackageManager.init_project("sample_build_app", tmp_path)
    output = PackageManager.build_project(project_dir)

    assert output.exists()
    if sys.platform.startswith("win"):
        assert output.suffix in (".c", ".exe")
    else:
        assert output.suffix in (".c", "")


def test_cli_init_and_build(tmp_path):
    with patch.object(sys, "argv", ["fresh", "init", "cli_app", "--dir", str(tmp_path)]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 0

    app_dir = tmp_path / "cli_app"
    assert (app_dir / "fresh.toml").exists()

    with patch.object(sys, "argv", ["fresh", "build", str(app_dir)]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 0


def test_package_custom_entry_resolution(tmp_path):
    project_dir = tmp_path / "custom_app"
    project_dir.mkdir()
    src_dir = project_dir / "src"
    src_dir.mkdir()

    manifest_content = """[package]
name = "custom_app"
version = "0.1.0"
entry = "src/custom_main.fresh"
"""
    (project_dir / "fresh.toml").write_text(manifest_content, encoding="utf-8")
    (src_dir / "custom_main.fresh").write_text("println(123);", encoding="utf-8")

    out = PackageManager.build_project(project_dir)
    assert out.exists()
    assert (project_dir / "build" / "main.c").exists()


def test_package_manifest_path_traversal_rejection(tmp_path):
    project_dir = tmp_path / "insecure_app"
    project_dir.mkdir()
    manifest_content = """[package]
name = "insecure_app"
entry = "../../../secret.fresh"
"""
    (project_dir / "fresh.toml").write_text(manifest_content, encoding="utf-8")

    with pytest.raises(Exception) as excinfo:
        PackageManager.build_project(project_dir)
    assert "Security error" in str(excinfo.value)


