"""High-level execution of reference and faulty benchmark versions."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .execution import run_iverilog, run_vcs
from .project import ProjectManifest


@dataclass(frozen=True)
class RunResult:
    project_id: str
    instance_id: str | None
    work_dir: Path
    output: Path
    stdout: str


def run_benchmark(
    manifest: ProjectManifest,
    *,
    work_root: Path,
    instance_id: str | None = None,
    backend: str,
    top: str | None = None,
    timeout: int = 300,
    coverage: bool = False,
) -> RunResult:
    """Compile and run one reference or selected faulty version."""
    sources = manifest.source_paths(instance_id)
    missing = [source for source in sources if not source.is_file()]
    if missing:
        preview = "\n".join(f"  - {path}" for path in missing[:20])
        raise FileNotFoundError(f"missing benchmark source files:\n{preview}")
    if backend == "iverilog" and coverage:
        raise ValueError(
            "--coverage is only supported by the VCS backend; "
            "Icarus Verilog does not produce the VCS/URG coverage data "
            "required by this workflow"
        )
    run_name = "reference" if instance_id is None else f"instances/{instance_id}"
    work_dir = (work_root / manifest.project_id / run_name).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    output = work_dir / manifest.output_filename
    if output.is_file():
        output.unlink()
    if backend == "iverilog":
        try:
            completed = run_iverilog(
                sources,
                output=work_dir / "simv.out",
                top=top,
                timeout=timeout,
                cwd=work_dir,
                include_dirs=[manifest.project_dir],
            )
        except subprocess.CalledProcessError as error:
            # Testbenches often call $fatal after writing the CSV. The log is
            # still the observability evidence; a missing log stays a hard error.
            if not output.is_file() or output.stat().st_size == 0:
                raise
            completed = error
    elif backend == "vcs":
        completed = run_vcs(
            sources,
            cwd=work_dir,
            timeout=timeout,
            coverage=coverage,
            include_dirs=[manifest.project_dir],
        )
    else:
        raise ValueError(f"unsupported simulator backend: {backend}")
    if not output.is_file():
        raise FileNotFoundError(
            f"simulation completed but did not create {manifest.output_filename!r} "
            f"in {work_dir}"
        )
    return RunResult(
        project_id=manifest.project_id,
        instance_id=instance_id,
        work_dir=work_dir,
        output=output,
        stdout=completed.stdout or "",
    )
