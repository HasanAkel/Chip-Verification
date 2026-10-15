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
