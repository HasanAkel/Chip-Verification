# Proposed: Mutation-Operator Fidelity Against Real OpenTitan Bugs

**Status:** proposed future work (2026-10-18). Not started; no results claimed.
**Track:** bridges [`../../masked-bug-injection/`](../../masked-bug-injection/)
(synthetic mutants) and this track (real bug history).
**Citation discipline:** every external number below was verified against the
primary source on 2026-10-18 (author's abstract, paper full text, or arXiv
HTML), except where explicitly marked. See "Relation to prior work" and
"Novelty check" for what was and was not found.

---

## Motivation

Both experiments in this repo rest on a fault model nobody has validated for
RTL at the source-code level. The injection track generates synthetic bugs by
applying VeriBugBench's 19 real-bug-derived mutation operators; the
archaeology track replays real bugs from OpenTitan's git history. The two
populations — "edits an operator can make" and "edits humans actually made" —
are assumed to overlap enough that conclusions transfer between them. That
assumption is precisely what software testing research spent a decade
measuring, and the answer was nuanced: mutants are a useful but imperfect
substitute for real faults [Just et al., FSE 2014], and the degree of
substitution depends strongly on *which* mutation operators are used [Gay &
Salahirad, ICST 2023].

This proposal measures, on OpenTitan, whether bug insertion (mutation) is a
reliable proxy for real bugs — the hardware analogue of Just et al.'s study —
in three directions: can operators reproduce real bug fixes (replicability),
do generated mutants correspond to real bugs (realism), and do operator
frequencies match real bug-category frequencies (distribution match).

The measurement is cheap, reuses existing infrastructure end to end, and is
decision-relevant: it either *licenses* the synthetic pair experiments at
scale (fidelity high) or *re-routes* the program toward archaeology-only
(fidelity low). Both outcomes are publishable.

---

## Research questions

**RQ-A (replicability).** What percentage of OpenTitan's real RTL bug-fix
diffs can be reproduced by existing mutation operators — VeriBugBench's 19
real-bug-derived operators plus standard HDL operators?

*Method.* Population: the RTL-only bug-fix commits in
[`survey/candidate_bug_fixes.csv`](../survey/candidate_bug_fixes.csv)
(297 keyword-mined candidates across uart/hmac/kmac/spi_device, of which 188
are flagged non-DV-only as of 2026-10-18; final counts follow the Phase-1
purification of `docs/RESEARCH_PLAN.md`). For each commit: extract the fix
diff from the OpenTitan clone (`C:\cv\opentitan`, parent-tree context, not
HEAD); parse the *buggy* (pre-fix) file with the VeriBugBench PyVerilog AST
machinery already vendored in `../masked-bug-injection/patches/veribugbench/`;
restrict candidate sites to the hunks the diff touches; enumerate
operator applications; declare a bug *reproduced* when a generated edit
script matches the human fix. Two strictness tiers, reported separately:

- **T1 — site+operator match:** some operator produces a plausible edit at
  the same AST construct (the human fix falls inside the operator's
  generative space).
- **T2 — exact edit match:** the generated edit normalizes to the human diff
  (same replacement value/predicate/case-arm).

Output: one row per commit — reproduced tier, reproducing operator(s), AST
category of the fix, block. Per-operator hit rates fall out of the same table.

**RQ-B (realism).** What percentage of generated synthetic mutants correspond
to some real bug — by syntactic similarity of the edit and/or behavioral
equivalence of the failure?

*Method.* Stratified sample from RQ-A's census (reproduced-T1,
reproduced-T2-only, non-reproduced), sized by F2's compute budget.
*Behavioral equivalence* = run the real-bug RTL and the candidate
synthetic-mutant RTL on the **same testbench build with the same seeds** and
compare failure signatures, reusing the classification funnel of
[`docs/METHODOLOGY.md`](METHODOLOGY.md) §4.3 (classes (a)–(d): not activated /
not propagated / propagated-not-checked / detected) and the trace-hash
signature machinery proven in the AXI experiment
(`masked-bug-injection/lab/axi_mask_search.py`: 2,619 mutants simulated,
signatures hashed from handshake traces + memory dumps). Equivalence tiers,
loosest to strictest: same funnel class → same failing-test set → same
failure-signature hash. A mutant counts as *realistic* only if the edit site
also matches the real fix (T1); behaviorally-identical mutants at unrelated
sites are reported as a separate, marginal count — they validate the testbench
signal, not the fault model. Testbench: whatever build the archaeology track
has validated at that time (current-at-HEAD first; the day-one environment
becomes available with Phase 2).

**RQ-C (distribution match).** Do operator frequencies match the frequencies
of real bug categories in OpenTitan's history?

*Method.* Label each real fix with a bug category (FSM/reset/CDC/off-by-one/
indexing/operator-swap/…), assigned from the diff's AST category plus commit
text, with two-annotator labeling on a sample and agreement reported (the
protocol Just et al. used). Compare the real-category distribution against
(i) the distribution of operators *needed* to reproduce those fixes (RQ-A)
and (ii) the operator frequencies mutation-based flows actually generate,
using rank correlation plus per-category residuals. A category that is common
in real history but rare (or absent) under the operator set is the actionable
output: e.g., VeriBugBench's own library defines no operator for 449 of 8,756
expression-level AST categories (5.13%: `FunctionCall`, `PARAMETRIZATION`)
[arXiv:2609.18022, §IV-C], and whether such constructs matter in *OpenTitan's*
fixes is an empirical question RQ-C answers directly.

---

## Experiment design

```
 F1: syntactic replication census  -->  F2: behavioral equivalence  -->  F3: distribution
 (all RTL-only fix diffs,          (stratified sample; same TB,      analysis + write-up
  AST matching only, no sims)       same seeds, signature compare)
```

**F1 — Syntactic replication census (RQ-A).** No simulation: diff extraction,
AST parsing, operator enumeration, edit-script normalization, matching.
Human audit of a 30-commit sample (agreement rate reported), as everywhere
else in this repo. *Gate:* proceed to F2 with any tier-1 population ≥ 10%;
a near-zero census is itself a headline result and routes straight to F3
plus the archaeology-only conclusion.

**F2 — Behavioral equivalence sample (RQ-B).** Simulation, the only
compute-consuming phase. Per sampled bug: build buggy variant (revert of the
fix on its parent tree) + the candidate reproducing mutants; run both on the
same TB build and seeds; clean-control runs void flaky verdicts (same
discipline as `docs/METHODOLOGY.md` §4.3). Deliverable: a joint table —
syntactic tier × behavioral tier — that no published RTL work has.

**F3 — Distribution analysis (RQ-C).** Category labeling, correlation
statistics, per-operator and per-category residual report; fold results into
both tracks' docs and, if warranted, a standalone paper.

---

## Expected compute

Laptop-class throughout; no new infrastructure.

- **F1** is CPU-bound Python AST work over ≤ 188 small diffs — hours, not
  days, dominated by the audit sample.
- **F2** reuses the proven pattern from the AXI experiment: 2,619 mutant
  simulations ran on this laptop (i5-13500H, 16 threads) in a single
  afternoon at the measured ~30–34k sims/hr block-level throughput
  (`docs/METHODOLOGY.md` §5). The F2 budget (hundreds of bugs × few tests ×
  2 variants) is one to two orders of magnitude below that pilot.
- Disk and tooling identical to the existing tracks: `scripts/env.ps1`
  environment, Icarus Verilog, OpenTitan at `C:\cv\opentitan`, VeriBugBench
  checkout at `C:\cv\VeriBugBench` with the Windows patches from
  `masked-bug-injection/patches/veribugbench/` already applied by
  `scripts/setup_laptop.ps1`.

---

## Relation to the existing tracks

- **masked-bug-injection (parked):** this study gives its pair-matrix
  experiments a *validated fault model* — or shows the model is not valid, in
  which case the 3,472-of-7,675 emergent-signature result needs a real-bug
  replication before anyone builds on it. High fidelity licenses cheap
  synthetic pair experiments at scale; low fidelity retires them.
- **masked-bug-archaeology (this track):** it operationalizes the Phase-3c
  synthetic cross-check of `docs/METHODOLOGY.md` §4.5, upgrading "compare
  per-TB detection rates" into a per-commit, per-operator explanation of
  *why* the rates differ. If fidelity is LOW, mutation-based testbench
  qualification *underestimates real-bug blindness* — the headline argument
  for the archaeology approach. If HIGH, the archaeology conclusions can be
  extended cheaply with synthetic faults.

**Both outcomes are publishable, and neither is a null result.** Low fidelity
is the hardware analogue of Just et al.'s 17%-uncoupled floor — a warning
that mutation-score-based sign-off arguments have a blind spot. High fidelity
is the first out-of-distribution validation of real-bug-derived HDL mutation
operators.

---

## Novelty honesty

The syntactic portion of RQ-A is *adjacent* to what MANTRA and VeriBugBench
could already do with their own datasets: VeriBugBench already reports a
"distributional consistency" check of its operators against its own
bug-fix corpus [arXiv:2609.18022]. Our differentiators, stated plainly:

1. **Out-of-distribution evaluation.** The operators were learned from
   OpenCores-family bug histories (1,298 retained bug-fix commit records
   across 300 Verilog projects [arXiv:2609.18022, §I]); we test them against
   OpenTitan — a different project, style, and verification culture — whose
   independent bug history was never in the training data. VeriBugBench's own
   threats-to-validity section names exactly this gap: *"Evaluation against
   an independent RTL bug-fix corpus remains future work"* (§VIII-B1). This
   proposal *is* that future work.
2. **Behavioral failure-signature equivalence** under identical testbench and
   seeds (RQ-B). Neither MANTRA nor VeriBugBench compares real-bug and
   mutant behavior; VeriBugBench's instances are explicitly single-fault and
   retention is defined by output observability, not equivalence to any real
   bug. Our searches (below) found no RTL work doing this.
3. **It validates or devalidates the fault model of our own experiments** —
   a self-audit the benchmark papers have no reason to run.

### Novelty check (searches run 2026-10-18)

Queries: *"real bugs mutation operators hardware Verilog fidelity"*, *"CirFix
mutation coverage"*, *"VeriBugBench fidelity"*, plus follow-ups on every hit.
**No published or preprint work was found that measures the fidelity of HDL
mutation operators against an independent real hardware bug history, in
either the syntactic or the behavioral direction.** Closest items found, none
of which covers the proposal:

- *Software, operator-level coupling:* Gay & Salahirad, "How Closely are
  Common Mutation Operators Coupled to Real Faults?", ICST 2023
  (<https://doi.org/10.1109/ICST57152.2023.00021>) — 32,002 mutants from 31
  Java operators vs 144 Defects4J faults: 9.92% of mutants strongly coupled,
  51.03% of faults with ≥1 strongly coupled mutant. Same *question* shape as
  RQ-A/RQ-B, software only.
- *Software, empirically-derived operators underperform:* Hans, Kettl &
  Winter, "Empirical Fault Patterns for Mutation Testing", EASE 2025
  (<https://doi.org/10.1145/3756681.3756963>) — operators derived from
  empirical defect distributions were *easier to detect and less coupled with
  real defects* than traditional operators on Defects4J in the majority of
  cases. A directly relevant warning for RQ-C: being "real-bug-derived" does
  not by itself make operators faithful.
- *Hardware, same-corpus only:* VeriBugBench's distributional consistency
  analysis (its operators vs the corpus they were mined from), with the
  independent-corpus evaluation explicitly deferred (above).
- *Hardware, different question:* VERMEI (arXiv:2508.15536,
  <https://doi.org/10.48550/arxiv.2508.15536>) uses equivalent mutation to
  test FPGA *synthesis tools* — tool bugs, not design-bug fidelity.

---

## Threats and limitations

1. **Operator-set coverage.** A "not reproduced" verdict is evidence about
   the operator set *plus* the matching strictness, not proof the human edit
   is outside operator space; the standard-operator arm narrows but does not
   close this. Fidelity numbers are lower bounds on coverage.
2. **Syntactic matching may miss semantic equivalents.** An operator may
   reproduce a bug's *behavior* through a different edit (T2 misses, RQ-B
   catches); conversely, behaviorally-identical mutants at wrong sites are
   not realism. We therefore never claim fidelity from behavior alone —
   the "realistic" verdict requires site match AND behavioral match, with
   marginals reported.
3. **Single-project scope.** One project (OpenTitan), four blocks. The
   operators were learned on OpenCores-style code; distribution mismatch may
   partly reflect style, not operator weakness. Replication on a second
   history (e.g., CVA6, already in this track's scope) is the natural v2.
4. **Commit purity.** The 188 non-DV-only commits still include refactors and
   feature-fixes until Phase-1 purification supersedes the list; percentages
   will be restated on the purified set, and multi-commit single bugs are
   counted once where detectable.
5. **Testbench-relative equivalence.** Failure-signature equality is defined
   by the TB build and seeds used (the same limitation the injection track
   documents); a "behaviorally equivalent" verdict is relative to that build,
   and stronger equivalence (formal) is out of scope.
6. **Simulator semantics.** Icarus verdicts may differ from the original
   (VCS-era) CI behavior; seed policy and X-propagation caveats carry over
   from `docs/METHODOLOGY.md` §4.6.

---

## Relation to prior work

The citations below were verified against primary sources on 2026-10-18.
This study is the hardware analogue of Just et al.: they asked whether
*tests that kill mutants* also detect real faults (coupling); we ask whether
*operators* generate the edits humans actually make (fidelity). The two are
complementary — coupling licenses inferring real-fault detection from mutant
detection [Offutt 1992]; fidelity licenses inferring real-bug coverage from
operator coverage — and neither implies the other.

- **Just, Jalali, Inozemtseva, Ernst, Holmes, Fraser, "Are Mutants a Valid
  Substitute for Real Faults in Software Testing?", FSE 2014.**
  <https://doi.org/10.1145/2635868.2635929> — 357 real faults from 5 Java
  programs (~321 KLOC); mutants couple to 73% of real faults; 17% couple to
  *no* mutant; ~2 mutants coupled per real fault on average. The direct
  software precedent for RQ-A/RQ-B.
- **MANTRA (Wu, Lei, Zhang, Meng, Yang, Li, He, Mao), "Mutation Testing of
  Hardware Design Code Based on Real Bugs," DAC 2023.**
  <https://doi.org/10.1109/DAC56929.2023.10247962> — first open-source
  code-level HDL mutation tool based on real hardware bugs; 19 operators from
  large-scale empirical analysis of real bugs; maximum boost 83.44% on the
  CirFix/OpenCores datasets. We test those operators *out-of-distribution*
  and add behavioral-equivalence checking, which MANTRA does not do.
- **VeriBugBench (Meng, Feng, Zhao, Zhang, Lei, Mao, Wu), arXiv:2609.18022
  (Sep 2026, submitted to IEEE TCAD).** <https://arxiv.org/abs/2609.18022> —
  45 projects, 2,608 executable single-fault instances, 19 executable inverse
  operators derived from 1,298 retained bug-fix commit records across 300
  Verilog projects; shipped testbenches observe only 36.01–39.54% of injected
  faults; operator library covers 8,307/8,756 expression-level AST categories
  (94.87%). Source of the mutation machinery; its own future-work note
  (§VIII-B1) names the independent-corpus evaluation this proposal performs.
- **CirFix (Huang et al.), "CirFix: Automatically Repairing Defects in
  Hardware Design Code," ASPLOS 2022.** <https://doi.org/10.1145/3503222.3507763>
  — benchmark of **32 expert-transplanted real-world Verilog defect scenarios
  across 11 projects** (six course projects + five from OpenCores/GitHub);
  CirFix produced plausible repairs for 21/32 and correct repairs for 16/32.
  (Note: the benchmark is 32 transplanted scenarios, *not* ~226 raw OpenCores
  bugs as sometimes assumed; the "as used by MANTRA" framing is from MANTRA's
  own evaluation section.) The datasets MANTRA's operators were validated on
  — i.e., the in-distribution baseline our out-of-distribution claim is
  measured against.
- **Offutt, "Investigations of the Software Testing Coupling Effect," ACM
  TOSEM 1(2), 1992.** <https://doi.org/10.1145/125489.125473> — coupling
  effect background; fidelity (this proposal) and coupling are complementary
  axes of mutant-validity.
- **Andrews, Briand, Labiche, "Is Mutation an Appropriate Tool for Testing
  Experiments?", ICSE 2005.** <https://doi.org/10.1109/ICSE.2005.1553583> —
  generated mutants behaved similarly to real faults, while *hand-seeded*
  faults were harder to detect than real ones; mutation is a defensible
  fault source *when its fidelity is checked* — exactly the check proposed
  here. Verified: the often-quoted claim "hand-seeded faults harder to detect
  than real faults" is in the abstract verbatim.
- **Gay & Salahirad, ICST 2023** and **Hans, Kettl & Winter, EASE 2025** —
  see "Novelty check" above; the software state of the art this proposal
  extends to RTL.

For the ML-for-masked-bugs state of the art (verified 2026-10-19: no direct
prior exists — the nearest neighbors and the open gap are catalogued in
[SOURCES.md](SOURCES.md), section "ML that predicts masked/hidden bugs").
