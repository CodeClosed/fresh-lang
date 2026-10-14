"""Unit and integration test suite for Fresh Module and Import System."""

import pytest

from fresh.common.errors import FreshSyntaxError
from fresh.pipeline import run_source


def test_import_function_across_files(tmp_path, run_fresh):
    # Create math_utils.fresh
    math_file = tmp_path / "math_utils.fresh"
    math_file.write_text("""
    fn square(x: int) -> int {
        return x * x;
    }
    """, encoding="utf-8")

    # Create main.fresh importing math_utils.fresh
    main_file = tmp_path / "main.fresh"
    main_file.write_text("""
    import "math_utils.fresh";
    println(square(5));
    """, encoding="utf-8")

    run_source(main_file.read_text(encoding="utf-8"), filename=str(main_file))
    # Capture output via run_fresh
    captured = run_fresh(f"""
    import "{math_file.as_posix()}";
    println(square(5));
    """)
    assert captured.strip() == "25"


def test_import_variables_and_structs(tmp_path, run_fresh):
    models_file = tmp_path / "models.fresh"
    models_file.write_text("""
    struct User { id: int, name: string }
    let default_id = 100;
    """, encoding="utf-8")

    captured = run_fresh(f"""
    import "{models_file.as_posix()}";
    let u = User {{ id: default_id, name: "Alice" }};
    println(u.name);
    println(u.id);
    """)
    assert captured.strip().splitlines() == ["Alice", "100"]


def test_circular_import_detection(tmp_path):
    a_file = tmp_path / "a.fresh"
    b_file = tmp_path / "b.fresh"

    a_file.write_text('import "b.fresh";\nlet a = 1;', encoding="utf-8")
    b_file.write_text('import "a.fresh";\nlet b = 2;', encoding="utf-8")

    with pytest.raises(FreshSyntaxError) as excinfo:
        run_source(a_file.read_text(encoding="utf-8"), filename=str(a_file))

    err_msg = str(excinfo.value)
    assert "[E4001]" in err_msg
    assert "Circular module dependency detected" in err_msg
