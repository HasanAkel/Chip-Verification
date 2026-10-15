"""Environment sanity check for the masked-bug-archaeology track.

Verifies the pieces this study needs on top of the base project env:
git with long-paths, the OpenTitan clone, a simulator, and disk space
for replay work trees. Run from an activated shell:

    . .\\scripts\\env.ps1
    python masked-bug-archaeology\\env\\check_env.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OPENTITAN = Path(r"C:\cv\opentitan")  # short path, matches project convention


def check(name: str, ok: bool, detail: str) -> bool:
    status = "ok " if ok else "MISSING"
    print(f"[{status}] {name}: {detail}")
    return ok


def git_version() -> str | None:
    git = shutil.which("git")
    if not git:
        return None
    try:
        out = subprocess.run(
            [git, "--version"], capture_output=True, text=True, check=True
        ).stdout
    except subprocess.CalledProcessError:
        return None
    return out.strip()


def main() -> int:
    required_ok = True

    required_ok &= check("python", sys.version_info >= (3, 10), sys.version.split()[0])

    ver = git_version()
    required_ok &= check("git", ver is not None, ver or "git not on PATH")

    iverilog = Path(r"C:\iverilog\bin\iverilog.exe")
    required_ok &= check("iverilog", iverilog.exists(), str(iverilog))

    verilator = shutil.which("verilator")
    check(
        "verilator",
        verilator is not None,
        verilator or "optional; needed for blocks Icarus cannot build",
    )

    vbb = Path(r"C:\cv\VeriBugBench")
    check(
        "VeriBugBench (for later mutation cross-check)",
        (vbb / "src" / "veribugbench").exists(),
        str(vbb),
    )

    required_ok &= check(
        "OpenTitan clone",
        (OPENTITAN / ".git").exists() and (OPENTITAN / "hw").exists(),
        str(OPENTITAN),
    )

    free_gb = shutil.disk_usage("C:\\").free / 2**30
    check(
        "disk space",
        free_gb > 20,
        f"{free_gb:.1f} GiB free on C: (replay trees need headroom)",
    )

    if not required_ok:
        print(
            "\nSetup: git clone --depth 1 https://github.com/lowRISC/opentitan "
            f"{OPENTITAN}"
        )
        return 1
    print("\nAll required pieces present. Phase 0 can start.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
