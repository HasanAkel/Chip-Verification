"""Report whether the local verification tools are usable.

Run after:

    . .\\scripts\\env.ps1
    python lab\\check_env.py

Exit code 0 means required pieces are present (Python, Icarus, git,
VeriBugBench checkout + import, pyverilog). GTKWave and Synopsys VCS are
optional and only printed as status.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IVERILOG = Path(os.environ.get("IVERILOG", r"C:\iverilog\bin\iverilog.exe"))
VVP = Path(os.environ.get("VVP", r"C:\iverilog\bin\vvp.exe"))
GTKWAVE_CANDIDATES = [
    Path(os.environ["GTKWAVE"]) if os.environ.get("GTKWAVE") else None,
    ROOT / "tools" / "gtkwave" / "gtkwave64" / "bin" / "gtkwave.exe",
    ROOT / "tools" / "gtkwave" / "bin" / "gtkwave.exe",
]


def check(name: str, ok: bool, detail: str) -> bool:
    status = "ok " if ok else "MISSING"
    print(f"[{status}] {name}: {detail}")
    return ok


def main() -> None:
    required_ok = True
    required_ok &= check("python", sys.version_info >= (3, 10), sys.version.split()[0])
    required_ok &= check("iverilog", IVERILOG.exists(), str(IVERILOG))
    required_ok &= check("vvp", VVP.exists(), str(VVP))

    git = shutil.which("git")
    required_ok &= check("git", git is not None, git or "git not on PATH")

    bench = Path(os.environ.get("VERIBUGBENCH_ROOT", r"C:\cv\VeriBugBench"))
    required_ok &= check(
        "VeriBugBench checkout",
        (bench / "src" / "veribugbench").exists(),
        str(bench),
    )

    try:
        import veribugbench  # noqa: F401

        imported = True
        detail = "import veribugbench succeeded"
    except Exception as exc:  # noqa: BLE001
        imported = False
        detail = f"{type(exc).__name__}: {exc}"
    required_ok &= check("veribugbench package", imported, detail)

    try:
        import pyverilog  # noqa: F401

        py_ok = True
        py_detail = "import pyverilog succeeded"
    except Exception as exc:  # noqa: BLE001
        py_ok = False
        py_detail = f"{type(exc).__name__}: {exc}"
    required_ok &= check("pyverilog", py_ok, py_detail)

    gtk = next((path for path in GTKWAVE_CANDIDATES if path and path.exists()), None)
    check(
        "gtkwave",
        gtk is not None,
        str(gtk) if gtk else "optional waveform viewer not installed",
    )

    vcs = shutil.which("vcs")
    check(
        "synopsys vcs",
        vcs is not None,
        vcs or "commercial simulator, not required for the lab",
    )

    if not required_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
