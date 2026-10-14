"""Automated Multi-Language Benchmark Runner for Fresh vs C vs Python.

Measures:
1. Wall-clock execution time (milliseconds)
2. Peak Resident Set Size (RSS) memory consumption (Megabytes)
Across:
- C (Compiled with GCC -O3)
- Fresh Native (Compiled via Fresh C Transpiler + GCC -O3)
- Fresh VM (Interpreted Fresh Bytecode VM)
- Python (CPython 3.12)
"""

import os
import sys
import time
import json
import gc
import subprocess
from pathlib import Path
import psutil

BENCH_DIR = Path(__file__).resolve().parent
ROOT_DIR = BENCH_DIR.parent

# Deferred cleanup list for Windows file locking
_cleanup_files = []

def _do_cleanup():
    """Attempt to delete temp files at exit."""
    for f in _cleanup_files:
        try:
            Path(f).unlink(missing_ok=True)
        except OSError:
            pass

import atexit
atexit.register(_do_cleanup)
ALGOS_DIR = BENCH_DIR / "algorithms"
RESULTS_FILE = BENCH_DIR / "results.json"

WORKLOADS = [
    {
        "id": "fibonacci",
        "name": "Recursive Fibonacci (fib(28))",
        "dir": ALGOS_DIR / "fibonacci",
        "c_src": "fibonacci.c",
        "py_src": "fibonacci.py",
        "fresh_src": "fibonacci.fresh",
        "supports_fresh_native": True,
    },
    {
        "id": "prime_sieve",
        "name": "Prime Number Sieve (10,000 limit)",
        "dir": ALGOS_DIR / "prime_sieve",
        "c_src": "primes.c",
        "py_src": "primes.py",
        "fresh_src": "primes.fresh",
        "supports_fresh_native": True,
    },
    {
        "id": "data_pipeline",
        "name": "Data Pipeline (10,000 items)",
        "dir": ALGOS_DIR / "data_pipeline",
        "c_src": "pipeline.c",
        "py_src": "pipeline.py",
        "fresh_src": "pipeline.fresh",
        "supports_fresh_native": True,
    },
    {
        "id": "quicksort",
        "name": "QuickSort (2,000 elements)",
        "dir": ALGOS_DIR / "quicksort",
        "c_src": "quicksort.c",
        "py_src": "quicksort.py",
        "fresh_src": "quicksort.fresh",
        "supports_fresh_native": False,   # ArrayExpr not supported in C backend
    },
]

N_TRIALS = 3

def measure_process(cmd, cwd):
    """Executes a command and measures wall-clock time (ms) and peak RSS memory (MB)."""
    t0 = time.perf_counter()
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    p = psutil.Process(proc.pid)
    peak_rss = 0

    try:
        while proc.poll() is None:
            try:
                mem = p.memory_info().rss
                if mem > peak_rss:
                    peak_rss = mem
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break
            time.sleep(0.002)
    except Exception:
        pass

    stdout, stderr = proc.communicate()
    t1 = time.perf_counter()

    if proc.returncode != 0:
        raise RuntimeError(f"Command failed ({proc.returncode}): {' '.join(str(c) for c in cmd)}\nStderr: {stderr}")

    duration_ms = (t1 - t0) * 1000.0
    peak_rss_mb = max(peak_rss / (1024 * 1024), 0.5)
    return duration_ms, peak_rss_mb, stdout.strip()

def run_benchmarks():
    print("=" * 80)
    print("   FRESH vs C vs PYTHON - COMPREHENSIVE BENCHMARK SUITE")
    print("=" * 80)
    print(f"Hardware & Environment: Python {sys.version.split()[0]} | MinGW GCC 6.3 | Windows x64")
    print(f"Trials per workload: {N_TRIALS} (averaged)\n")

    results = {}

    for w in WORKLOADS:
        w_id = w["id"]
        w_name = w["name"]
        w_dir = w["dir"]
        print(f"--> Running Benchmark: {w_name}")
        results[w_id] = {
            "name": w_name,
            "metrics": {},
        }

        # 1. C (GCC -O3)
        c_exe = w_dir / f"{w_id}_c.exe"
        try:
            compile_cmd = ["gcc", "-O3", w["c_src"], "-o", str(c_exe)]
            subprocess.run(compile_cmd, cwd=w_dir, check=True, capture_output=True)
            
            times_c, mems_c = [], []
            for _ in range(N_TRIALS):
                t, m, _ = measure_process([str(c_exe)], w_dir)
                times_c.append(t)
                mems_c.append(m)
            _cleanup_files.append(str(c_exe))
            avg_t_c = sum(times_c) / len(times_c)
            avg_m_c = sum(mems_c) / len(mems_c)
            results[w_id]["metrics"]["C (GCC -O3)"] = {"time_ms": round(avg_t_c, 2), "memory_mb": round(avg_m_c, 2)}
            print(f"    [C -O3]        Time: {avg_t_c:8.2f} ms | Peak Memory: {avg_m_c:6.2f} MB")
        except Exception as e:
            print(f"    [C -O3]        ERROR: {e}")
            results[w_id]["metrics"]["C (GCC -O3)"] = {"time_ms": None, "memory_mb": None}

        # 2. Fresh Native (C Backend + GCC -O3)
        if w["supports_fresh_native"]:
            fresh_c_src = w_dir / f"{w_id}_fresh_native.c"
            fresh_native_exe = w_dir / f"{w_id}_fresh_native.exe"
            try:
                # Emit C via subprocess (avoids shell-pipe null-char corruption)
                emit_res = subprocess.run(
                    ["fresh", "run", "--emit-c", w["fresh_src"]],
                    cwd=w_dir,
                    capture_output=True,
                    text=True,
                    check=True
                )
                fresh_c_src.write_text(emit_res.stdout, encoding="utf-8")
                
                # Compile with GCC -O3
                subprocess.run(["gcc", "-O3", str(fresh_c_src), "-o", str(fresh_native_exe)],
                               cwd=w_dir, check=True, capture_output=True)

                times_fn, mems_fn = [], []
                for _ in range(N_TRIALS):
                    t, m, _ = measure_process([str(fresh_native_exe)], w_dir)
                    times_fn.append(t)
                    mems_fn.append(m)
                
                _cleanup_files.append(str(fresh_c_src))
                _cleanup_files.append(str(fresh_native_exe))
                avg_t_fn = sum(times_fn) / len(times_fn)
                avg_m_fn = sum(mems_fn) / len(mems_fn)
                results[w_id]["metrics"]["Fresh (Native C)"] = {"time_ms": round(avg_t_fn, 2), "memory_mb": round(avg_m_fn, 2)}
                print(f"    [Fresh Native] Time: {avg_t_fn:8.2f} ms | Peak Memory: {avg_m_fn:6.2f} MB")
            except Exception as e:
                print(f"    [Fresh Native] ERROR: {e}")
                results[w_id]["metrics"]["Fresh (Native C)"] = {"time_ms": None, "memory_mb": None}
                _cleanup_files.append(str(fresh_c_src))
                _cleanup_files.append(str(fresh_native_exe))
        else:
            results[w_id]["metrics"]["Fresh (Native C)"] = {"time_ms": None, "memory_mb": None}
            print(f"    [Fresh Native] SKIPPED (C backend doesn't support dynamic arrays)")

        # 3. Python (CPython)
        try:
            times_py, mems_py = [], []
            for _ in range(N_TRIALS):
                t, m, _ = measure_process([sys.executable, w["py_src"]], w_dir)
                times_py.append(t)
                mems_py.append(m)
            avg_t_py = sum(times_py) / len(times_py)
            avg_m_py = sum(mems_py) / len(mems_py)
            results[w_id]["metrics"]["Python (3.12)"] = {"time_ms": round(avg_t_py, 2), "memory_mb": round(avg_m_py, 2)}
            print(f"    [Python 3.12]  Time: {avg_t_py:8.2f} ms | Peak Memory: {avg_m_py:6.2f} MB")
        except Exception as e:
            print(f"    [Python 3.12]  ERROR: {e}")
            results[w_id]["metrics"]["Python (3.12)"] = {"time_ms": None, "memory_mb": None}

        # 4. Fresh Bytecode VM
        try:
            times_vm, mems_vm = [], []
            for _ in range(N_TRIALS):
                t, m, _ = measure_process(["fresh", "run", w["fresh_src"]], w_dir)
                times_vm.append(t)
                mems_vm.append(m)
            avg_t_vm = sum(times_vm) / len(times_vm)
            avg_m_vm = sum(mems_vm) / len(mems_vm)
            results[w_id]["metrics"]["Fresh (Bytecode VM)"] = {"time_ms": round(avg_t_vm, 2), "memory_mb": round(avg_m_vm, 2)}
            print(f"    [Fresh VM]     Time: {avg_t_vm:8.2f} ms | Peak Memory: {avg_m_vm:6.2f} MB\n")
        except Exception as e:
            print(f"    [Fresh VM]     ERROR: {e}\n")
            results[w_id]["metrics"]["Fresh (Bytecode VM)"] = {"time_ms": None, "memory_mb": None}

    # Save results to JSON
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Saved benchmark results to {RESULTS_FILE}\n")

    # Print Summary Table
    print_summary_table(results)
    return results

def print_summary_table(results):
    print("=" * 86)
    print(f"{'Workload':<28} | {'C (-O3)':<12} | {'Fresh Native':<14} | {'Python 3.12':<12} | {'Fresh VM':<12}")
    print("-" * 86)
    for w_id, data in results.items():
        m = data["metrics"]
        c_t = f"{m['C (GCC -O3)']['time_ms']} ms" if m['C (GCC -O3)']['time_ms'] else "N/A"
        fn_t = f"{m['Fresh (Native C)']['time_ms']} ms" if m['Fresh (Native C)']['time_ms'] else "N/A"
        py_t = f"{m['Python (3.12)']['time_ms']} ms" if m['Python (3.12)']['time_ms'] else "N/A"
        vm_t = f"{m['Fresh (Bytecode VM)']['time_ms']} ms" if m['Fresh (Bytecode VM)']['time_ms'] else "N/A"
        print(f"{data['name'][:28]:<28} | {c_t:<12} | {fn_t:<14} | {py_t:<12} | {vm_t:<12}")
    print("=" * 86)

if __name__ == "__main__":
    run_benchmarks()
