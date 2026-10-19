# Chip Verification Research — Masked Bugs in RTL Verification

Owner: [@HasanAkel](https://github.com/HasanAkel) · Teammates: Omar-ocorp, Mohamed-Aaqib, salimakell

**The question this project answers:** when a hardware design's testbench
finds bug A, how many bugs like B never got found *because* the testbench
couldn't see past A — and how do we measure, predict, and fix that?

Two complementary tracks:

| Track | Folder | Status | What it does |
| --- | --- | --- | --- |
| **Masked-bug archaeology** | [`masked-bug-archaeology/`](masked-bug-archaeology/) | **active** | Replays a real chip's historical bugs against its own day-one testbench and measures, for the first time, what the early environment could and couldn't detect — with per-bug funnel attribution (not activated / not propagated / not checked) and pairwise masking/emergence statistics |
| Masked-bug injection (parked) | [`masked-bug-injection/`](masked-bug-injection/) | runnable, parked | Synthetic pair study: 2,619 mutants on an OpenCores AXI4 interconnect, 7,675 stackable pairs → 4,179 masked / 3,472 emergent signatures. Proof-of-concept that masking and emergence are measurable at scale |

## Why it matters

- **Nobody publishes masked-bug rates for real hardware bugs.** Software
  testing has a 30-year literature on fault coupling and higher-order
  mutation (Offutt 1992 → Just 2014 → Wong 2020); hardware has single-fault
  injection tools (Certitude), single-bug probabilistic masking (BugMAPI),
  and synthetic radiation-fault pair studies — but never *real bug pairs
  replayed against the project's own historical testbench*. That cell of
  the table is empty. We are filling it. (`masked-bug-archaeology/docs/METHODOLOGY.md` §7)
- The payoff is practical: a measured "day-one blindness" number per
  block grounds risk at sign-off, tells teams how much testbench
  investment actually bought, and gives masked-bug *detectors* a
  baseline to beat.

## The instrument: OpenTitan

[OpenTitan](https://github.com/lowRISC/opentitan) is an open-source root-of-trust
security chip (Earlgrey) that taped out in Oct 2024 — the only chip whose
entire RTL, UVM testbenches, nightly regression history, and bug-by-bug
git history are public. We cloned the full history (2,500 days) and mined
it:

- **297 candidate RTL bug-fix commits** across uart/hmac/kmac/spi_device
  (188 after flagging testbench-only commits) — the study population
- UART's day-one testbench pinned to the **first public commit**
  (`802543a5ec`, 2019-08-31): full UVM env + scoreboard + 17 sequences
- Full verified dossier: block sizes, release-tag timeline, regression
  infrastructure, replay pitfalls — `masked-bug-archaeology/docs/OPENTITAN_BRIEFING.md`

## Method in one paragraph

Reconstruct the day-one testbench from git (Phase 2) → revert each
historical bug's fix on its parent tree and replay the day-one suite with
the original seeds (Phase 3a) → classify each bug through the detection
funnel: (a) not activated, (b) activated-but-not-propagated, (c)
propagated-but-not-checked, (d) detected (Phase 3a) → inject bug pairs
and measure masked vs emergent outcomes with reachability auditing
(Phase 3b) → cross-check synthetic mutants vs real bugs (Phase 3c) →
test whether software's composition laws (interaction order ≤4, N+1
rule, same-code proximity) hold for hardware (Phase 4). Full protocol,
priors, threats, and compute plan (laptop → desktop → farm): 
[`masked-bug-archaeology/docs/METHODOLOGY.md`](masked-bug-archaeology/docs/METHODOLOGY.md).

## Evidence base (all primary-source verified, Oct 2026)

Key grounding, full citations in
[`masked-bug-archaeology/docs/SOURCES.md`](masked-bug-archaeology/docs/SOURCES.md):

| Finding | Source |
| --- | --- |
| 1-order-adequate tests still kill 94–99% of 2-order mutants (the license for single-bug replay) | [Offutt, TOSEM 1992](https://doi.org/10.1145/125489.125473) |
| 17% of real faults couple to *no* mutant — real bugs ≠ mutants | [Just et al., FSE 2014](https://doi.org/10.1145/2635868.2635929) |
| 43.5% of "subtle" fault pairs never execute both members — masking audits need reachability checks | [Diniz et al., ISSRE 2023](https://doi.org/10.1109/ISSRE59848.2023.00079) |
| Real-system interactions: 93.3% of failures ≤2 conditions, 100% ≤4 (the prior we test in RTL) | [Kuhn et al., TSE 2004](https://doi.org/10.1109/TSE.2004.24) |
| >40% of 2,563 real CPU errata need combined triggers | [RemembERR, MICRO 2022](https://comsec-files.ethz.ch/papers/rememberr_micro22.pdf) |
| Bug masking is estimable: 77% accuracy at 1000x speedup (post-silicon, single bug) | [BugMAPI, DAC 2016](https://doi.org/10.1145/2897937.2898072) |
| ~30% of injected faults never reach any checker in industrial flows | Certitude DVCon ("Who's Watching the Watchmen?") |
| 30.9% of POWER9 post-silicon bugs in one unit — defect clustering is real | [Kolan et al., DATE 2020](https://doi.org/10.23919/DATE48585.2020.9116491) |

## Repo layout

```
masked-bug-archaeology/     ACTIVE TRACK
  docs/METHODOLOGY.md       full protocol, priors, threats, compute plan
  docs/RESEARCH_PLAN.md     phases, deliverables, go/no-go gates
  docs/SOURCES.md           verified bibliography (with corrections log)
  docs/OPENTITAN_BRIEFING.md  target-chip dossier (confidence-tagged)
  env/check_env.py          track readiness check
  survey/count_commits.py   OpenTitan bug-history miner (retry-hardened)
  survey/candidate_bug_fixes.csv  297 bugs mined, DV-only flagged
  survey/block_rtl_lines.csv      measured RTL size of all 41 hw/ip blocks
masked-bug-injection/       PARKED TRACK (still runnable)
  lab/                      pipe teaching lab + AXI pair-masking search
  patches/veribugbench/     Windows fixes for VeriBugBench/PyVerilog
  docs/LITERATURE_AND_STATUS.md   AXI run numbers + regression literature
scripts/                    env.ps1 (activate), setup_laptop.ps1 (bootstrap)
```

## Quick start (Windows laptop)

```powershell
winget install Git.Git Python.Python.3.12 Icarus.Verilog -e   # once
.\scripts\setup_laptop.ps1                                    # once
. .\scripts\env.ps1                                           # every shell
python masked-bug-injection\lab\check_env.py      # injection track still green
python masked-bug-archaeology\env\check_env.py    # needs C:\cv\opentitan clone
python masked-bug-archaeology\survey\count_commits.py   # regenerate the bug survey
```

## Status & next steps

- ✅ Phase 0 complete: population mined (297 candidates), target blocks
  sized, day-one UART testbench located, feasibility dossier verified
- ▶️ Phase 1 (bug-database purification via issue tracker) and Phase 2
  (day-one environment reconstruction) — see
  [`masked-bug-archaeology/docs/RESEARCH_PLAN.md`](masked-bug-archaeology/docs/RESEARCH_PLAN.md)
- Pilot target: 10 hand-replayed UART bugs through the funnel, then automate

## License / upstream

Original lab, scripts, and docs are for the team project.
VeriBugBench and imported RTL retain their upstream licenses
(see that project's `LICENSE` / `THIRD_PARTY_NOTICES.md`).
