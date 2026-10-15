"""Survey helpers: mining OpenTitan git history for the bug database.

These are the Phase 0/1 tools. Every number quoted in docs must come from
one of these scripts (rules of the road in docs/RESEARCH_PLAN.md).

Current entry point:

    python masked-bug-archaeology\\survey\\count_commits.py --help
"""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OPENTITAN = Path(r"C:\cv\opentitan")

# Commit message patterns that indicate an RTL bug fix (not features,
# cleanup, or DV-only changes).
FIX_PATTERNS = [
    re.compile(r"\bfix(es|ed)?\b", re.IGNORECASE),
    re.compile(r"\bbug\b", re.IGNORECASE),
    re.compile(r"\bcorrect(ion|ed)?\b", re.IGNORECASE),
    re.compile(r"\bwrong(ly)?\b", re.IGNORECASE),
    re.compile(r"\boff[- ]by[- ]one\b", re.IGNORECASE),
    re.compile(r"\brace condition\b", re.IGNORECASE),
]
# Commits that only touch these paths are excluded from RTL-bug counts.
NON_RTL_DIRS = ("doc/", "sw/", "site/", "util/", ".github")


@dataclass
class Commit:
    sha: str
    date: str
    subject: str
    files: list[str]

    @property
    def rtl_files(self) -> list[str]:
        return [
            f
            for f in self.files
            if f.startswith("hw/") and f.endswith((".v", ".sv", ".svh", ".vh"))
        ]

    @property
    def matches_fix_pattern(self) -> bool:
        return any(p.search(self.subject) for p in FIX_PATTERNS)


def git(repo: Path, *args: str, retries: int = 3) -> str:
    last_err: subprocess.CalledProcessError | None = None
    for attempt in range(retries):
        try:
            return subprocess.run(
                ["git", "-C", str(repo), "-c", "core.longpaths=true", *args],
                capture_output=True,
                text=True,
                check=True,
            ).stdout
        except subprocess.CalledProcessError as exc:
            last_err = exc
            # Transient failures happen when another git process holds locks
            # or a lazy blob fetch hiccups in partial clones. Back off, retry.
            wait = 2**attempt
            print(
                f"git {' '.join(args[:2])}... failed (exit {exc.returncode}), "
                f"retrying in {wait}s ({attempt + 1}/{retries})",
                file=sys.stderr,
            )
            import time

            time.sleep(wait)
    raise last_err  # type: ignore[misc]


def load_commits(repo: Path, block: str) -> list[Commit]:
    """All commits touching hw/ip/<block> RTL, oldest first."""
    log = git(
        repo,
        "log",
        "--date=short",
        "--pretty=format:%H|%ad|%s",
        "--name-only",
        "--",
        f"hw/ip/{block}",
    )
    commits: list[Commit] = []
    for entry in log.split("\n\n"):
        lines = [ln for ln in entry.splitlines() if ln.strip()]
        if len(lines) < 2:
            continue
        sha, date, subject = lines[0].split("|", 2)
        commits.append(Commit(sha, date, subject, lines[1:]))
    commits.reverse()  # oldest first
    return commits


def rtl_bug_commits(commits: list[Commit]) -> list[Commit]:
    return [
        c
        for c in commits
        if c.rtl_files and c.matches_fix_pattern and not c.subject.startswith("Update")
    ]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--blocks",
        nargs="+",
        default=["uart", "gpio", "hmac", "kmac", "spi_device", "alert_handler"],
        help="OpenTitan IP block names under hw/ip/",
    )
    ap.add_argument("--repo", type=Path, default=OPENTITAN)
    ap.add_argument(
        "--out", type=Path, default=REPO / "masked-bug-archaeology" / "survey"
    )
    args = ap.parse_args()

    rows: list[dict[str, str]] = []
    for block in args.blocks:
        if not (args.repo / "hw" / "ip" / block).exists():
            print(f"skip {block}: not in repo")
            continue
        commits = load_commits(args.repo, block)
        bugs = rtl_bug_commits(commits)
        if commits:
            first, last = commits[0].date, commits[-1].date
            span_days = (
                __import__("datetime").date.fromisoformat(last)
                - __import__("datetime").date.fromisoformat(first)
            ).days
        else:
            span_days = 0
        print(
            f"{block:15s} commits={len(commits):5d} rtl_bug_fixes={len(bugs):4d} "
            f"span={span_days}d ({first} .. {last})"
        )
        for c in bugs:
            rows.append(
                {
                    "block": block,
                    "sha": c.sha,
                    "date": c.date,
                    "subject": c.subject,
                    "n_rtl_files": str(len(c.rtl_files)),
                }
            )

    out_csv = args.out / "candidate_bug_fixes.csv"
    args.out.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["block", "sha", "date", "subject", "n_rtl_files"])
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {out_csv} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
