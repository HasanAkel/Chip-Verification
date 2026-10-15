# Masked Bug Archaeology — Research Plan

Working folder for the empirical masked-bug study. Owner: Hasan.
Sibling project: `../masked-bug-injection/` (synthetic mutants — parked,
kept runnable; its VeriBugBench infra will be reused here).

## The claim we want to measure

On real chips, each successive regression run finds roughly half of the
bugs that remain findable (50 / 25 / 12.5 / ... canonical find/fix decay).
The leading explanations are: proportional depletion of a finite pool
(Jelinski-Moranda / Goel-Okumoto), long-tailed conjunctive triggers
(RemembERR, MICRO'22), stimulus saturation, and the activation ->
propagation -> observation funnel. None of these have been tested against
*replayable* real bug history with the funnel stage attributed per bug.
That is the experiment.

## Target projects (in order of preference)

| Project | Why | Risk |
| --- | --- | --- |
| OpenTitan (lowRISC) | Full RTL + UVM TB + disciplined git history + milestone releases (M1..M6) + public issue tracker; taped out Oct 2024 | Replay infra on Windows; some blocks need Verilator or commercial tools — prefer Icarus-friendly blocks |
| CVA6 (OpenHW) | Regression runs per PR on CI; clean history; Spike golden model | UVM-heavy; may need larger toolchain |
| Ariane (legacy) | Frozen project, finite history | Older methodology |

## Phases

### Phase 0 — Scoping (current)

Goal: pick 1-3 OpenTitan IP blocks where replay is feasible on this laptop
(Icarus Verilog or Verilator), and mine the full bug history for them.

- [ ] Clone OpenTitan, list blocks whose DV is self-contained and
      simulator-friendly (candidates: `uart`, `gpio`, `hmac`, `alert_handler`).
- [ ] For each candidate: count RTL fix commits referencing bugs/issues
      over time (`survey/count_commits.py`), build the candidate bug table.
- [ ] Confirm day-one testbench replays under an available simulator.
- [ ] **Go/no-go:** at least one block with >= 30 replayable bugs and a
      working day-one environment.

### Phase 1 — Bug database construction

Goal: a structured CSV of every bug for the chosen blocks.

Schema (one row per bug):
`block, bug_id, fix_commit, fix_date, days_from_time_zero, files_touched,
lines_changed, trigger_desc, found_by (test/assertion/dv tool), referenced_issue,
milestone_at_discovery`

- [ ] Mine git log: commits under each block dir with fix/bug keywords +
      linked issues (`survey/mine_history.py`).
- [ ] Cross-reference the GitHub issue tracker (labels, milestones).
- [ ] Manual annotation pass on a 20-bug sample: trigger description,
      suspected funnel stage. Agreement check with a second annotator.

### Phase 2 — Time-zero environment reconstruction

Goal: the environment as it existed when the block's TB first worked.

- [ ] Identify time zero per block: first commit where DV doc marks the
      block DV-stage >= V1 or TB "functional" (OpenTitan documents this).
- [ ] Checkout that tree; get its regression running locally.
- [ ] Record its coverage + test list as the "instrument spec".

### Phase 3 — Replay and classification

Goal: per-bug verdict (a)-(d).

- [ ] For each bug: revert its fix commit(s) on top of the earliest sane
      parent -> buggy RTL variant (`replay/build_variant.py`).
- [ ] Run the time-zero suite on the buggy variant; run the clean tree as
      control (flakiness filter).
- [ ] Classify:
  (a) not activated  - suite passes, internal probe never fired
  (b) act., not propagated - internal state differs, outputs match
  (c) propagated, not checked - outputs differ, no test failed
  (d) detected - suite failed
  Internal probes: waveform/state diffing between clean and buggy runs.
- [ ] **Go/no-go:** replay automation handles >= 80% of bugs unattended.

### Phase 4 — Analysis and writeup

- [ ] Detection power of day-one env vs. time (the decay curve, real data).
- [ ] Masked fraction by class (a)/(b)/(c) per block.
- [ ] Correlate day-one coverage with day-one detection (does coverage
      predict real detectability?).
- [ ] Compare real-bug detection rate vs. VeriBugBench/Certitude-style
      mutation score on the same block + TB (bridges to sibling project).
- [ ] Draft: DVCon/DAC-shaped paper, "methodology + first numbers".

## Deliverables

1. `data/bugs.csv` - the annotated bug database (public artifact).
2. `data/replay_results.csv` - per-bug (a)-(d) verdicts.
3. Replay toolkit (works on OpenTitan out of the box).
4. Paper draft + figures.

## Rules of the road

- Every number in a doc must trace to a script in `survey/` or `replay/`
  and raw data in `data/` - no hand-copied counts.
- Simulation products go in `work/` (gitignored), labeled datasets go in
  `data/` (committed).
- Windows-first: everything must run from `.\scripts\env.ps1`-activated
  shells on this laptop; long paths stay under `C:\cv\` if needed.
