# Masked-Bug Archaeology: Detectability, Decay, and the Case for Replaying History

**Project:** masked-bug archaeology on OpenTitan (see `README.md`,
`METHODOLOGY.md`)
**Date:** 2026-10-18
**Status:** research statement — all external claims verified against primary
sources on 2026-10-18; measurements so far are from the sibling AXI injection
track and are clearly labeled. Not yet peer-reviewed.

---

## Executive summary

1. Verification dominates hardware cost [P1], and a regression's detection
   power is bounded by its stimulus and checkers [P2]. Found-bug counts decay
   per cycle [P3] — but decay reflects *catchability*, not absence [P3, P4].
2. Testbench blindness is measurable and large: shipped hardware testbenches
   observe only ~36–39.5% of injected faults [P4]; LLM-generated Verilog
   passing 100% of a suite's tests fails formal equivalence 44.2% of the time
   [P4].
3. Bugs mask each other [P5], fixes induce fixes [P6], so unmasking is
   sequential — it appears in history as fix-chains [P6].
4. Therefore replaying real historical bugs against the day-one testbench
   yields the masked population *with causal attribution* — a controlled
   counterfactual no existing measurement provides [P7].
5. The data does not exist publicly; the infrastructure does (OpenTitan
   history, day-one UART testbench at commit `802543a5ec`, 2019-08-31) [P8].
6. Falsifiable predictions are stated in §7, and the null result — if
   masking is negligible — would itself recalibrate sign-off confidence.

---

## 1. The logical case for masked-bug archaeology

This section is a premise→conclusion chain. Each premise carries its
evidence; assumptions and limitations are stated per premise. Section
references in brackets point to the bibliography at the end of this document.

**P1 — Verification dominates hardware development cost.**
Functional verification — not design — is where schedule and budget go.
Regression execution alone can reach "as much as 70% of the hardware design
costs" [1]; in the 2024 Wilson Research Group survey, only **14%** of
IC/ASIC projects achieved first-silicon success, the lowest in two decades,
and three quarters of projects ship late [2].
*Assumption note:* survey figures are industry self-reports with sampling
uncertainty; the 70% figure is a vendor's upper-bound claim about
regression *execution cost*, not total verification effort.

**P2 — Regression detection is bounded by stimulus and checkers.**
A bug is found only if the environment activates it, propagates its effect
to a checker, and the checker fails. This activation/propagation/detection
funnel is the published industrial taxonomy [3]. The software analogue is
the coupling effect: test sets adequate for single faults mostly cover
multi-fault combinations — Offutt measured 94–99% kill rates on 2nd/3rd-order
mutants by 1-order-adequate suites [4] — which is precisely why the *live
residue* (the 1–6% that coupling does not cover) is the interesting object:
it is the part of the funnel that single-bug adequacy cannot see.
*Assumption note:* Offutt's data is tiny C functions; the hardware version
of the coupling number does not yet exist — we produce it as a by-product.

**P3 — Per-cycle discovery decays, yet decay ≠ absence.**
The DEC VAX debug memorandum tabulates bugs found per silicon pass across
four processors (full table in §2): "The high degree of functionality on
CVAX pass 1 allowed for a classical 'descending exponential' bug rate.
Nonetheless, the tail proved very long, with several bugs showing up in
pass 4" [5]. Rex Black's find/fix planning model canonicalizes the software
pattern (50/25/12.5/6.25/3.1 percent-per-cycle) and flags deviations as
scope or test-design problems [6]. Malka & Ziv's continuous analysis of two
PowerPC processors reached the same shape over 68 billion cycles [7].
But all three sources contain the counter-evidence in their own text:
the VAX tail persisted to passes 4–5 [5]; Black's model attributes decay to
*the tests, not the code* ("a flat shape across cycles indicates
lower-yield tests running too early"); and Malka & Ziv caught Laplace
factors *rising* between 200 and 500 million cycles when testing of a major
new function began — discovery intensity follows testbench attention, not
just depletion [7]. Decay therefore measures *reduced catchability by the
current environment*, not exhaustion of the bug population.
*Assumption note:* the VAX memo is a 1991 internal document (not
peer-reviewed) covering circuit-level silicon debug; we use it as
qualitative evidence for the decay shape and the long tail.

**P4 — Testbench blindness is measurable and large.**
VeriBugBench — 45 open-source projects, 2,608 executable single-fault
instances built from real bug-fix histories — reports that project
testbenches observe only **36.01–39.54%** of injected faults, and that
figure is *after* LLM-based testbench enhancement [8]. RealBench found
**44.2%** of GPT-4-Turbo-generated Verilog that *passes* RTLLMV2's
testbenches fails formal equivalence checking [9]. Certitude-style fault
injection in industrial flows reports up to ~30% of faults classified NP —
"never propagate" to any checker — and that these faults "would typically
be reported as covered using code or functional coverage metrics" [3].
*Assumption note:* VeriBugBench and Certitude numbers are for synthetic
faults (VeriBugBench's derived from real fix patterns) on heterogeneous
projects; blindness on any specific design may differ — which is why we
measure, not assume.

**P5 — Bugs mask each other, measurably.**
The first direct audit of mutual masking (Diniz et al., ISSRE 2023) found
that of strongly-subsuming 2-order mutants, **53.52%** are Reachmax (mutual
masking possible), **43.47%** Reachmin (one mutation never executed — no
masking, plain stimulus hole), **3.01%** Reachint [10]. In multi-fault
software injection, masking is observed more often than new-failure
creation [11]. Two-fault interactions have a formal taxonomy — expected,
worsening, **fault masking**, fault shifting [12]. And in real silicon,
RemembERR's 2,563 Intel/AMD errata show triggers are *conjunctive* — more
than 40% of bugs are uncovered only when two distinct trigger types combine
[13].
*Assumption note:* all direct masking measurements are software-mutant or
synthetic-fault studies; the hardware real-bug version is exactly our
measurement (§6).

**P6 — Fixes induce fixes, so unmasking is sequential.**
Yin et al. found **14.8–24.4%** of sampled post-release bug fixes in four
large operating systems are incorrect — they introduce new bugs [14].
The Bristol DV lecture notes put the regression tax compactly: "every bug
fix, on average, introduces one fifth of a bug" [15]. If a fix introduces
bugs at these rates, then the bug population is not static under testing:
each fix can unmask (or create) the next bug, and the masking structure —
which bug was hiding behind which — is laid down sequentially in the
project's history as fix-chains. This is what makes *archaeology* (replay
of historical order) a valid instrument: the information is in the
sequence.
*Assumption note:* Yin et al. sampled OS code, not RTL; the "one fifth"
figure is a teaching heuristic, not a measurement. The RTL analogue is part
of what our replay data will show.

**P7 — Therefore: replaying real historical bugs against the day-one
testbench yields the masked population with causal attribution.**
Combining P2–P6: the day-one environment's detection power is the funnel
(P2); decay made late bugs invisible to it (P3); blindness is large (P4);
masking is real and structured (P5); and history recorded the order in
which bugs were actually found and fixed (P6). Replaying each historical
bug — revert its fix on its parent commit, run the day-one suite, classify
(a) not-activated / (b) activated-not-propagated / (c) propagated-not-checked
/ (d) detected — converts that history into a controlled counterfactual:
*what would have happened had this bug existed at time zero?* Replaying
pairs of real bugs jointly extends this to *mutual masking with
attribution* — per-bug funnel-stage attribution plus a Diniz-style
reachability audit separating true interaction from stimulus holes [10].
No existing measurement provides this: VeriBugBench is single-fault against
current benches [8]; Certitude is synthetic single faults [3]; BugMAPI
estimates single-bug masking probabilistically, post-silicon [16];
RemembERR has no testbench and no replay [13].
*Assumption note:* keyword-heuristic mining may over- or under-count the
bug population (mitigated by issue-tracker purification and a manual audit
sample); replay validity depends on the faithfulness of day-one
reconstruction (mitigated by a sensitivity analysis against a
milestone-frozen environment); one project limits generalizability
(mitigated by four structurally different blocks: uart/hmac/kmac/
spi_device).

**P8 — The data does not exist publicly; the infrastructure does.**
A two-agent literature check (2026-10-18, independent searches) found no
published work that injects *pairs of real historical bugs* into RTL and
replays them against the project's own historical day-one testbench with
activation/propagation/observation attribution. Nearest neighbors:
VeriBugBench (real-bug-derived faults, single-fault) [8], Certitude
(funnel taxonomy, synthetic single faults) [3], BugMAPI (masking,
single-bug, post-silicon) [16], and ISCAS 2014 SEU+SET mutual masking
(synthetic radiation faults) [17]. The novelty is the *conjunction*, not
any single ingredient — the funnel taxonomy itself is Certitude's [3].
Meanwhile the substrate exists in the open: OpenTitan's full public
history, with the UART's day-one UVM environment present from the first
public commit `802543a5ec` (2019-08-31) [18], and the sibling AXI
injection track has already exercised the replay-and-classify pipeline
end to end (§6).

**Conclusion.** Given P1–P8: a real, previously-unmeasured population —
the bugs a project's day-one environment could not see — can be measured
retrospectively with causal attribution, on public data, with existing
infrastructure. The output is (i) a number ("the day-one environment was
blind to X% of this block's eventual bugs"), (ii) the funnel-stage
distribution of why, and (iii) the first masking statistics for real RTL
bug pairs.

---

## 2. Evidence I — bugs found per regression cycle (discrete counts)

The discrete framing asks: *how many bugs did each regression cycle (or
silicon pass) find?* The canonical hardware data is the DEC VAX debug
memorandum [5] — Bob Supnik, "VLSI CPU Bugs: A Comparative Analysis
(Revised)," 10-Dec-1991, preserved by the SIMH computer-history project
(verified reachable 2026-10-18). "Pass" is the silicon pass in which the
bug was fixed. Total passes+minipasses (CVAX includes the CMOS-2 shrink
bug-fix pass):

| | uVAX | CVAX | Rigel | NVAX |
|---|---|---|---|---|
| passes+minipasses | 5+11 | 5+11 | 6+1 | 2+0 |

Bugs found per pass [5, §5], reproduced verbatim:

| pass: | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| uVAX | 6 | 11 | 10 | 3 | 3 |
| CVAX | 19 | 7 | 7 | 3 | |
| Rigel | 7 | 4 | 1 | 2 | 2 |
| NVAX | 15 | 3 | | | |

The memo's own conclusions [5, §7], quoted precisely:

> "The high degree of functionality on CVAX pass 1 allowed for a classical
> 'descending exponential' bug rate. Nonetheless, the tail proved very long,
> with several bugs showing up in pass 4. Rigel showed a similar curve, with
> several bugs showing up in pass 4 and 5. Only NVAX finally broke through
> this barrier."

> "The significantly increased verification efforts on Rigel and NVAX were
> repaid by significantly reduced bug rates."

Three readings matter. First, the decay is real but the tail is long —
CVAX's pass 4 still found 3 bugs. Second, decay is *attributable*:
NVAX's two-pass debug reflects deliberate verification investment (and a
patchable control store that "allowed debug on first pass parts to proceed
further and find more problems"), not luck. Third, the new-function hump is
already visible discretely: "the microcode bug rate actually got worse,
despite better tools, because of the addition of new functionality (eg,
vectors, IB error handling, etc)" [5, §7]. Supnik's CHM oral history
corroborates the phenomenon from memory: "as the bug rates declined, the
kinds of bugs we found became sort of more and more on the fringes" [19].

The software planning analogue is Rex Black's find/fix model [6]: the
canonical per-cycle pattern 50 / 25 / 12.5 / 6.25 / 3.1 / 3.0 / acceptance,
i.e. each cycle finds half of what remains. The page is explicit that
deviations are diagnostic: "Programs that do not match this shape usually
have a scope problem (regression re-opening bugs) or a test-design problem
(same tests running cycle after cycle)." This is a planning model with a
calibration philosophy, not a published measurement corpus — but it is the
form in which the industry actually consumes per-cycle decay.

The continuous contrast is Malka & Ziv (§3): same overall decay, but their
Laplace-test analysis shows intensity responding to *testbench attention*
(the 200–500-million-cycle hump on Processor A [7]), which a per-cycle
table shows only as the microcode-bug hump the VAX memo records.

**The gap:** no modern chip project publishes per-regression-cycle or
per-pass bug counts. Errata databases carry no pass attribution (RemembERR
processed 2,563 errata since 2008 — none indexed by discovery cycle [13]);
Wilson/Siemens trend reports publish spins and schedule slips, not per-cycle
counts [2]; project papers (POWER9 [20]) report aggregates. The DEC memo is
the last public table of its kind. Our OpenTitan mining produces the modern
successor: every bug-fix commit carries its date and block, and after
day-one replay carries a detection verdict, giving a per-cycle detection
profile measured with a fixed historical instrument (§6). A fuller
treatment of the discrete-vs-continuous framing, the additional software
per-cycle literature, and the search protocol is in
`docs/BUGS_PER_REGRESSION.md`.

---

## 3. Evidence II — discovery intensity over time (the continuous view)

The continuous framing asks: *at what rate are bugs being discovered per
unit of testing effort?* The canonical source is Malka & Ziv, "Design
reliability — estimation through statistical analysis of bug discovery
data," DAC 1998 [7] — work of IBM Research–Haifa (Haifa, Israel). (This is
the paper informally called "the Israeli paper" in earlier drafts; in
anything formal it should be cited as Malka & Ziv, IBM Research–Haifa,
DAC 1998, DOI 10.1145/277044.277209.)

Their setup: two superscalar PowerPC processors, more than 8 months of
data, 68 billion simulation cycles (Processor A) and 2 billion (Processor
B), several hundred bugs tracked *daily*. Method in two stages: a
Laplace-test trend analysis of reliability growth, followed by fitting
non-homogeneous Poisson process (NHPP) models — Musa–Okumoto, Duane,
Goel–Okumoto. The payoff: they predicted Processor B's bug count and MTTF
three months in advance, and validated the prediction against a further
105 billion cycles and 794 total bugs.

The phenomenon that matters most for this project: on Processor A, Laplace
factors **rose between 200 and 500 million cycles** — reliability
*decreased* mid-campaign. The authors located the cause:

> "When we tried to find the reason for this behavior, we found that this
> time corresponds to the time when testing of a major function of the
> processor started."

Discovery intensity follows testbench attention, not just the remaining
bug population. A decay curve is therefore a statement about the
*joint* state of (a) how many bugs remain, (b) whether current stimulus can
activate them, (c) whether checkers would see them, and (d) what the
testbench is currently pointed at. Regression planning consumes decay
curves as if (b)–(d) were fixed; day-one archaeology is the controlled
experiment that holds (b)–(d) at their time-zero values and varies only
the bug — converting the confounded curve into a measurement.

---

## 4. Evidence III — masking across domains

**Software mutation testing (the inherited foundation).** Offutt's coupling
effect studies: 1-order-adequate suites killed 94–99% of 2nd/3rd-order
mutants [4] — single-bug adequacy mostly covers combinations, and the
residual 1–6% is the masked/interaction territory. Jia & Harman's
higher-order mutation taxonomy names the interaction outcomes: expected,
worsening, fault masking, fault shifting [12]. Debroy & Wong, injecting
multiple faults into real programs, found failure masking occurs *more
often* than new-failure creation [11]. Diniz et al. added the discipline
that makes masking numbers meaningful — a reachability audit. Of strongly
subsuming 2-order mutants: 53.52% Reachmax (both constituents executed by
the killing tests — masking possible), 43.47% Reachmin (one constituent
never executed — no masking; a stimulus artifact), 3.01% Reachint [10].
Nearly half of apparent "subtlety" was stimulus poverty, not interaction —
the exact distinction our funnel classes (a) vs (b)/(c) operationalizes.
And Just et al. anchor the whole enterprise to reality: 73% of 357 real
faults couple to at least one mutant, but 17% couple to *no* mutant [21] —
a hard detection floor that mutation scores alone never see.

**Real-system interaction statistics.** Kuhn, Wallace & Gallo's NASA field
data: failures triggered by n-way interactions — 67.5% single-condition,
93.3% by ≤2-way, 98.8% by ≤3-way, 100% by ≤4-way; medical devices 97% by
pairs [22]. Most failures are single-bug phenomena; a bounded interaction
tail exists and matters. RemembERR's errata census concurs from the
silicon side: triggers are conjunctive, observations disjunctive, and
>40% of bugs need two distinct trigger types combined [13].

**Hardware synthetic-fault evidence.** The Certitude/DVCon funnel —
activation, propagation, detection — with up to ~30% of injected faults
never propagating to any checker [3]. VeriBugBench/MANTRA: real-bug-derived
mutation operators, 2,608 instances, shipped testbenches observe only
36.01–39.54% of injected faults [8]. BugMAPI: probabilistic *single-bug*
masking estimation for post-silicon tests, 77% accuracy, three orders of
magnitude faster than brute force [16]. ISCAS 2014: pairwise mutual
masking measured for SEU+SET *radiation* fault pairs [17].

**Our own synthetic-bug measurements (sibling AXI track, 2026).** On
OpenCores AXI4 with VeriBugBench-derived mutants: 2,619 mutants; 1,374
visible in 88 output classes; pair panel of 7,675 simulations: **4,179
masked**, 3,472 new-signature (emergent), 17 same-signature, 7 errors.
An earlier SRAM-only scoreboard configuration saw only 3 output classes
(142 mutants visible) and produced **zero** new signatures in 9,922 pairs —
the bench, not the design, gates which interactions are even expressible.
Two lessons carry directly into the archaeology protocol: (i) masking and
emergence in RTL are large effects (vs. software priors where masking
dominates [11], we saw ~54% emergence — itself a divergence worth
resolving), and (ii) reachability auditing per Diniz [10] is mandatory,
because an unexecuted bug site masquerades as interaction.

---

## 5. The regression workflow, as verified in practice

The workflow this project assumes (and whose artifacts we mine) is the
standard industrial regression loop:

1. **Nightly regression on master.** The regression suite runs overnight
   against the current integration branch. The University of Bristol DV
   course notes state the purpose plainly: regression exists for
   "assuring that things that worked did not stop working" [15].
2. **Failure triage.** A nightly run ends with failures attributed to
   specific bugs (test, seed, interface).
3. **Fix development off-line.** While a fix for bug X is being developed,
   the nightly continues on master — the trunk does not wait.
4. **Fix validation: smoke test first.** A candidate fix gets a short
   smoke run before expensive validation.
5. **Same-seed replay, then other seeds.** The fix is tested against the
   *same seed and inputs that exposed the original bug* — a controlled
   before/after comparison — and then against additional seeds to check
   it does not merely suppress the symptom at one sample point.
6. **Promotion to master, full testing.** Only then does the fix merge,
   and the full chip-level suite runs on the updated master.

Two properties of this loop matter for archaeology. The **same-seed
replay** is, in miniature, the same controlled counterfactual we perform
at project scale: fix the design, hold the inputs fixed, observe the
difference. And the loop's *sequencing* is why bug-fix commits arrive in a
strict historical order: each fix enters master only after the previous
state's bugs were exposed — which is precisely the order information that
P6 requires and our replay exploits.

---

## 6. Method and measured numbers so far

**Target.** OpenTitan Earlgrey (open-source root-of-trust SoC; tapeout
October 2024), local full-history clone. Mined 297 candidate bug-fix
commits; 188 remain after DV-only filtering; block distribution:
uart 15, hmac 41, kmac 50, spi_device 82. The UART's day-one UVM
testbench exists at the first public commit `802543a5ec` (2019-08-31) —
full environment, not a stub [18].

**Single-bug replay (per bug).** Revert the fix commit on its parent tree →
buggy RTL at its historical point → run the day-one suite with original
seeds → classify: (a) not-activated, (b) activated-not-propagated,
(c) propagated-not-checked, (d) detected. Classes (a)–(c) are the masked
population, each with its funnel-stage cause attributed. A clean same-seed
control run filters flakiness.

**Pair replay (masking).** Stackable pairs of real bugs replayed jointly
against the same day-one suite; outcomes classified masked / emergent /
independent / error, each masked verdict audited for reachability (were
both bug sites executed?) per the Diniz protocol [10] — separating true
interaction from day-one stimulus holes.

**Measured so far (sibling AXI injection track; synthetic mutants, not
OpenTitan real bugs):** as §4 — 2,619 mutants, 1,374 visible, 7,675-pair
panel with 4,179 masked / 3,472 new-signature / 17 same-signature / 7
errors; earlier SRAM-only scoreboard run: 3 output classes, 142 visible,
zero new signatures in 9,922 pairs. The OpenTitan replay itself is the
next milestone; these numbers establish the pipeline and the measurement
categories, not the final rates.

---

## 7. Falsifiable predictions and the value of the null result

**Falsifiable predictions.**

1. **The masked fraction is non-trivial.** Given P4 (36–60% blindness for
   synthetic faults) and P5, we predict a substantial minority — not a
   trace — of real OpenTitan bugs fall in classes (a)–(c) for the day-one
   suite. A single-digit masked fraction across four blocks would falsify
   the transfer of software/hardware-synthetic blindness rates to real
   bugs.
2. **Funnel-stage distribution differs between real bugs and synthetic
   mutants.** Prediction: stage (c) (propagated, not checked) dominates
   for synthetic mutants — built by perturbing design outputs — while
   stage (a) (not activated) dominates for real bugs, whose triggers are
   conjunctive [13]. If both populations show the same stage profile,
   synthetic fault injection is a valid cheap proxy for real-bug
   blindness — itself a useful, publishable result.
3. **Software composition laws hold for RTL pairs.** Following [12] and
   the SSHOM composition laws (interaction order ≤4; N+1 containment;
   same-neighborhood proximity), we predict interacting OpenTitan bug
   pairs concentrate in the same block/subsystem and obey small-order
   composition. Violations would mean hardware bug interactions are
   structurally different from software ones.
4. **Masking vs. emergence.** Software prior (Debroy & Wong [11]): masking
   outnumbers emergence. Our AXI synthetic prior disagrees (3,472 emergent
   vs 4,179 masked — near parity). The OpenTitan real-bug panel decides
   which prior survives on real bugs.

**The null result's value.** If replay shows the day-one environment was
detecting essentially everything it later caught — i.e., masking is
negligible — that is not a failure of the method; it is a *calibration
result*. It would say that (i) regression decay on this project reflects
true depletion rather than testbench blindness, (ii) sign-off confidence
can be read almost directly from the decay curve, and (iii) industrial
testbench-QA investment (Certitude-style fault injection) buys little on
designs like these. Either outcome recalibrates how much a clean regression
history is worth. The same holds for the pivot: if masked bugs turn out
rare, the replay database still supports **predicting bug-prone components
from found-bug locality** — using the archaeology data (which blocks,
files, and change types spawned fixes) as training signal for
change-risk models, predicting where the *next* bug lives from the change
currently being reviewed, rather than from the bug count already found.
The infrastructure — bug database, replay harness, attribution data — is
identical for both outcomes; only the headline changes.

---

## References

Numbered; grouped. All URLs/DOIs verified against primary sources
2026-10-18 unless noted. Full annotations live in `docs/SOURCES.md` and
`docs/METHODOLOGY.md`.

### Methodology and foundations

- [1] G. Parthasarathy, A. Rushdi, P. Choudhary, S. Nanda, M. Evans,
  H. Gunasekara, S. Rajakumar, "RTL Regression Test Selection Using Machine
  Learning," Proc. ASP-DAC 2022, Synopsys. Regression "sometimes [costs] as
  much as 70% of the hardware design costs."
  <https://doi.org/10.1109/ASP-DAC52403.2022.9712550>
- [4] A. J. Offutt, "Investigations of the Software Testing Coupling
  Effect," *ACM TOSEM* 1(2), 1992. 1-order-adequate tests kill 94–99% of
  2nd/3rd-order mutants. <https://doi.org/10.1145/125489.125473>
- [10] J. P. Diniz, F. Ferreira, F. Ferrari, A. B. Vieira, M. A. G. Viggio,
  P. D. L. Machado, R. Abreu, "Do Mutations of Strongly Subsuming
  Second-Order Mutants Really Mask Each Other?" Proc. IEEE ISSRE 2023.
  53.52% Reachmax / 43.47% Reachmin / 3.01% Reachint.
  <https://doi.org/10.1109/ISSRE48739.2023.00023> (preprint:
  <https://labsoft-ufmg.github.io/publications/2023/issre2023preprint.pdf>)
- [12] Y. Jia and M. Harman, "Higher Order Mutation Testing," *Information
  and Software Technology* 51(10), 2009. Taxonomy: expected / worsening /
  fault masking / fault shifting. <https://doi.org/10.1016/j.infsof.2009.04.016>

### Empirical — software

- [6] Rex Black, "The model that says when you will run out of bugs,"
  bug find/fix estimation template, QA Library. Canonical 50/25/12.5/
  6.25/3.1 percent-per-test-cycle decay; deviations signal scope or
  test-design problems.
  <https://rexblack.com/resources/qa-library/bug-find-fix-estimation-template>
- [11] V. Debroy and W. E. Wong, "Insights on Fault Interference for
  Programs with Multiple Bugs," Proc. IEEE ISSRE 2009. Failure masking
  observed more often than new-failure creation.
  <https://doi.org/10.1109/ISSRE.2009.14>
- [14] Z. M. Yin, X. Yuan, Y. Zhou, S. Pasupathy,
  L. N. Bairavasundaram, "How do fixes become bugs?" Proc. FSE 2011.
  "At least 14.8%–24.4% of sampled fixes for post-release bugs in these
  large OSes are incorrect." <https://doi.org/10.1145/2025113.2025121>
- [21] R. Just, D. Jalali, L. Inozemtseva, M. D. Ernst, R. Holmes,
  G. Fraser, "Are Mutants a Valid Substitute for Real Faults in Software
  Testing?" Proc. FSE 2014. 73% of 357 real faults couple to mutants; 17%
  couple to none. <https://doi.org/10.1145/2635868.2635929>
- [22] D. R. Kuhn, D. R. Wallace, A. M. Gallo, "Software Fault Interactions
  and Implications for Software Testing," *IEEE TSE* 30(6), 2004. 67.5%
  1-way, 93.3% ≤2-way, 98.8% ≤3-way, 100% ≤4-way.
  <https://doi.org/10.1109/TSE.2004.24>

### Empirical — hardware

- [5] R. Supnik, "VLSI CPU Bugs: A Comparative Analysis (Revised)," DEC
  interoffice memorandum, 10-Dec-1991. SIMH preservation:
  <https://simh.trailing-edge.com/semi/docs/bug_anal.txt> (mirror:
  <https://mirrors.meulie.net/bitsavers.org/simh.trailing-edge.com_201206/semi/docs/bug_anal.txt>)
- [7] Y. Malka and A. Ziv, "Design reliability — estimation through
  statistical analysis of bug discovery data," Proc. DAC 1998, IBM
  Research–Haifa. Laplace-test trend analysis + NHPP models; Laplace
  factors rose 200–500M cycles when major new function testing started.
  <https://doi.org/10.1145/277044.277209>
- [13] F. Solt, P. Jattke, K. Razavi, "RemembERR: Leveraging Microprocessor
  Errata for Design Testing and Validation," Proc. MICRO 2022, ETH Zurich.
  2,563 Intel/AMD errata since 2008; triggers conjunctive, observations
  disjunctive; >40% of bugs need two trigger types combined.
  <https://comsec-files.ethz.ch/papers/rememberr_micro22.pdf>
- [16] D. Lee, T. Kolan, A. Morgenshtein, V. Sokhin, R. Morad, A. Ziv,
  V. Bertacco, "Probabilistic bug-masking analysis for post-silicon tests
  in microprocessor verification" (BugMAPI), Proc. DAC 2016. 77% accuracy,
  3 orders of magnitude faster; single-bug, probabilistic.
  <https://doi.org/10.1145/2897937.2898072>
- [17] K. Wu, H. Pahlevanzadeh, P. Liu, Q. Yu, "A new fault injection method
  for evaluation of combining SEU and SET effects on circuit reliability,"
  Proc. ISCAS 2014. Pairwise masking for synthetic radiation faults.
  <https://doi.org/10.1109/ISCAS.2014.6865207>
- [19] R. Supnik, interview by G. Hendrie, *Oral History of Robert Supnik,
  part 2*, Computer History Museum, recorded 9 May 2017, CHM ref. X8215.2017.
  <https://archive.computerhistory.org/resources/access/text/2019/07/102740181-05-01-acc.pdf>
- [20] T. Kolan, A. Mendelson, V. Sokhin, P. Reick, E. Tsanko, C. Wetli,
  "Post-Silicon Validation of the IBM POWER9 Processor," Proc. DATE 2020.
  4% of POWER9 bugs found post-silicon (vs 1% POWER8); load-store unit =
  30.9% of post-silicon bugs.
  <https://doi.org/10.23919/DATE48585.2020.9116491>

### Standards, benchmarks, tools

- [2] Wilson Research Group, *2024 IC/ASIC Functional Verification Trend
  Report* (Siemens). 14% first-silicon success; 75% of projects late.
  <https://resources.sw.siemens.com/en-US/white-paper-2024-wilson-research-group-ic-asic-functional-verification-trend-report/>
- [3] D. Brownell, "Who's Watching the Watchmen? The Time has Come to
  Objectively Measure the Quality of Your Verification Environment,"
  DVCon (Synopsys Certitude). Activation/propagation/detection funnel; up
  to ~30% of injected faults classified NP (never propagate to a checker).
  <https://dvcon-proceedings.org/wp-content/uploads/whos-watching-the-watchmen-the-time-has-come-to-objectively-measure-the-quality-of-your-verification-environment.pdf>
- [8] X. Meng, K. Feng, X. Zhao, Z. Zhang, Y. Lei, X. Mao, J. Wu,
  "VeriBugBench: An Empirically Grounded Framework for Constructing Verilog
  RTL Debugging Benchmarks," arXiv:2609.18022, submitted to IEEE TCAD
  (extends MANTRA, Proc. DAC 2023,
  <https://doi.org/10.1109/DAC56929.2023.10247962>). 45 projects, 2,608
  single-fault instances, 19 real-bug-derived operators; observability
  36.01–39.54%. <https://arxiv.org/abs/2609.18022>
- [9] "RealBench: A Firefox-Worthy Benchmark Suite for Real-World Verilog
  Design Verification," arXiv:2507.16200, 2025. 44.2% of GPT-4-Turbo
  Verilog passing RTLLMV2's testbenches fails formal equivalence.
  <https://arxiv.org/abs/2507.16200>
- [15] University of Bristol, *Design Verification* lecture notes,
  "Closing the Cycle." "Assuring that things that worked did not stop
  working"; "every bug fix, on average, introduces one fifth of a bug";
  80/20 coverage-effort split.
  <https://uobdv.github.io/Design-Verification/Lectures/Current/11_Closing_the_Cycle-narrated_v6-plain.pdf>

### Our infrastructure

- [18] OpenTitan (lowRISC et al.), full public development history; UART
  day-one UVM testbench at commit `802543a5eca6895db068bbd8cbb45bb0577c216e`
  (2019-08-31, "Start of public OpenTitan development history").
  <https://github.com/lowRISC/opentitan> — commit verified in the local
  full-history clone on 2026-10-18. Local mined database: 297 candidate
  commits / 188 RTL-only; uart 15, hmac 41, kmac 50, spi_device 82
  (`../survey/`).
- Sibling AXI injection track: measured pair-panel numbers (2,619 mutants;
  7,675 sims; 4,179 masked / 3,472 new-signature / 17 same-signature / 7
  errors; SRAM-only run: 3 classes, 142 visible, 0 new in 9,922 pairs) from
  this repository's `masked-bug-injection/` track (2026).
