# Bugs found per regression cycle: discrete vs. continuous evidence

Part of the masked-bug-archaeology track. Companion documents: `METHODOLOGY.md`
(methods, threats), `SOURCES.md` (full bibliography), `RESEARCH_PLAN.md`
(phases and gates). Authoritative version of Deliverable 1; expanded and
revised in `../DELIVERABLES.md` §2.

## 1. Two framings of the same question

"How do found-bug counts behave over a project's life?" has two distinct
answers in the literature, and they are often conflated.

**Discrete, per-cycle counts.** Each regression cycle (or silicon pass) is
one observation: *how many bugs did this run of the environment find?* The
data lives in one bin per cycle. Decay means each bin holds fewer bugs than
the last — and, critically, empty late bins mean "the cycles found nothing",
which is evidence about *detection power per cycle*, the quantity regression
planning actually needs.

**Continuous intensity.** Time (or simulation cycles) is the axis; the
quantity is bugs-per-unit-effort, smoothed over intervals. Decay means the
*hazard rate* falls. Empty late *intervals* are compatible with an
environment that never had detection power for the remaining bugs: intensity
can fall to zero because *there is nothing left to find* — or because *the
remaining bugs cannot be caught by current stimulus and checkers*. Intensity
alone cannot distinguish these, and confounds discovery with testbench
attention (see §3).

Discrete per-cycle data is what the regression-decay heuristics speak; it is
also much scarcer in the public record, for a structural reason: per-cycle
counts require someone to tabulate bugs *by the cycle that found them*, and
neither vendor errata sheets nor defect-tracking dashboards record that.

## 2. The DEC VAX debug memorandum (silicon passes)

An internal Digital Equipment Corporation debug memorandum — Bob Supnik,
"VLSI CPU Bugs: A Comparative Analysis (Revised)", interoffice memorandum,
10-Dec-1991 — preserved by the SIMH computer-history project, tabulates bugs
by the silicon pass that fixed them, for four successive VAX microprocessors
(MicroVAX, CVAX, Rigel, NVAX). The document is reachable at
<https://simh.trailing-edge.com/semi/docs/bug_anal.txt> (verified 2026-10-18;
a mirror exists at
<https://mirrors.meulie.net/bitsavers.org/simh.trailing-edge.com_201206/semi/docs/bug_anal.txt>).
"Pass" is the pass in which the bug was fixed; minipasses are partial-metal
fix passes.

**Total passes+minipasses** (CVAX includes CMOS-2 shrink bug-fix pass):

| | uVAX | CVAX | Rigel | NVAX |
|---|---|---|---|---|
| passes+minipasses | 5+11 | 5+11 | 6+1 | 2+0 |

**Bugs found per pass:**

| pass: | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| uVAX | 6 | 11 | 10 | 3 | 3 |
| CVAX | 19 | 7 | 7 | 3 | |
| Rigel | 7 | 4 | 1 | 2 | 2 |
| NVAX | 15 | 3 | | | |

The memo's conclusions [7], quoted verbatim:

> "The high degree of functionality on CVAX pass 1 allowed for a classical
> 'descending exponential' bug rate. Nonetheless, the tail proved very long,
> with several bugs showing up in pass 4. Rigel showed a similar curve, with
> several bugs showing up in pass 4 and 5. Only NVAX finally broke through
> this barrier."

> "The significantly increased verification efforts on Rigel and NVAX were
> repaid by significantly reduced bug rates."

> "The microcode bug rate actually got worse, despite better tools, because
> of the addition of new functionality (eg, vectors, IB error handling, etc)
> and new microarchitectural complexity."

Three observations matter for us. **(i) The tail is real and discrete:**
CVAX still produced 3 fixes on pass 4; Rigel on passes 4–5. **(ii) Decay is
attributable:** the memo attributes NVAX's short tail to increased
verification effort and its patchable control store ("allowed debug on
first pass parts to proceed further and find more problems") — effort moved
the curve, not luck. **(iii) The new-function hump is visible even here:**
microcode bug rate *rose* when vectors and IB error handling were added,
foreshadowing the Laplace-factor rise Malka & Ziv measure continuously
(§3). Supnik's 2017 oral history [8] corroborates the table from memory:
"as the bug rates declined, the kinds of bugs we found became sort of more
and more on the fringes."

## 3. Continuous intensity: Malka & Ziv (DAC 1998)

Malka & Ziv, "Design reliability — estimation through statistical analysis
of bug discovery data," DAC 1998, IBM Research–Haifa
(<https://doi.org/10.1145/277044.277209>): two superscalar PowerPC
processors, >8 months of simulation data, 68 billion cycles (Processor A)
and 2 billion cycles (Processor B), several hundred bugs tracked daily.
Method: Laplace-test trend analysis of reliability growth, then NHPP
reliability-growth models (Musa–Okumoto, Duane, Goel–Okumoto). They
predicted Processor B's bug count and MTTF three months in advance,
validated against 105 billion cycles and 794 total bugs.

The key phenomenon for our framing: on Processor A, Laplace factors **rose
between 200 and 500 million cycles** — reliability *decreased* — because
testing of a major new function started in that window; discovery intensity
followed testbench attention, not elapsed time. An intensity curve, read
naively as "bugs remaining", would have misread this as a tail of hard bugs;
it was a *change in what was being looked at*.

This is the continuous counterpart of the discrete table above: same decay
overall, but intensity conflates (a) depletion of the bug population, (b)
detection power of current stimulus/checkers, and (c) where testbench
attention is pointed. Only a controlled measurement — same environment,
known bug population — can separate (b) from (a). That is exactly the
day-one replay this track performs.

## 4. Other discrete or quasi-discrete data in the literature

- **Rex Black's find/fix model** (software system test)
  <https://rexblack.com/resources/qa-library/bug-find-fix-estimation-template>:
  the canonical *geometric per-cycle decay* 50 / 25 / 12.5 / 6.25 / 3.1 /
  3.0 / acceptance, used for find/fix projection; the page states
  "Programs that do not match this shape usually have a scope problem
  (regression re-opening bugs) or a test-design problem (same tests running
  cycle after cycle)." Explicitly per-cycle, but a *planning model*, not a
  published measurement.
- **ABDOM** (He, Yan & Liu, *Journal of Software* 2011,
  <https://doi.org/10.3724/SP.J.1001.2010.03691>): models defects-found
  *per test cycle* as damped oscillation (periodic peaks decaying toward
  zero), fitted to two industrial projects — the closest software analogue
  to "bugs found per regression cycle".
- **Walsh (OOPSLA 1992)**, defect data from Rational Rose
  (<https://doi.org/10.1145/141937.141952>): discovery *rate* fell from 26
  defects per 1,000 CPU-seconds at functional-test entry to ~5 after 100
  defects; quasi-discrete phase data, again intensity-like.
- **Oriol (ICST 2012)**, <https://doi.org/10.1109/ICST.2012.100>: faults
  found by random testing follow a Michaelis–Menten saturation law in the
  number of tests — discrete-in-tests, continuous-in-effort.

## 5. The gap, and what this project adds

No modern silicon project publishes per-regression-cycle or per-pass bug
counts. Vendor errata sheets are cumulative lists with no cycle attribution
(RemembERR mined 2,563 Intel/AMD errata since 2008 — none carry
"found on pass n" fields [9]); Wilson/Siemens trend reports publish spin
and schedule outcomes, not per-cycle counts; verification-team papers
(POWER9, BugMAPI) report aggregates. The DEC memo appears to be the last
public table of its kind — and it is 35 years old, covers circuit-level
silicon debug, and predates constrained-random/UVM regression entirely.

Our OpenTitan mining produces exactly this data for a modern open-source
silicon project: every mined bug-fix commit carries its date, its block,
and — after day-one replay — the *verdict of the day-one suite*. Grouping
replay verdicts by the commit interval in which each bug was fixed yields a
per-regression-cycle detection profile for a 2019–2024 project, measured
with a fixed historical instrument rather than reconstructed from memory.
This is Deliverable 1's empirical contribution; §2 of `../DELIVERABLES.md`
carries the analysis.

## References

- [5] R. Supnik, "VLSI CPU Bugs: A Comparative Analysis (Revised)," DEC
  interoffice memorandum, 10-Dec-1991. SIMH computer-history preservation:
  <https://simh.trailing-edge.com/semi/docs/bug_anal.txt> (mirror:
  <https://mirrors.meulie.net/bitsavers.org/simh.trailing-edge.com_201206/semi/docs/bug_anal.txt>)
- [6] Y. Malka and A. Ziv, "Design reliability — estimation through
  statistical analysis of bug discovery data," Proc. DAC 1998.
  <https://doi.org/10.1145/277044.277209>
- [7] Rex Black, "The model that says when you will run out of bugs,"
  bug find/fix estimation template, QA Library.
  <https://rexblack.com/resources/qa-library/bug-find-fix-estimation-template>
- [8] R. Supnik, interview by G. Hendrie, *Oral History of Robert Supnik,
  part 2*, Computer History Museum, recorded 9 May 2017, CHM reference
  X8215.2017. <https://archive.computerhistory.org/resources/access/text/2019/07/102740181-05-01-acc.pdf>
- [9] F. Solt, P. Jattke and K. Razavi, "RemembERR: Leveraging
  Microprocessor Errata for Design Testing and Validation," Proc. MICRO
  2022. <https://comsec-files.ethz.ch/papers/rememberr_micro22.pdf>
- [10] Z. He, H. Yan and C. Liu, "Accumulative Bi-Damped Oscillation Model
  for the Sequential Process of Software Defect Discovery," *Journal of
  Software* (China), 2011. <https://doi.org/10.3724/SP.J.1001.2010.03691>
- [11] J. Walsh, "Preliminary defect data from the iterative development of
  a large C++ program," OOPSLA 1992 (experience report).
  <https://doi.org/10.1145/141937.141952>
- [12] M. Oriol, "Random Testing: Evaluation of a Law Describing the Number
  of Faults Found," Proc. ICST 2012. <https://doi.org/10.1109/ICST.2012.100>
