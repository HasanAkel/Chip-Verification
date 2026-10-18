# Sources and prior art

What already exists, what it measured, and the gap this project fills.
Only peer-reviewed papers, industry studies, and primary sources.

## The decay phenomenon (what we want to explain/measure)

- Rex Black, "The model that says when you will run out of bugs."
  Canonical 50 / 25 / 12.5 / 6.25 / 3.1 percent-per-cycle pattern used in
  find/fix projection models; deviations signal scope or test-design
  problems.
  <https://rexblack.com/resources/qa-library/bug-find-fix-estimation-template>
- Jelinski & Moranda (1972) and Goel & Okumoto (1979): software
  reliability growth models. Detection rate proportional to remaining
  bugs (JM) or NHPP saturation (GO). The mathematical skeleton of decay.
- University of Bristol DV lecture notes, "Closing the Cycle": the
  80/20 coverage-effort split, and "every bug fix, on average, introduces
  one fifth of a bug" (the regression tax).
  <https://uobdv.github.io/Design-Verification/Lectures/Current/11_Closing_the_Cycle-narrated_v6-ink.pdf>

## Real-bug evidence

- RemembERR (MICRO 2022, ETH Zurich). 2,563 Intel/AMD errata since 2008,
  annotated with triggers / contexts / observations. Key findings:
  triggers are conjunctive, observations disjunctive; >40% of bugs need
  two distinct trigger types combined. Mechanistic basis for the long
  tail of hard-to-trigger bugs.
  <https://comsec-files.ethz.ch/papers/rememberr_micro22.pdf>
- 2024 Wilson Research Group IC/ASIC Functional Verification Trend Report
  (Siemens). Only 14% first-silicon success; logic/functional flaws the
  top respin cause; verification outspends design.
  <https://resources.sw.siemens.com/en-US/white-paper-2024-wilson-research-group-ic-asic-functional-verification-trend-report/>
- Fault-Slip-Through study of a 15mm2 SoC (MECO 2024): 28% of found bugs
  slipped through milestone gates; 340 engineering-days of slip cost.
  <https://doi.org/10.1109/meco62516.2024.10577831>

## Testbench quality / mutation measurement (the synthetic analogue)

- "Who's Watching the Watchmen?" (DVCon, Synopsys Certitude experience):
  activation/propagation/detection classification of injected faults; up
  to ~30% of faults never propagate to any checker; classic holes are
  missing output checks, missing negative checks, single-reset tests.
  <https://dvcon-proceedings.org/wp-content/uploads/whos-watching-the-watchmen-the-time-has-come-to-objectively-measure-the-quality-of-your-verification-environment.pdf>
- RealBench (2025): LLM-generated Verilog passing 100%-line-coverage TBs
  still fails formal equivalence 44% of the time - synthetic/coverage
  metrics diverge from real functional correctness.
  <https://arxiv.org/html/2507.16200>
- Mutation-based test quality lineage: DeMillo/Offutt (software, 1970s+),
  Serrestou et al. DSD 2007 (RTL mutation-driven validation),
  Ikram & Ellis DVCon 2017 (coverage-clustered suites matched Certitude
  fault-detection with fewer tests).

## The gap

Nobody publishes: for a real design, of all bugs found over the project,
what fraction was detectable by the day-one environment, with the funnel
stage (activation / propagation / observation) attributed per real bug.
RemembERR studies silicon escapes from errata sheets (no replay, no TB).
Certitude-style tools inject synthetic faults (not real bugs). This
project measures the missing cell of that table on OpenTitan/CVA6
history, and validates the decay curve against real detection power.

## Software mutation science — the inherited foundation (verified Oct 2026)

All of the following were verified against primary sources (abstract or
full text) in the Oct 2026 literature sweep; full annotations,
methodology, numbers, and limitations are in `METHODOLOGY.md` §2–§3.

**Coupling effect / mutant-to-real-fault validity**
- Offutt, "Investigations of the Software Testing Coupling Effect,"
  ACM TOSEM 1(2), 1992. <https://doi.org/10.1145/125489.125473>
  1-order-adequate tests kill 94–99% of 2-order mutants; ~1% vs ~10%
  equivalence rates (2-order vs 1-order).
- Just et al., "Are Mutants a Valid Substitute for Real Faults in
  Software Testing?" FSE 2014. <https://doi.org/10.1145/2635868.2635929>
  73% of 357 real faults couple to mutants; 17% couple to none;
  ~2 mutants per real fault.
- Andrews et al., ICSE 2005. <https://doi.org/10.1109/ICSE.2005.1553583>
  (mutants ≈ real faults for experiments; hand-seeded harder than real).

**Higher-order mutation — interaction taxonomy and laws**
- Jia & Harman, IST 51(10) 2009. <https://doi.org/10.1016/j.infsof.2009.04.016>
  Taxonomy: expected / worsening / fault masking / fault shifting.
- Jia & Harman, SCAM 2008. <https://doi.org/10.1109/SCAM.2008.36>
  (subsuming and strongly subsuming HOMs, SSHOM fitness).
- Langdon, Harman, Jia, GPCE 2009.
  <https://dl.acm.org/doi/10.1145/1654995.1655061>
  7th-order tcas mutant killed by 1 of 1,608 tests.
- Harman et al., "Angels and Monsters," ASE 2014.
  <https://doi.org/10.1145/2642937.2643008>
  15,792 FOMs; SSHOM substitution: 35–45% fewer mutants, 15% test
  efficiency gain.
- Wong et al., ESEC/FSE 2020. <https://doi.org/10.1145/3368089.3409713>
  Composition laws: >90% of SSHOMs use ≤4 FOMs; 96–99% obey N+1
  containment; same-method proximity.

**Masking measurement discipline**
- Diniz et al., ISSRE 2023.
  <https://doi.org/10.1109/ISSRE48739.2023.00023>
  Reachmax/Reachmin audit of claimed masking: only 53.5% of subtle
  2-order pairs show possible masking; 43.5% never execute one
  mutation (stimulus artifacts, not interaction).
- Debroy & Wong, ISSRE 2009. <https://doi.org/10.1109/ISSRE.2009.14>
  Masking observed more often than new-failure creation.
- Papadakis et al. (TCE), ICSE 2015.
  <https://doi.org/10.1145/2737924.2737965>
  7.4% of mutants equivalent, 21% duplicated.

**Interaction statistics from real systems**
- Kuhn, Wallace & Gallo, IEEE TSE 30(6) 2004.
  <https://doi.org/10.1109/TSE.2004.24>
  NASA field failures: 67.5% single-condition, 93.3% ≤2-way, 98.8%
  ≤3-way, 100% ≤4-way. Medical devices 97% pairwise.
- Double-fault interference, ICRSE 2017.
  <https://doi.org/10.1109/ICRSE.2017.8030752>
  Interference <1% but non-random (same-variable clustering).
- Zhang et al., ISSTA 2014. <https://dl.acm.org/doi/10.1145/2610384.2610404>
  Dependent tests mask program faults (test-masks-test).
- ASanity, IEEE S&P Workshops 2023.
  <https://doi.org/10.1109/SPW59333.2023.00037>
  ~4.7% of 814 fuzzing reports shadowed more-severe bugs (sanitizer
  early-exit masking). Security-domain analogue.

**Test-suite reduction safety (why coverage ≠ detection power)**
- Rothermel, Harrold, Ostrin, Hong, ICSM 1998.
  <https://doi.org/10.1109/ICSM.1998.738487>
- Rothermel & Harrold (with Jeffrey), STVR 2002.
  <https://doi.org/10.1002/stvr.256>
  Coverage-based minimization loses real fault-detection power.

**Modern LLM-era mutation (context / future extension)**
- Khanfir et al. (µBERT), 2023. <https://arxiv.org/abs/2301.03543>
- Garg et al., ICST 2024 (LLM mutants vs vulnerabilities coupling).
  <https://rdegiovanni.github.io/publications/files/ICST2024.pdf>
- Wang et al., 2024/2026 (7 LLMs, 851 real bugs, ~7.8M mutations).
  <https://arxiv.org/abs/2406.09843>
  None measure mutual masking among LLM-generated mutants — gap.

**Hardware/safety neighbors (verified)**
- BugMAPI, DAC 2016 (Michigan + IBM Haifa).
  <https://doi.org/10.1145/2897937.2898072>
  Single-bug probabilistic masking estimation, 77% accuracy, 1000x.
- Kolan et al., "Post-Silicon Validation of the IBM POWER9 Processor,"
  DATE 2020. <https://doi.org/10.23919/DATE48585.2020.9116491>
  4% of POWER9 bugs post-silicon (vs 1% POWER8); 30.9% in the
  load-store unit (defect clustering).
- Akers, IEEE D&T 1992 (fault collapsing / dominance).
  <https://doi.org/10.1109/54.124518>
- Jasper FSV fault-pair collapsing, DVCon (29.5% fault-list reduction;
  Prime Faults = pairwise dominance, no masking statistics).
  <https://dvcon-proceedings.org/wp-content/uploads/use-of-formal-methods-for-verification-and-optimization-of-fault-lists-in-the-scope-of-iso26262.pdf>
- SEU+SET mutual masking, ISCAS 2014.
  <https://doi.org/10.1109/iscas.2014.6865207>
  (pairwise masking rates for synthetic radiation faults — scope our
  claims to real logic bugs accordingly).
- Bagbaba et al., Electronics 11(3):319, 2022 (application-safe fault
  classification: 20% CPU / 11% UART / 13% CAN; ISO 26262 tooling is
  single-fault only). <https://doi.org/10.3390/electronics11030319>
- Firefly (LLM mutants for verification gaps), MLCAD 2025.
  <https://doi.org/10.1109/mlcad65511.2025.11189125>
- VeriBugBench, arXiv 2609.18022 (submitted TCAD; single-fault by
  design; observability 36.01–39.54%). CONCURRENT WORK — cite
  prominently; our differentiators: pairs, historical day-one envs,
  reachability-audited funnel attribution.
  <https://arxiv.org/abs/2609.18022>

**Claim-corrections from the verification sweep**
- Yin et al. FSE 2011 studied FOUR OSes (3 open-source + 1 proprietary,
  2,000 fixes, 500/OS): "at least 14.8%–24.4% of sampled fixes ...
  are incorrect"; 39% of concurrency-fix incorrect. Our earlier
  "three OSes" note was wrong.
- RealBench 44.2% figure refers to GPT-4-Turbo code passing RTLLMV2's
  testbenches failing formal equivalence (not RealBench's own 100%-line
  benches).
- BugMAPI speedup is stated as "3 orders of magnitude"; "77% dynamic
  accuracy" confirmed.
- MANTRA's archival abstract says "maximum boost of 83.44%" (the DAC
  program page's 35.89% is the stale number).

## Public verification histories (the data sources)

- OpenTitan: RTL + UVM TB + nightly regression dashboards +
  milestone release notes (M1-M6) + issue tracker.
  Repo: <https://github.com/lowRISC/opentitan>
  Dashboard: <https://dashboard.reports.lowrisc.org/opentitan/earlgrey/dashboard.html>
- CVA6 / CORE-V-VERIF: regression-per-PR CI, Spike golden model,
  public issue tracker.
  <https://github.com/openhwgroup/cva6>
- OpenSPARC T1 (2006, historical): full RTL + verification suite of a
  shipping chip, pre-UVM methodology.
