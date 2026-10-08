"""Stack VeriBugBench mutants on the AXI interconnect and look for masked bugs.

A bug is observable when the four SRAM dumps differ from the clean design.
A k-bug combination hides a member when the joint SRAM image matches exactly
one of those members run alone: the other bugs left no extra trace.

Bugs are injected together only when their edits do not touch the same lines.
Order does not matter, so this searches combinations, not permutations.

Usage (from the repo root, after .\\scripts\\env.ps1):

    python lab\\axi_mask_search.py probe
    python lab\\axi_mask_search.py run
    python lab\\axi_mask_search.py run --max-order 2
"""

from __future__ import annotations

import argparse
import csv
import difflib
import hashlib
import itertools
import math
import os
import re
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BENCH = Path(
    r"C:\cv\VeriBugBench\dataset\v1.0\sources\Native\opencores"
    r"\addition\verilog_axi-interconnect\testbench"
)
WORK = REPO / "work" / "axi_mask"
RTL_FIX = WORK / "rtl"
GENERATED = WORK / "generated"
RESULTS = WORK / "results"
EXTRA = WORK / "extra_mutants"
STRICT = WORK / "strict_results"
# These DUT files never entered the original mutant set: PyVerilog rejects
# their empty `else;` / `default;` statements. The master BFM is stimulus,
# not a place we inject bus bugs.
UNPARSED_DUT = (
    "addr_wdata_demux_1to2.v",
    "addr_wdata_mux_2to1.v",
    "addr_wdata_mux_m4.v",
)

# Handwritten sources compiled with the testbench. `interconnect` is a
# SystemVerilog-2012 keyword, so the local copy is renamed axi_fabric.
ORIGIN_FILES = [
    "addr_wdata_demux_1to2.v",
    "master.v",
    "sram_controller.v",
    "addr_wdata_mux_2to1.v",
    "rdata_demux_1to2.v",
    "addr_wdata_mux_m4.v",
    "rdata_mux_2to1.v",
    "wr_demux_1to2.v",
    "ar_demux_1to2.v",
    "rdata_mux_m4.v",
    "wr_mux_2to1.v",
    "ar_mux_2to1.v",
    "router_master_2to1.v",
    "wr_mux_s4.v",
    "ar_mux_m4.v",
    "router_slave_1to2.v",
    "interconnect.v",
    "sram_1024x32.v",
]

SCHEMAS = sorted(
    [
        "NSubInsert_IF",
        "NSubInsert_Case",
        "PartselectUpdate",
        "PartselectInsert",
        "PartselectDelete",
        "PointerUpdate",
        "PointerInsert",
        "PointerDelete",
        "ExprUpdate",
        "ExprInsert",
        "ExprDelete",
        "NSubUpdate",
        "NSubInsert",
        "NSubDelete",
        "NSubMove",
        "AssignN2B",
        "AssignB2N",
        "EdgeFlip",
        "EdgeInsert",
        "EdgeDelete",
        "IOFlip1",
        "IOFlip2",
    ],
    key=len,
    reverse=True,
)

IVERILOG = os.environ.get("IVERILOG", r"C:\iverilog\bin\iverilog.exe")
VVP = os.environ.get("VVP", r"C:\iverilog\bin\vvp.exe")
SRAM_NAMES = ("sram0.txt", "sram1.txt", "sram2.txt", "sram3.txt")


@dataclass(frozen=True)
class Bug:
    bug_id: str
    stem: str
    schema: str
    node_id: int
    line: int
    mutant: Path
    origin: Path

    @property
    def filename(self) -> str:
        return f"{self.stem}.v"


def parse_bug(directory: Path) -> Bug:
    name = directory.name
    for schema in SCHEMAS:
        token = f"_{schema}_"
        if token not in name:
            continue
        stem, rest = name.split(token, 1)
        node_text, line_text = rest.split("_")
        return Bug(
            bug_id=name,
            stem=stem,
            schema=schema,
            node_id=int(node_text),
            line=int(line_text),
            mutant=directory / f"{name}.v",
            origin=directory / f"{name}_origin.v",
        )
    raise ValueError(f"cannot parse mutant directory {name}")


def load_bugs(include_extra: bool = False) -> list[Bug]:
    directories = [path for path in sorted((BENCH / "mantra").iterdir()) if path.is_dir()]
    if include_extra and EXTRA.is_dir():
        directories.extend(path for path in sorted(EXTRA.iterdir()) if path.is_dir())
    bugs = [parse_bug(path) for path in directories]
    missing = [bug.bug_id for bug in bugs if not bug.mutant.is_file() or not bug.origin.is_file()]
    if missing:
        raise SystemExit(f"mutant files missing for {missing[:5]}")
    return bugs


def patch_testbench(text: str) -> str:
    """Make the enhanced bench compile on Icarus and finish after directed tests."""
    text = text.replace("interconnect interconnect(", "axi_fabric axi_fabric(", 1)
    # Reset must happen before the directed tests, or tb_start wipes their writes.
    text = text.replace("reg llm_go_signal = 1;", "reg llm_go_signal = 0;", 1)
    text = text.replace(
        "// === LLM Enhanced Stimuli (Phase 1) ===\nreg llm_go_signal = 1;\n",
        "// === LLM Enhanced Stimuli (Phase 1) ===\n",
        1,
    )
    text = text.replace(
        """initial begin
   
    wait(llm_go_signal == 0); // [Auto] Handover from LLM to Original TB
tb_start;
   #8
""",
        """initial begin
   tb_start;
   #8
   llm_go_signal = 1;
   wait(llm_go_signal == 0);
""",
        1,
    )
    # Drop the 3ms $random flood. Directed master0..3 calls are the stimulus.
    text = re.sub(
        r"while\s*\(\s*1\s*\)\s*master[0-3]\([^;]*\);",
        "/* random master traffic disabled for the masking search */",
        text,
    )
    text = text.replace("#3000000", "#200", 1)
    text = text.replace("integer i, j, k, f;", "integer i, j, k, f, spin;", 1)
    for master_id in range(4):
        old_wait = f"while(!last_m{master_id}) #10;"
        new_wait = (
            f"spin = 0; while(!last_m{master_id} && spin < 80) begin #10; spin = spin + 1; end"
        )
        if old_wait not in text:
            raise SystemExit(f"task wait not found: {old_wait}")
        text = text.replace(old_wait, new_wait, 1)
    # This loop writes a line every time unit and dominates runtime.
    text = text.replace(
        """          forever begin
            //#10
            #1
            $fwrite(file_mantra, "%0d, ", $time);""",
        """          if (0) begin
            //#10
            #1
            $fwrite(file_mantra, "%0d, ", $time);""",
        1,
    )
    text = text.replace("#20000000;", "#200000;", 1)
    watchdog = """    #200000;
    $display("\\n[Watchdog] Timeout triggered at %t!", $time);
    if (file_mantra != 0) $fclose(file_mantra);
    $finish;"""
    watchdog_dump = """    #200000;
    $display("\\n[Watchdog] Timeout triggered at %t!", $time);
    dump_file(2'b00);
    dump_file(2'b01);
    dump_file(2'b10);
    dump_file(2'b11);
    if (file_mantra != 0) $fclose(file_mantra);
    $display("MASK_SEARCH_WATCHDOG %t", $time);
    $finish;"""
    if watchdog not in text:
        raise SystemExit("watchdog block not found; testbench patch is stale")
    text = text.replace(watchdog, watchdog_dump, 1)
    text = text.replace(
        "         $finish;",
        '         $display("MASK_SEARCH_DONE %t", $time);\n         $finish;',
        1,
    )
    # Two masters hit slave 0 together, then read their own words back.
    text = text.replace(
        "    llm_go_signal = 0;",
        """    fork
      master1(1'b1, 32'h0000_0040, 128'h44444444444444444444444444444444, 2'b01, 4'b0000);
      master2(1'b1, 32'h0000_0050, 128'h66666666666666666666666666666666, 2'b01, 4'b0000);
    join
    master1(1'b0, 32'h0000_0040, 128'h0, 2'b01, 4'b0000);
    master2(1'b0, 32'h0000_0050, 128'h0, 2'b01, 4'b0000);
    llm_go_signal = 0;""",
        1,
    )
    trace = """
integer trace_fd;
initial begin
  trace_fd = $fopen("trace.csv");
  $fwrite(trace_fd, "ev\\n");
  forever begin
    #10
  if (awvalid_m0 === 1'b1 && awready_m0 === 1'b1) $fwrite(trace_fd, "AW 0 %h %h %h\\n", awaddr_m0, awlen_m0, awburst_m0);
  if (wvalid_m0 === 1'b1 && wready_m0 === 1'b1) $fwrite(trace_fd, "W 0 %h %h %h\\n", wdata_m0, wstrb_m0, wlast_m0);
  if (bvalid_m0 === 1'b1 && bready_m0 === 1'b1) $fwrite(trace_fd, "B 0 %h %h\\n", bid_m0, bresp_m0);
  if (arvalid_m0 === 1'b1 && arready_m0 === 1'b1) $fwrite(trace_fd, "AR 0 %h %h %h\\n", araddr_m0, arlen_m0, arburst_m0);
  if (rvalid_m0 === 1'b1 && rready_m0 === 1'b1) $fwrite(trace_fd, "R 0 %h %h %h\\n", rdata_m0, rlast_m0, rresp_m0);
  if (awvalid_m1 === 1'b1 && awready_m1 === 1'b1) $fwrite(trace_fd, "AW 1 %h %h %h\\n", awaddr_m1, awlen_m1, awburst_m1);
  if (wvalid_m1 === 1'b1 && wready_m1 === 1'b1) $fwrite(trace_fd, "W 1 %h %h %h\\n", wdata_m1, wstrb_m1, wlast_m1);
  if (bvalid_m1 === 1'b1 && bready_m1 === 1'b1) $fwrite(trace_fd, "B 1 %h %h\\n", bid_m1, bresp_m1);
  if (arvalid_m1 === 1'b1 && arready_m1 === 1'b1) $fwrite(trace_fd, "AR 1 %h %h %h\\n", araddr_m1, arlen_m1, arburst_m1);
  if (rvalid_m1 === 1'b1 && rready_m1 === 1'b1) $fwrite(trace_fd, "R 1 %h %h %h\\n", rdata_m1, rlast_m1, rresp_m1);
  if (awvalid_m2 === 1'b1 && awready_m2 === 1'b1) $fwrite(trace_fd, "AW 2 %h %h %h\\n", awaddr_m2, awlen_m2, awburst_m2);
  if (wvalid_m2 === 1'b1 && wready_m2 === 1'b1) $fwrite(trace_fd, "W 2 %h %h %h\\n", wdata_m2, wstrb_m2, wlast_m2);
  if (bvalid_m2 === 1'b1 && bready_m2 === 1'b1) $fwrite(trace_fd, "B 2 %h %h\\n", bid_m2, bresp_m2);
  if (arvalid_m2 === 1'b1 && arready_m2 === 1'b1) $fwrite(trace_fd, "AR 2 %h %h %h\\n", araddr_m2, arlen_m2, arburst_m2);
  if (rvalid_m2 === 1'b1 && rready_m2 === 1'b1) $fwrite(trace_fd, "R 2 %h %h %h\\n", rdata_m2, rlast_m2, rresp_m2);
  if (awvalid_m3 === 1'b1 && awready_m3 === 1'b1) $fwrite(trace_fd, "AW 3 %h %h %h\\n", awaddr_m3, awlen_m3, awburst_m3);
  if (wvalid_m3 === 1'b1 && wready_m3 === 1'b1) $fwrite(trace_fd, "W 3 %h %h %h\\n", wdata_m3, wstrb_m3, wlast_m3);
  if (bvalid_m3 === 1'b1 && bready_m3 === 1'b1) $fwrite(trace_fd, "B 3 %h %h\\n", bid_m3, bresp_m3);
  if (arvalid_m3 === 1'b1 && arready_m3 === 1'b1) $fwrite(trace_fd, "AR 3 %h %h %h\\n", araddr_m3, arlen_m3, arburst_m3);
  if (rvalid_m3 === 1'b1 && rready_m3 === 1'b1) $fwrite(trace_fd, "R 3 %h %h %h\\n", rdata_m3, rlast_m3, rresp_m3);
  end
end
"""
    marker = text.rfind("endmodule")
    if marker < 0:
        raise SystemExit("testbench has no endmodule")
    text = text[:marker] + trace + "\nendmodule\n"
    return text


def patch_master(text: str) -> str:
    """Bound each handshake wait so a stuck response does not end the test."""
    text = text.replace(
        "integer            i;\n",
        "integer            i;\ninteger            guard;\n",
        1,
    )
    swaps = {
        "while (!awready) #10;": "guard = 0; while (!awready && guard < 40) begin #10; guard = guard + 1; end",
        "while (!wready) #10;": "guard = 0; while (!wready && guard < 40) begin #10; guard = guard + 1; end",
        "while (!bvalid) #10;": "guard = 0; while (!bvalid && guard < 40) begin #10; guard = guard + 1; end",
        "while(!arready) #10;": "guard = 0; while (!arready && guard < 40) begin #10; guard = guard + 1; end",
        "while(!rlast) #10;": "guard = 0; while (!rlast && guard < 40) begin #10; guard = guard + 1; end",
    }
    for old, new in swaps.items():
        if old not in text:
            raise SystemExit(f"master wait not found: {old}")
        text = text.replace(old, new, 1)
    return text


def rename_fabric(text: str) -> str:
    return text.replace("module interconnect", "module axi_fabric", 1)


def prepare_rtl() -> None:
    RTL_FIX.mkdir(parents=True, exist_ok=True)
    GENERATED.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    fabric = (BENCH / "interconnect.v").read_text(encoding="utf-8", errors="replace")
    (RTL_FIX / "interconnect.v").write_text(rename_fabric(fabric), encoding="utf-8")
    master = (BENCH / "master.v").read_text(encoding="utf-8", errors="replace")
    (RTL_FIX / "master.v").write_text(patch_master(master), encoding="utf-8")
    bench = (BENCH / "tb_topmodule_enhanced.v").read_text(encoding="utf-8", errors="replace")
    (RTL_FIX / "tb_topmodule_enhanced.v").write_text(patch_testbench(bench), encoding="utf-8")


def line_edits(origin: list[str], mutant: list[str]) -> tuple[tuple[int, int, tuple[str, ...]], ...]:
    matcher = difflib.SequenceMatcher(a=origin, b=mutant, autojunk=False)
    edits = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        edits.append((i1, i2, tuple(mutant[j1:j2])))
    return tuple(edits)


def merge_edits(
    origin: list[str],
    edits_per_bug: list[tuple[tuple[int, int, tuple[str, ...]], ...]],
) -> list[str] | None:
    """Apply several non-overlapping edits. Overlap means the bugs are not stackable."""
    claimed: dict[int, int] = {}
    for bug_index, edits in enumerate(edits_per_bug):
        for start, stop, _new in edits:
            # An insert at `start` claims that boundary so two inserts cannot share it.
            span = range(start, stop) if stop > start else range(start, start + 1)
            for line_no in span:
                owner = claimed.get(line_no)
                if owner is not None and owner != bug_index:
                    return None
                claimed[line_no] = bug_index
    merged = list(origin)
    for start, stop, new in sorted(
        (edit for edits in edits_per_bug for edit in edits),
        key=lambda item: item[0],
        reverse=True,
    ):
        merged[start:stop] = list(new)
    return merged


def source_list(bugs: list[Bug], origins: dict[str, list[str]], cache: dict[str, tuple]) -> list[Path]:
    """Build the file list for a combination of bugs. Raises ValueError if edits overlap."""
    by_stem: dict[str, list[Bug]] = defaultdict(list)
    for bug in bugs:
        by_stem[bug.stem].append(bug)
    paths: list[Path] = []
    for filename in ORIGIN_FILES:
        stem = filename[:-2]
        chosen = by_stem.get(stem, [])
        if not chosen:
            if filename == "interconnect.v":
                paths.append(RTL_FIX / "interconnect.v")
            elif filename == "master.v":
                paths.append(RTL_FIX / "master.v")
            else:
                paths.append(BENCH / filename)
            continue
        if len(chosen) == 1:
            path = chosen[0].mutant
        else:
            key = tuple(sorted(bug.bug_id for bug in chosen))
            cached = cache.get("|".join(key))
            if cached is None:
                edits = [line_edits(origins[stem], bug_lines(bug)) for bug in chosen]
                merged = merge_edits(origins[stem], edits)
                if merged is None:
                    raise ValueError("overlapping edits")
                text = "\n".join(merged) + "\n"
                if stem == "interconnect":
                    text = rename_fabric(text)
                path = GENERATED / f"{'_'.join(key)}.v"
                path.write_text(text, encoding="utf-8")
                cache["|".join(key)] = (path,)
            path = cache["|".join(key)][0]
        if stem == "interconnect" and len(chosen) == 1:
            renamed = GENERATED / f"{chosen[0].bug_id}.v"
            if not renamed.is_file():
                renamed.write_text(
                    rename_fabric(path.read_text(encoding="utf-8", errors="replace")),
                    encoding="utf-8",
                )
            path = renamed
        paths.append(path)
    paths.append(RTL_FIX / "tb_topmodule_enhanced.v")
    return paths


def bug_lines(bug: Bug) -> list[str]:
    return bug.mutant.read_text(encoding="utf-8", errors="replace").splitlines()


def simulate(sources: list[str]) -> tuple[str, str, float]:
    """Compile and run. Returns (status, signature, seconds)."""
    started = time.perf_counter()
    from tempfile import TemporaryDirectory

    with TemporaryDirectory(prefix="axi_sim_") as tmp:
        cwd = Path(tmp)
        sim = cwd / "sim.vvp"
        compile = subprocess.run(
            [IVERILOG, "-g2012", "-o", str(sim), "-s", "tb", *sources],
            cwd=cwd,
            text=True,
            capture_output=True,
        )
        if compile.returncode != 0:
            tail = (compile.stderr or compile.stdout or "compile failed")[-400:]
            return "compile_error", tail.replace("\n", " "), time.perf_counter() - started
        try:
            run = subprocess.run(
                [VVP, str(sim)],
                cwd=cwd,
                text=True,
                capture_output=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            return "timeout", "", time.perf_counter() - started
        blobs = []
        for name in SRAM_NAMES:
            path = cwd / name
            if not path.is_file():
                log = (run.stdout or "")[-200:].replace("\n", " ")
                return "no_sram", log, time.perf_counter() - started
            blobs.append(path.read_bytes())
        trace = cwd / "trace.csv"
        blobs.append(trace.read_bytes() if trace.is_file() else b"NO_TRACE")
        digest = hashlib.sha256(b"".join(blobs)).hexdigest()[:16]
        status = "watchdog" if "MASK_SEARCH_WATCHDOG" in (run.stdout or "") else "ok"
        return status, digest, time.perf_counter() - started


def _worker(payload: tuple[str, list[str]]) -> tuple[str, str, str, float]:
    label, sources = payload
    status, signature, seconds = simulate(sources)
    return label, status, signature, seconds


def run_pool(jobs: list[tuple[str, list[str]]], workers: int) -> list[tuple[str, str, str, float]]:
    if not jobs:
        return []
    results = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_worker, job) for job in jobs]
        done = 0
        for future in as_completed(futures):
            results.append(future.result())
            done += 1
            if done % 25 == 0 or done == len(jobs):
                print(f"  finished {done}/{len(jobs)}", flush=True)
    return results


def shared_origins(bugs: list[Bug]) -> dict[str, list[str]]:
    """One codegen baseline per RTL file. Mutants of a file are diffs against it."""
    grouped: dict[str, list[Bug]] = defaultdict(list)
    for bug in bugs:
        grouped[bug.stem].append(bug)
    origins: dict[str, list[str]] = {}
    for stem, group in grouped.items():
        texts = [bug.origin.read_text(encoding="utf-8", errors="replace").splitlines() for bug in group]
        first = texts[0]
        if any(text != first for text in texts[1:]):
            raise SystemExit(f"codegen origins disagree for {stem}; cannot stack bugs in that file")
        origins[stem] = first
    return origins


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def stackable(bugs: tuple[Bug, ...], origins: dict[str, list[str]]) -> bool:
    by_stem: dict[str, list[Bug]] = defaultdict(list)
    for bug in bugs:
        by_stem[bug.stem].append(bug)
    for stem, group in by_stem.items():
        if len(group) < 2:
            continue
        edits = [line_edits(origins[stem], bug_lines(bug)) for bug in group]
        if merge_edits(origins[stem], edits) is None:
            return False
    return True


def classify(combo_sig: str, member_sigs: dict[str, str], golden: str) -> tuple[str, str]:
    """Return (class, hidden bug ids). Hidden bugs are the ones whose signature disappeared."""
    if combo_sig == golden:
        # Joint run looks clean, so every member's effect disappeared.
        return "all_hidden_or_cancelled", " ".join(member_sigs)
    hidden = [bug_id for bug_id, sig in member_sigs.items() if sig != combo_sig]
    matches = [bug_id for bug_id in member_sigs if bug_id not in hidden]
    if matches and hidden:
        return "masked", " ".join(hidden)
    if matches:
        return "same_signature", ""
    return "new_signature", ""


def sanitize_for_parser(text: str) -> str:
    """Give PyVerilog an empty statement it will accept. Behavior is unchanged."""
    text = re.sub(r"\belse\s*;", "else begin end", text)
    text = re.sub(r"\bdefault\s*;", "default: begin end", text)
    return text


def generate_extra() -> int:
    """Inject one mutant per operator site in the DUT files the old set skipped."""
    marker = EXTRA / "COUNT.txt"
    if marker.is_file():
        return int(marker.read_text(encoding="utf-8").strip())
    import copy
    import random
    import tempfile

    import yaml
    import pyverilog.vparser.ast as vast
    from pyverilog.ast_code_generator.codegen import ASTCodeGenerator
    from pyverilog.vparser.parser import parse
    from veribugbench.framework import _collect_nodes
    from veribugbench.mutation import implementations

    patterns = yaml.safe_load(
        Path(r"C:\cv\VeriBugBench\configs\mutation_patterns.yaml").read_text(encoding="utf-8")
    )["patterns"]
    EXTRA.mkdir(parents=True, exist_ok=True)
    made = 0
    skipped = 0
    for filename in UNPARSED_DUT:
        source = BENCH / filename
        with tempfile.TemporaryDirectory(prefix="axi-parse-") as tmp:
            parse_path = Path(tmp) / filename
            parse_path.write_text(
                sanitize_for_parser(source.read_text(encoding="utf-8", errors="replace")),
                encoding="utf-8",
            )
            ast, _directives = parse(
                [str(parse_path)],
                preprocess_include=[str(BENCH), tmp],
                outputdir=tmp,
                debug=False,
            )
        found, lines = _collect_nodes(ast, patterns, vast)
        origin_text = ASTCodeGenerator().visit(ast)
        print(f"{filename}: {sum(len(set(ids)) for ids in found.values())} sites", flush=True)
        for schema, node_ids in found.items():
            operator_class = getattr(implementations, patterns[schema]["OPClass"])
            for node_id in dict.fromkeys(node_ids):
                random.seed(node_id)
                try:
                    mutant_text = ASTCodeGenerator().visit(
                        operator_class(copy.deepcopy(ast), node_id).mutate()
                    )
                except Exception:
                    skipped += 1
                    continue
                if mutant_text == origin_text:
                    skipped += 1
                    continue
                bug_id = f"{source.stem}_{schema}_{node_id}_{lines.get(node_id, 0)}"
                folder = EXTRA / bug_id
                folder.mkdir(parents=True, exist_ok=True)
                (folder / f"{bug_id}.v").write_text(mutant_text, encoding="utf-8")
                (folder / f"{bug_id}_origin.v").write_text(origin_text, encoding="utf-8")
                made += 1
    marker.write_text(str(made), encoding="utf-8")
    print(f"extra mutants {made}, skipped {skipped}", flush=True)
    return made


def choose_pairs(observable: dict[str, str], by_id: dict[str, Bug]) -> tuple[list[tuple[Bug, Bug]], str]:
    """All cross-signature pairs when that set is small; otherwise a panel of representatives."""
    groups: dict[str, list[Bug]] = defaultdict(list)
    for bug_id, signature in observable.items():
        groups[signature].append(by_id[bug_id])
    signatures = list(groups)
    cross = sum(
        len(groups[left]) * len(groups[right])
        for left, right in itertools.combinations(signatures, 2)
    )
    if 0 < cross <= 800:
        chosen = [
            (left_bug, right_bug)
            for left, right in itertools.combinations(signatures, 2)
            for left_bug in groups[left]
            for right_bug in groups[right]
        ]
        return chosen, f"all {cross} cross-signature pairs"
    reps: list[Bug] = []
    for bugs in groups.values():
        picked: list[Bug] = []
        stems: set[str] = set()
        for bug in bugs:
            if bug.stem not in stems:
                picked.append(bug)
                stems.add(bug.stem)
            if len(picked) == 2:
                break
        if len(picked) < min(2, len(bugs)):
            for bug in bugs:
                if bug not in picked:
                    picked.append(bug)
                    break
        reps.extend(picked)
    return list(itertools.combinations(reps, 2)), (
        f"representative panel of {len(reps)} bugs "
        f"({cross} cross-signature pairs would be the full set)"
    )


def run_strict(workers: int) -> None:
    made = generate_extra()
    print(f"newly identified mutants: {made}", flush=True)
    bugs = load_bugs(include_extra=True)
    print(f"total mutants: {len(bugs)}", flush=True)
    origins = shared_origins(bugs)
    by_id = {bug.bug_id: bug for bug in bugs}
    cache: dict[str, tuple] = {}
    golden_status, golden_sig, golden_seconds = simulate(
        [str(path) for path in source_list([], origins, cache)]
    )
    print(f"clean status={golden_status} sig={golden_sig} seconds={golden_seconds:.2f}", flush=True)
    if golden_status not in {"ok", "watchdog"} or not golden_sig:
        raise SystemExit("clean design produced no signature")

    jobs = [
        (bug.bug_id, [str(path) for path in source_list([bug], origins, cache)])
        for bug in bugs
    ]
    print(f"simulating {len(jobs)} singles on {workers} workers", flush=True)
    single_results = run_pool(jobs, workers)
    rows = []
    observable: dict[str, str] = {}
    for bug_id, status, signature, seconds in sorted(single_results):
        changed = status in {"ok", "watchdog"} and bool(signature) and signature != golden_sig
        rows.append(
            {
                "bug_id": bug_id,
                "file": by_id[bug_id].filename,
                "operator": by_id[bug_id].schema,
                "status": status,
                "signature": signature,
                "changes_output": int(changed),
                "seconds": f"{seconds:.2f}",
            }
        )
        if changed:
            observable[bug_id] = signature
    STRICT.mkdir(parents=True, exist_ok=True)
    write_rows(STRICT / "singles.csv", rows)
    class_rows = []
    grouped: dict[str, list[str]] = defaultdict(list)
    for bug_id, signature in observable.items():
        grouped[signature].append(bug_id)
    for signature, ids in sorted(grouped.items(), key=lambda item: -len(item[1])):
        class_rows.append(
            {
                "signature": signature,
                "count": len(ids),
                "files": " ".join(sorted({by_id[bug_id].filename for bug_id in ids})),
                "example": ids[0],
            }
        )
    write_rows(STRICT / "classes.csv", class_rows)
    print(f"observable singles: {len(observable)} / {len(bugs)} in {len(grouped)} output classes", flush=True)

    selected, how = choose_pairs(observable, by_id)
    stackable_pairs = [pair for pair in selected if stackable(pair, origins)]
    print(f"pairs: {how}; stackable {len(stackable_pairs)} of {len(selected)}", flush=True)
    jobs = []
    for left, right in stackable_pairs:
        label = f"{left.bug_id}+{right.bug_id}"
        jobs.append((label, [str(path) for path in source_list([left, right], origins, cache)]))
    pair_results = run_pool(jobs, workers)
    detail = []
    counts: dict[str, int] = defaultdict(int)
    hidden_incidents = 0
    for label, status, signature, seconds in pair_results:
        ids = label.split("+")
        if status not in {"ok", "watchdog"} or not signature:
            kind, hidden_ids = "error", ""
        else:
            kind, hidden_ids = classify(
                signature,
                {bug_id: observable[bug_id] for bug_id in ids},
                golden_sig,
            )
        counts[kind] += 1
        if kind in {"masked", "all_hidden_or_cancelled"} and hidden_ids:
            hidden_incidents += len(hidden_ids.split())
        detail.append(
            {
                "bugs": label,
                "status": status,
                "signature": signature,
                "class": kind,
                "hidden_bugs": hidden_ids,
                "seconds": f"{seconds:.2f}",
            }
        )
    write_rows(STRICT / "pairs.csv", detail)
    print(
        "pair classes: "
        + ", ".join(f"{name}={count}" for name, count in sorted(counts.items()))
        + f", hidden_bug_incidents={hidden_incidents}",
        flush=True,
    )
    print(f"wrote {STRICT}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("probe", "run", "strict"))
    parser.add_argument("--max-order", type=int, default=0, help="highest combination size; 0 means as far as the budget allows")
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 4) - 2))
    parser.add_argument("--pair-budget", type=int, default=8000, help="max 2-bug sims to launch in one run")
    args = parser.parse_args()

    if not Path(IVERILOG).is_file() or not Path(VVP).is_file():
        raise SystemExit(f"Icarus not found at {IVERILOG}")
    prepare_rtl()
    if args.mode == "strict":
        run_strict(args.workers)
        return
    bugs = load_bugs()
    print(f"mutants on disk: {len(bugs)}", flush=True)
    origins = shared_origins(bugs)
    by_id = {bug.bug_id: bug for bug in bugs}
    cache: dict[str, tuple] = {}

    golden_sources = source_list([], origins, cache)
    print("simulating clean design...", flush=True)
    golden_status, golden_sig, golden_seconds = simulate([str(path) for path in golden_sources])
    print(f"clean status={golden_status} sig={golden_sig} seconds={golden_seconds:.2f}", flush=True)
    if golden_status not in {"ok", "watchdog"} or not golden_sig:
        raise SystemExit("clean design produced no SRAM signature")

    if args.mode == "probe":
        sample = bugs[:2]
        for bug in sample:
            status, sig, seconds = simulate([str(path) for path in source_list([bug], origins, cache)])
            changed = sig != golden_sig
            print(f"probe {bug.bug_id} status={status} changed={changed} seconds={seconds:.2f}", flush=True)
        return

    jobs = []
    for bug in bugs:
        sources = [str(path) for path in source_list([bug], origins, cache)]
        jobs.append((bug.bug_id, sources))
    print(f"simulating {len(jobs)} single bugs on {args.workers} workers...", flush=True)
    started = time.perf_counter()
    single_results = run_pool(jobs, args.workers)
    single_seconds = time.perf_counter() - started
    rows = []
    observable: dict[str, str] = {}
    for bug_id, status, signature, seconds in sorted(single_results):
        changed = status in {"ok", "watchdog"} and signature != golden_sig and signature != ""
        rows.append(
            {
                "bug_id": bug_id,
                "file": by_id[bug_id].filename,
                "operator": by_id[bug_id].schema,
                "status": status,
                "signature": signature,
                "changes_output": int(changed),
                "seconds": f"{seconds:.2f}",
            }
        )
        if changed:
            observable[bug_id] = signature
    write_rows(RESULTS / "singles.csv", rows)
    print(
        f"observable singles: {len(observable)} / {len(bugs)} "
        f"in {single_seconds:.1f}s",
        flush=True,
    )

    observable_bugs = [by_id[bug_id] for bug_id in sorted(observable)]
    summary = []
    # k = 1 is the observable count. Higher k walks combinations until the
    # next order no longer fits in the pair budget scaled by order.
    max_order = args.max_order or len(observable_bugs)
    for order in range(2, max_order + 1):
        space = math.comb(len(observable_bugs), order)
        if space > args.pair_budget:
            print(
                f"stopping at order {order}: {space} combinations exceeds budget {args.pair_budget}",
                flush=True,
            )
            summary.append(
                {
                    "order": order,
                    "combinations": space,
                    "stackable": "not_run",
                    "simulated": 0,
                    "masking_cases": "not_run",
                    "hidden_bug_incidents": "not_run",
                    "cancelled_to_clean": "not_run",
                    "new_signature": "not_run",
                    "errors": "not_run",
                }
            )
            break
        raw = list(itertools.combinations(observable_bugs, order))
        chosen = [combo for combo in raw if stackable(combo, origins)]
        print(
            f"order {order}: combinations {len(raw)} stackable {len(chosen)}",
            flush=True,
        )
        if not chosen:
            summary.append(
                {
                    "order": order,
                    "combinations": len(raw),
                    "stackable": 0,
                    "simulated": 0,
                    "masking_cases": 0,
                    "hidden_bug_incidents": 0,
                    "cancelled_to_clean": 0,
                    "new_signature": 0,
                    "errors": 0,
                }
            )
            break
        if len(chosen) > args.pair_budget and order >= 2:
            print(
                f"stopping at order {order}: {len(chosen)} sims exceeds budget {args.pair_budget}",
                flush=True,
            )
            summary.append(
                {
                    "order": order,
                    "combinations": len(raw),
                    "stackable": len(chosen),
                    "simulated": 0,
                    "masking_cases": "not_run",
                    "hidden_bug_incidents": "not_run",
                    "cancelled_to_clean": "not_run",
                    "new_signature": "not_run",
                    "errors": "not_run",
                }
            )
            break
        jobs = []
        for combo in chosen:
            label = "+".join(bug.bug_id for bug in combo)
            sources = [str(path) for path in source_list(list(combo), origins, cache)]
            jobs.append((label, sources))
        combo_results = run_pool(jobs, args.workers)
        masking = hidden = cancelled = novel = errors = 0
        detail_rows = []
        for label, status, signature, seconds in combo_results:
            ids = label.split("+")
            if status not in {"ok", "watchdog"} or not signature:
                errors += 1
                kind, hidden_ids = "error", ""
            else:
                kind, hidden_ids = classify(signature, {bug_id: observable[bug_id] for bug_id in ids}, golden_sig)
            if kind == "masked":
                masking += 1
                hidden += len(hidden_ids.split())
            elif kind == "all_hidden_or_cancelled":
                cancelled += 1
                hidden += len(hidden_ids.split())
            elif kind == "new_signature":
                novel += 1
            detail_rows.append(
                {
                    "bugs": label,
                    "status": status,
                    "signature": signature,
                    "class": kind,
                    "hidden_bugs": hidden_ids,
                    "seconds": f"{seconds:.2f}",
                }
            )
        write_rows(RESULTS / f"order_{order}.csv", detail_rows)
        summary.append(
            {
                "order": order,
                "combinations": len(raw),
                "stackable": len(chosen),
                "simulated": len(combo_results),
                "masking_cases": masking,
                "hidden_bug_incidents": hidden,
                "cancelled_to_clean": cancelled,
                "new_signature": novel,
                "errors": errors,
            }
        )
        print(
            f"order {order}: masking_cases={masking} hidden_bug_incidents={hidden} "
            f"cancelled={cancelled} new={novel} errors={errors}",
            flush=True,
        )
    write_rows(RESULTS / "summary.csv", summary)
    avg = single_seconds / max(len(bugs), 1)
    print(f"average single-bug wall time per worker-job: see singles.csv; batch {single_seconds:.1f}s for {len(bugs)} on {args.workers} workers ({avg:.2f}s amortized)", flush=True)
    print(f"wrote {RESULTS}", flush=True)


if __name__ == "__main__":
    main()
