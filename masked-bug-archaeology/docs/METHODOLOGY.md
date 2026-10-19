# Methodology: Masked-Bug Archaeology

Authoritative methods document for the archaeology track. Every external
claim is cited; every citation was verified against the primary source
(paper abstract/full text) in October 2026 unless marked otherwise.
Companion documents: `SOURCES.md` (full bibliography),
`OPENTITAN_BRIEFING.md` (target-project facts), `RESEARCH_PLAN.md`
(phases and gates).

---

## 1. Research questions

**RQ1 — Day-one detectability.** For a real taped-out design (OpenTitan
Earlgrey blocks), what fraction of the block's *actual historical bugs*
could its *day-one verification environment* (first functional testbench
+ regression suite) have detected — and for those it could not, which
funnel stage blocked detection?

**RQ2 — Masking structure among real bugs.** When two real bugs are
injected together and replayed against a historical testbench, how often
does one bug mask the other's detection, how often does the pair produce
an emergent (new) failure signature, and what structural laws do the
interacting pairs obey?

**RQ3 — Transfer of software composition laws.** Do the empirical laws
discovered for software higher-order mutants — small interaction order,
N+1 containment, code-proximity of interacting pairs — hold for hardware
bug pairs? (This is a hypothesis test, not an assumption.)

Outcomes are always attributed through the three-stage detection funnel:

```
P(found) = P(activate) x P(propagate to a checker) x P(checker fails)
   (a) not activated          (b) activated, not propagated   (c) propagated, not checked
   ... and (d) detected.
```

**Novelty phrasing (important — see §7):** the contribution is the
*conjunction*: (i) real historical bug pairs, (ii) replayed against the
project's own day-one environment, (iii) with per-bug funnel attribution.
Each ingredient alone exists in prior work (§2, §3); the conjunction does
not, per an extensive search in Oct 2026.

---

## 2. Pillar 1 — Software mutation science (the grounding we inherit)

Hardware verification has no published masked-bug statistics. Software
testing does. Our study is the hardware translation of a mature research
program; every design decision below traces to a specific paper.

### 2.1 The coupling effect — does killing simple bugs imply catching complex ones?

**Offutt, "Investigations of the Software Testing Coupling Effect,"
ACM TOSEM 1(2), 1992.** <https://doi.org/10.1145/125489.125473>

- *Method:* build a test suite that kills every first-order mutant
  (single small edit); then exhaustively generate all 2nd- and 3rd-order
  mutants (two/three edits combined) and check whether the same suite
  kills them.
- *Key results:* 1-order-adequate suites killed **94%** of 903 2-order
  mutants (MAX) and **~99%** of 10,388 2-order mutants (MID); 99% of
  12,341 3-order mutants. Also: only ~**1%** of 2-order mutants are
  equivalent (undetectable) vs ~10% of 1-order mutants — combining
  faults *hides* them from the equivalence problem too.
- *Limitations:* tiny C functions; probabilistic conclusion; hand
  analysis on a small sample; no replication-with-contradiction exists
  in the literature.
- *Why our method works (the license this paper grants):* a testbench
  that catches single bugs mostly catches coupled pairs — so *measuring
  single-bug detectability of the day-one TB* is a meaningful estimator
  of its power against the real, mixed bug population. RQ1 stands on
  this. RQ2 then measures the residual **6–27%** where coupling fails —
  exactly the masked-bug territory. The hardware version of Offutt's
  number does not exist; we produce it.

**Just et al., "Are Mutants a Valid Substitute for Real Faults in
Software Testing?" FSE 2014.** <https://doi.org/10.1145/2635868.2635929>

- *Method:* 357 real faults from 5 open-source Java programs (~321 KLOC);
  measure whether mutants couple to *real* faults (not just to other
  mutants), controlling for coverage.
- *Key results:* **73%** of real faults are coupled to at least one
  mutant; **17%** couple to none (a hard detection floor); ~2 mutants
  per real fault on average; correlation between mutation score and
  real-fault detection survives coverage controls.
- *Use:* this is the validity argument every mutation-based claim needs.
  Our design answers it directly: we use *real* bugs (from OpenTitan's
  git history) as the fault population — not synthetic mutants — and we
  cross-check synthetic mutant results against real-bug results
  (Phase 3c). Where synthetic and real disagree, real wins and the
  disagreement is itself a finding.

### 2.2 Higher-order mutation — the taxonomy of bug interaction

**Jia & Harman, "Higher Order Mutation Testing," IST 51(10), 2009**
(<https://doi.org/10.1016/j.infsof.2009.04.016>) and **SCAM 2008**
(<https://doi.org/10.1109/SCAM.2008.36>).

- *Contribution:* the vocabulary we adopt for pair outcomes. Two edits
  combined can be: **expected** (joint effect ≈ union), **worsening**,
  **fault masking** (one hides the other), or **fault shifting** (an
  emergent third behavior). They also formalize *strongly subsuming*
  higher-order mutants (SSHOMs) — pairs strictly harder to detect than
  either constituent.
- *Numbers:* 2-order mutants are ~10x less likely to be equivalent than
  1-order (inheriting Offutt's data); search finds SSHOMs effectively.
- **Langdon, Harman, Jia, GPCE 2009**
  (<https://dl.acm.org/doi/10.1145/1654995.1655061>): genetic search
  found a 7th-order tcas mutant killed by only 1 of 1,608 tests —
  proof that interacting faults can be *individually invisible to
  almost an entire suite*. This is the existence proof for the risk our
  research quantifies.
- **Harman et al., "Angels and Monsters," ASE 2014**
  (<https://doi.org/10.1145/2642937.2643008>): from 15,792 first-order
  mutants, replacing subsumed ones with SSHOMs cut mutant counts 35–45%
  while *improving* test effectiveness 5.6–12% — "trivial faults combine
  into monsters."
- **Wong et al., ESEC/FSE 2020**
  (<https://doi.org/10.1145/3368089.3409713>): exhaustive SSHOM
  enumeration discovered *composition laws*: >90% of SSHOMs are built
  from ≤4 first-order mutants; **96–99% obey the N+1 containment rule**
  (a subset of the pair is itself subtle); constituents are almost
  always in the same method/class (proximity effect).
- *Use:* RQ2's outcome taxonomy (masked / emergent / independent) is
  Jia & Harman's, operationalized for simulation traces. RQ3 tests the
  N+1 and proximity laws on RTL bug pairs — neither law has ever been
  measured outside software. Our own AXI experiment already gives a
  hardware prior: 4,179 masked / 3,472 emergent of 7,675 stackable
  synthetic pairs (see §4.4), i.e. both phenomena are *massive* in RTL —
  the software literature had no reason to predict such large emergent
  fractions.

### 2.3 Masking measurement done right — the reachability discipline

**Diniz et al., "Do Mutations of Strongly Subsuming Second-Order
Mutants Really Mask Each Other?" ISSRE 2023.**
<https://doi.org/10.1109/ISSRE59848.2023.00079>

- *Method:* the only paper that *audits* claimed masking. For each
  subtle 2-order mutant, analyze whether the killing tests actually
  **execute both mutations**: Reachmax (both always executed ⇒ masking
  possible), Reachmin (one never executed ⇒ no masking — plain
  subsumption), Reachint.
- *Key result:* only **53.5%** of claimed-subtle pairs show possible
  masking; **43.5%** are artifacts — one mutation is never even
  executed. Nearly half of "subtlety" was stimulus poverty, not
  interaction.
- *Use:* **this is the methodological template for Phase 3b.** Every
  "masked" verdict in our pair replays gets a reachability audit: did
  the day-one stimulus actually execute both bug sites, or did the bug
  simply sit in a hole the day-one TB never visited? The distinction is
  the difference between "the testbench was present but blinded" and
  "the testbench never went there" — two different remedies, two
  different papers.

### 2.4 Interaction statistics from real systems — the prior we test against

**Kuhn, Wallace & Gallo, "Software Fault Interactions and Implications
for Software Testing," IEEE TSE 30(6), 2004.**
<https://doi.org/10.1109/TSE.2004.24>

- *Method:* classify 329 field failures from a NASA distributed system
  by the number of concurrent conditions needed to trigger (FTFI).
- *Key results:* cumulative detection by n-way interactions:
  **67.5% at 1-way, 93.3% at ≤2-way, 98.8% at ≤3-way, 100% at ≤4-way.**
  Medical-device recalls (same authors' earlier work): 97% pairwise.
- **ICRSE 2017 double-fault study** (<https://doi.org/10.1109/ICRSE.2017.8030752>):
  probability of two injected faults interfering **<1%**, but
  interference is *non-random* — interfering pairs concentrate on the
  same variable.
- **Debroy & Wong, ISSRE 2009** (<https://doi.org/10.1109/ISSRE.2009.14>):
  across multiple-fault injections, *failure masking occurs more often
  than new-failure creation* — no interference form dominates
  unconditionally.
- *Use:* these give the testable priors for RQ2/RQ3: (i) most bugs are
  single-bug phenomena; (ii) interactions cluster locally (same
  signal/always-block/module — our analogue of "same variable"); (iii)
  masking should outnumber emergence (our AXI prior disagrees — 45%
  emergence — which is itself a finding to resolve in Phase 3b).

### 2.5 Supporting software results

- **Trivial Compiler Equivalence line** (Papadakis et al., ICSE 2015,
  <https://doi.org/10.1145/2737924.2737965>): **7.4%** of mutants are
  equivalent and **21% are duplicates** of other mutants — nearly a
  third of synthetic faults are redundant. Our pair panel must dedupe
  signatures before statistics (we do: the 1,042-bug single-class in
  the AXI data is exactly this phenomenon).
- **Test-suite reduction safety** (Rothermel & Harrold, TSE 1998;
  STVR 2002): minimizing suites by *coverage* loses real fault-detection
  power — coverage-equivalent tests are not fault-equivalent. Grounds
  our claim that coverage-based "day-one TB strength" is an unreliable
  proxy for real detectability (the core motivation for replaying real
  bugs instead of trusting coverage numbers).
- **Test dependence masks faults** (Zhang et al., ISSTA 2014,
  <https://dl.acm.org/doi/10.1145/2610384.2610404>): dependent tests
  *mask program faults* — in-simulation analogue: an early UVM error
  aborting a test before bug B's window. Our funnel records this as
  class (c)-with-truncation.
- **Sanitizer shadowing** (ASanity, IEEE S&P Workshops 2023,
  <https://doi.org/10.1109/SPW59333.2023.00037>): re-running 814 fuzzing
  reports with recover-mode sanitizers found **~4.7%** had shadowed
  *more severe* bugs behind the first crash — the closest security
  analogue of our masking question, and evidence the phenomenon is
  real, consequential, and under-measured outside software testing.

---

## 3. Pillar 2 — Hardware and safety-verification neighbors

*(All verified against primary sources, Oct 2026. Full annotations in
SOURCES.md.)*

- **BugMAPI** (Lee, Bertacco et al., Michigan+IBM Haifa, DAC 2016,
  <https://doi.org/10.1145/2897937.2898072>): probabilistic *single-bug*
  masking-rate estimation for post-silicon test programs, 77% accuracy
  at 3 orders of magnitude speedup. Proof that masking estimation is a
  legitimate, publishable target. Difference: one bug at a time,
  post-silicon, probabilistic, no history replay.
- **Certitude / Testbench QA** (industrial; DVCon "Who's Watching the
  Watchmen?"): the activation/propagation/detection funnel is their
  published taxonomy; up to **30%** of injected faults never propagate
  to any checker in industrial flows. Synthetic mutants only, one fault
  at a time. Our funnel stages (a)-(d) deliberately reuse their
  vocabulary — the novelty is *not* the funnel (§7).
- **JasperGold FSV fault-pair analysis** (DVCon ISO 26262 paper):
  formal tools *do* analyze fault pairs — but for *dominance collapsing*
  (Prime Faults) to prune simulation lists (29.5% average fault-list
  reduction). Pairwise analysis exists; pairwise masking *statistics*
  are not reported.
- **ATPG fault collapsing** (Akers, IEEE D&T 1992,
  <https://doi.org/10.1109/54.124518>; textbook dominance relations):
  dominance = one-directional masking at the gate level ("every test
  for the dominated fault catches the dominator"). **Conceptual bridge:**
  RTL bug-masking under a testbench is the sequential, environment-
  relative generalization of dominance; our results measure the
  *empirical dominance structure of real bugs under a real TB* — a
  quantity gate-level tools approximate statically.
- **Radiation double-fault campaigns** (SEU+SET mutual masking, ISCAS
  2014; dual-bit MBU, Electronics 2025): pairwise masking *rates* exist
  for **synthetic radiation faults** (e.g., 303,161 dual-bit MBU
  injections; 98.63% masking on AES workloads). This is why any "first
  pairwise masking rates" claim must be scoped to *logic bugs* — real,
  design bugs — not fault models generally.
- **ISO 26262 multi-point faults**: the standard *names* the category
  (faults dangerous only in combination); tooling classifies single
  faults only (application-safe rates: 20% CPU / 11% UART / 13% CAN in
  the AutoSoC benchmark study, Electronics 2022). No published
  multi-point interaction empirics at RTL. Safety standards are thus a
  *consumer* of exactly the measurement we propose (latent-fault /
  dual-point metrics need pair data).
- **Real-project interaction evidence:** IBM POWER9 (DATE 2020, Kolan
  et al.): 4% of bugs found post-silicon, **30.9% concentrated in one
  unit** — defect clustering is real and unit-level; Tampere FST (MECO
  2024): 28% of bugs slip milestones, 340 engineering-days of slip
  cost; **RemembERR** (MICRO 2022, ETH): >40% of 2,563 real CPU errata
  need two distinct trigger types combined — the strongest existing
  evidence that multi-trigger (i.e., interaction-prone) bugs are the
  norm, not the exception, in real silicon.
- **VeriBugBench / MANTRA** (DAC 2023; arXiv 2609.18022, submitted to
  TCAD): 19 mutation operators *mined from real RTL bug-fix histories*;
  2,608 executable single-fault instances; shipped testbenches observe
  only 36–39.5% of injected faults. The fault substrate for our
  synthetic arm — and, per §7, the concurrent-work threat to monitor.

---

## 4. The method, end to end

### 4.0 Design summary

```
 Phase 1          Phase 2            Phase 3a          Phase 3b          Phase 4
 bug database --> day-one env  -->  single-bug  --->  pair masking  ->  statistics &
 (purified)       (reconstructed)   replay + (a)-(d)  matrix + reach.   law testing
                                      |                  |
                                      +--> synthetic-mutant cross-check (Phase 3c)
```

Two environments only are ever used: the **day-one environment**
(time-zero TB + suite + constraints, reconstructed from git) and, as a
control, the **current environment**. Bugs are the independent
variable; environments are fixed instruments; outcomes are attributed
per funnel stage. All replay is seeded and deterministic; every buggy
run is paired with a clean control run on the identical build to filter
flakiness (CDC races etc.).

### 4.1 Phase 1 — Purified bug database

- Source: `git log` mining already produces 297 candidates across
  uart/hmac/kmac/spi_device (188 after DV-only flagging).
- Purification: (i) commit↔issue cross-reference via the OpenTitan
  tracker (issues carry test/seed/stage evidence); (ii) exclude
  cosmetic/debug commits by diff inspection; (iii) two-annotator
  labeling of a 30-bug sample (trigger description, suspected funnel
  stage, found-by) with inter-annotator agreement reported — the
  protocol Just et al. used for real-fault validity.
- Output: `data/bugs.csv` — one row per bug: block, fix sha(s), date,
  days-from-time-zero, files/functions touched, found-by, issue link,
  annotation fields.
- Gate: ≥30 clean bugs in ≥2 blocks.

### 4.2 Phase 2 — Day-one environment reconstruction

- Time zero per block: the earliest commit where the block's DV is
  declared functional. For uart this is pinned: DV exists from the very
  first public commit `802543a5ec` (2019-08-31, full UVM env +
  scoreboard + 17 vseqs, Makefile/FuseSoC era).
- Fallback (documented, not hidden): if the literal day-one flow cannot
  be revived (tool drift), freeze a "synthetic day-one" at a tagged
  milestone and report sensitivity between the two definitions.
- Instrument spec recorded: test list, seed policy, checker inventory,
  coverage model at time zero.
- Gate: day-one suite runs end-to-end on clean RTL at HEAD-undo
  (regression green on known-good historical commits).

### 4.3 Phase 3a — Single-bug replay (RQ1)

For each bug b: construct buggy variant = revert of the fix commit(s)
on its parent tree; run day-one suite with original seeds; classify:

- (d) detected — any test/checker/assertion fails
- (c) propagated, not checked — outputs differ from golden but no
  checker complains (checker-side diffing of dumps/traces)
- (b) activated, not propagated — internal state diverges (instrumented
  probes / waveform diff) while checked outputs match
- (a) not activated — no divergence anywhere (bug site never executed
  or trigger never hit)

Control: clean build same seeds; runs whose control fails are voided
(flakiness filter). Each classification is decided by evidence, not
intuition: (b) vs (a) requires probe instrumentation; (c) requires an
output diff that no checker consumes.

### 4.4 Phase 3b — Pair masking matrix (RQ2)

- Pair selection: all stackable pairs among replayed bugs within a
  block, up to compute budget, prioritized (i) cross-signature pairs,
  (ii) same-module pairs (tests the proximity law), (iii) random
  cross-module pairs. Stackability = non-overlapping source edits
  (same rule as our AXI study).
- Outcome per pair (Jia & Harman taxonomy, operationalized):
  *masked* (joint output ≡ one member's solo output), *emergent*
  (matches neither), *independent/additive*, *error*.
- **Reachability audit (Diniz protocol):** for every masked verdict,
  determine whether the day-one stimulus executed both bug sites
  (instrumented coverage on the two reverted hunks). Report
  Reachmax/Reachmin/Reachint separately. A "masked" pair with Reachmin
  is reclassified as *day-one stimulus hole*, not causal masking.
- Outputs: `data/pairs.csv` + masking rate per block with binomial CIs;
  N+1 and proximity tests (RQ3); funnel-stage histogram of masked
  members.

### 4.5 Phase 3c — Synthetic cross-check

Run the same day-one suite against VeriBugBench-style synthetic mutants
of the same blocks. Compare per-TB detection rates: real bugs vs
synthetic mutants. Software precedent predicts real faults are harder
(Just 2014's 17% uncoupled floor). Quantifying the hardware gap between
mutation score and real-bug detectability is a standalone result — it
grades the entire industrial practice of mutation-based TB qualification.

### 4.6 Phase 4 — Analysis and threats

- RQ1: day-one detection power over time (does the 50/25/12.5 decay
  curve appear when detection power, not raw counts, is measured?);
  per-funnel-stage masked fractions; correlation of day-one *coverage*
  with day-one *detectability* (tests the coverage-as-proxy assumption
  that Rothermel/Harrold's results already challenge in software).
- RQ2/RQ3: masking rates with CIs; interaction-order and proximity
  statistics vs Wong et al.'s laws; emergent-vs-masked ratio vs Debroy &
  Wong's prior; Kuhn-style cumulative FTFI analogue (how many
  concurrent conditions did escapes need?).
- Threats to validity (pre-registered):
  1. keyword-mined bug list may over/under-count → issue-tracker
     purification + manual audit sample (Phase 1);
  2. day-one reconstruction may be imperfect → sensitivity analysis
     day-one vs milestone-frozen; report both;
  3. one project → replicate on ≥2 blocks with different profiles
     (uart small/mature, kmac crypto/large) and, if feasible, one
     non-OpenTitan design (CVA6);
  4. Icarus/Verilator vs original VCS semantics → seed policy and
     X-propagation differences documented; spot-check verdicts under a
     second simulator where licensing allows;
  5. single-bug replay can itself mask (a reverted fix's neighborhood
     may have moved) → diff-inspection gate per replay; moved-code bugs
     replayed against the tree they were found in, not HEAD.

---

## 5. Compute plan (scales to any available PC)

The workload is *embarrassingly parallel* (independent compilations +
simulations), bounded by RAM per worker (~0.5–1 GB for block-level
UVM-ish envs) and CPU cores. No GPU is used by the simulators
(Icarus/Verilator are CPU-bound; the 2060 is irrelevant to simulation
itself — honest note — though useful later for LLM-assisted test
generation if we go there).

| Machine | Cores/threads | RAM | Est. throughput (block-level sims) | Suitable roles |
|---|---|---|---|---|
| Laptop i5-13500H (current rig) | 16T | 16 GB | ~1.5 s/sim, 14 workers ≈ **30–34k sims/hr** | pilot blocks (uart, hmac); Phase 1–2 dev |
| Desktop i5-11th gen, 40 GB, RTX 2060 | ~12T (6C/12T typical) | 40 GB | ~20–25k sims/hr | kmac/spi_device pair matrices; RAM headroom for chip-level envs |
| Any additional Linux PC / CI runners | scales linearly | ≥1 GB/worker | add ~2.5k sims/hr per worker | farm expansion; identical scripts |

Planning numbers (from the measured AXI pilot): full cross-signature
pair enumeration for one block ≈ 391k sims ≈ **12–16 h on the laptop
alone**; the archaeology pair panels (≤ a few thousand pairs per block,
since real-bug populations are ~15–82 per block) fit in **minutes to a
couple of hours per block**. The expensive part is not compute — it is
replay engineering (Phase 2). Disk: ~50 GB free covers work trees for
all four blocks; keep simulation products under `work/` (gitignored).

Software stack per machine: Python 3.12 venv (requirements.txt),
Icarus Verilog (or Verilator for blocks Icarus can't build), git with
`core.longpaths=true`, OpenTitan clone at a short path (`C:\cv\opentitan`
on Windows). The replay toolkit must run from `scripts/env.ps1`
(Windows) or a plain venv (Linux) — no other dependencies.

---

## 6. Why this is a real scientific process (one paragraph, with receipts)

Every load-bearing choice is inherited from peer-reviewed precedent:
real-bug-based fault populations (Just FSE 2014; MANTRA DAC 2023),
pair-combination taxonomy (Jia & Harman IST 2009), masking-vs-subsumption
auditing (Diniz ISSRE 2023), reachability discipline (same), interaction
census methodology (Kuhn TSE 2004), validity threats from suite-reduction
literature (Rothermel & Harrold), and funnel attribution from industrial
fault injection (Certitude DVCon). The design is pre-registered in this
document (phases, gates, priors, threats) before replay results exist;
all raw data (bug DB, replay verdicts, seeds, logs) is committed or
regenerable from committed scripts; every number in every doc traces to
a script under `survey/`/`replay/` — no hand-copied counts (rules of the
road in RESEARCH_PLAN.md).

---

## 7. Novelty statement and concurrent work (read before writing any abstract)

**Claim (precise form):** *First measurement, on a real taped-out
design, of (i) the fraction of a project's historical bugs detectable by
its own day-one verification environment, and (ii) pairwise masking and
emergence rates among those real bugs — with per-bug funnel-stage
attribution and reachability auditing.*

**Do NOT claim** (all false or contested, per the Oct 2026 search):
- "first funnel attribution" — that taxonomy is Certitude's published
  industrial standard;
- "first pairwise masking rates" flat — synthetic-fault pairwise rates
  exist (SEU+SET ISCAS 2014; dual-bit MBU 2025);
- "first real-bug replay on testbenches" — VeriBugBench replays
  real-bug-derived single faults on testbenches (36–39.5% observability
  finding).

**Concurrent-work watch:** the MANTRA/VeriBugBench group (NUDT/
Chongqing/Shanghai Polytechnic) has every ingredient one step away
(real-bug operators, replayable instances, observability metrics) and
published a new preprint Sep 2026. Cite them prominently as concurrent
related work; our differentiators are *pairs* (they are explicitly
single-fault), *historical day-one environments* (they use current
benches), and *funnel attribution with reachability auditing*. Stake
the flag fast; the pilot (10 bugs, 1 block, hand-replayed) is the
priority artifact.
