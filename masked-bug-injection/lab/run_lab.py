"""Compile the pipe lab, simulate each masking scenario, and write labels.

This is the smallest end-to-end "injection + simulate + classify" loop in the
project. VeriBugBench does the same idea at project scale with 19 operators.

Run after activating the project env:

    . .\\scripts\\env.ps1
    python lab\\run_lab.py

Each scenario is one Icarus Verilog compile (-D for bug defines) plus one
`vvp` run (+stim= for the regression shape). The clean design under the same
stimulus is the golden CSV. Labels use internal probes (count/hit) as well as
the checked pin (seen) so starvation and downstream cover-up are distinguishable.
"""

from __future__ import annotations

import csv
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # repo root (lab/ now sits one level deeper)
LAB = Path(__file__).resolve().parent
RTL = LAB / "rtl" / "pipe.v"
TB = LAB / "tb" / "tb_pipe.v"
RESULTS = LAB / "results"

# Override with env vars if Icarus is not in the default install location.
IVERILOG = Path(os.environ.get("IVERILOG", r"C:\iverilog\bin\iverilog.exe"))
VVP = Path(os.environ.get("VVP", r"C:\iverilog\bin\vvp.exe"))

# Must match the case arms in tb_pipe.v
STIM_FULL = 0
STIM_BLIND = 1
STIM_STARVE = 2

# (name, compile-time defines, stimulus id)
SCENARIOS = [
    {"name": "clean_full", "defines": [], "stim": STIM_FULL},
    {"name": "clean_blind", "defines": [], "stim": STIM_BLIND},
    {"name": "clean_starve", "defines": [], "stim": STIM_STARVE},
    {"name": "visible_sub", "defines": ["BUG_SUB"], "stim": STIM_FULL},
    {"name": "downstream_mask", "defines": ["BUG_SUB"], "stim": STIM_BLIND},
    {"name": "starvation", "defines": ["BUG_SUB"], "stim": STIM_STARVE},
    {"name": "upstream_only", "defines": ["BUG_ALLOW_STUCK"], "stim": STIM_FULL},
    {
        "name": "upstream_hides_sub",
        "defines": ["BUG_SUB", "BUG_ALLOW_STUCK"],
        "stim": STIM_FULL,
    },
]


def run(cmd: list[str], cwd: Path) -> None:
    """Run a subprocess; print stdout/stderr and abort on non-zero exit."""
    completed = subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        sys.stderr.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        raise SystemExit(f"command failed ({completed.returncode}): {' '.join(cmd)}")


def simulate(name: str, defines: list[str], stim: int) -> list[dict[str, str]]:
    """Compile + run one scenario; return the rows of trace.csv."""
    work = RESULTS / name
    work.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(IVERILOG),
        "-g2012",
        "-o",
        str(work / "sim.vvp"),
        "-s",
        "tb_pipe",
    ]
    cmd += [f"-D{define}" for define in defines]
    cmd += [str(RTL), str(TB)]
    run(cmd, work)
    run([str(VVP), str(work / "sim.vvp"), f"+stim={stim}"], work)
    with (work / "trace.csv").open(newline="") as handle:
        return list(csv.DictReader(handle))


def column_differs(left: list[dict[str, str]], right: list[dict[str, str]], key: str) -> bool:
    """True if any row differs in column `key` (or lengths differ)."""
    if len(left) != len(right):
        return True
    return any(a[key] != b[key] for a, b in zip(left, right))


def reached(rows: list[dict[str, str]]) -> bool:
    """True if the bug site saw enable at least once (hit rose)."""
    return any(row["hit"] == "1" for row in rows)


def classify(
    name: str,
    defines: list[str],
    local_vs_clean: bool,
    pin_vs_clean: bool,
    local_vs_upstream: bool | None,
    site_reached: bool,
) -> str:
    """Map probe/pin mismatches onto the mask taxonomy used by the project."""
    if name.startswith("clean_"):
        return "reference"
    if "BUG_SUB" in defines and "BUG_ALLOW_STUCK" in defines:
        # Pin fails vs clean (always-stuck enable looks broken), but the
        # counter matches the upstream-only chip → the SUB bug is hidden.
        if pin_vs_clean and local_vs_upstream is False:
            return "masked_by_upstream_bug"
        return "dual_bug_not_masked"
    if pin_vs_clean:
        return "visible"
    if local_vs_clean and not site_reached:
        return "unexpected_local_change_without_reach"
    if local_vs_clean:
        return "downstream_mask"
    if not site_reached and "BUG_SUB" in defines:
        return "starvation"
    return "no_effect"


def main() -> None:
    if not IVERILOG.exists() or not VVP.exists():
        raise SystemExit(
            "Icarus Verilog was not found. Expected iverilog.exe and vvp.exe "
            f"under {IVERILOG.parent}."
        )

    traces: dict[str, list[dict[str, str]]] = {}
    for scenario in SCENARIOS:
        print(f"sim  {scenario['name']}")
        traces[scenario["name"]] = simulate(
            scenario["name"], scenario["defines"], scenario["stim"]
        )

    # Golden traces are the clean DUT under each stimulus shape.
    clean_by_stim = {
        STIM_FULL: traces["clean_full"],
        STIM_BLIND: traces["clean_blind"],
        STIM_STARVE: traces["clean_starve"],
    }
    upstream_only = traces["upstream_only"]

    labels_path = RESULTS / "labels.csv"
    fieldnames = [
        "scenario",
        "defines",
        "stim",
        "reached",
        "local_mismatch_vs_clean",
        "pin_mismatch_vs_clean",
        "local_mismatch_vs_upstream_only",
        "mask_class",
    ]
    with labels_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for scenario in SCENARIOS:
            name = scenario["name"]
            rows = traces[name]
            clean = clean_by_stim[scenario["stim"]]
            local = column_differs(rows, clean, "count")
            pin = column_differs(rows, clean, "seen")
            versus_upstream = None
            if name == "upstream_hides_sub":
                versus_upstream = column_differs(rows, upstream_only, "count")
            label = classify(
                name,
                scenario["defines"],
                local,
                pin,
                versus_upstream,
                reached(rows),
            )
            writer.writerow(
                {
                    "scenario": name,
                    "defines": " ".join(scenario["defines"]),
                    "stim": scenario["stim"],
                    "reached": int(reached(rows)),
                    "local_mismatch_vs_clean": int(local),
                    "pin_mismatch_vs_clean": int(pin),
                    "local_mismatch_vs_upstream_only": (
                        "" if versus_upstream is None else int(versus_upstream)
                    ),
                    "mask_class": label,
                }
            )
            print(
                f"label {name:22} {label:24} "
                f"reached={int(reached(rows))} local={int(local)} pin={int(pin)}"
            )

    # Regression guard: if someone edits RTL/TB, labels must still match intent.
    expected = {
        "clean_full": "reference",
        "clean_blind": "reference",
        "clean_starve": "reference",
        "visible_sub": "visible",
        "downstream_mask": "downstream_mask",
        "starvation": "starvation",
        "upstream_only": "visible",
        "upstream_hides_sub": "masked_by_upstream_bug",
    }
    with labels_path.open(newline="") as handle:
        got = {row["scenario"]: row["mask_class"] for row in csv.DictReader(handle)}
    mismatches = {name: got[name] for name, label in expected.items() if got[name] != label}
    if mismatches:
        raise SystemExit(f"label check failed: {mismatches}")
    print(f"wrote {labels_path}")
    print("all scenario labels match the expected masking classes")


if __name__ == "__main__":
    main()
