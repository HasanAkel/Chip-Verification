# Regression cost, related work, and where this lab stands

This note records the literature we are aligning with, the AXI masking
numbers measured on this machine, and the limits of that measurement.
The runner is `lab/axi_mask_search.py` (`python lab/axi_mask_search.py strict`).
Raw tables live under `work/axi_mask/strict_results/` and are not committed
(simulation products; see `.gitignore`).

## Regression cost is treated as a real problem

These are industry studies and peer-reviewed papers, not blog posts.

- Harry D. Foster, "Trends in Functional Verification: A 2016 Industry Study,"
  DVCon 2016. Wilson Research Group / Mentor study. From 2007 to 2016 the
  headcount of verification engineers grew about 10.4% per year, against
  about 3.6% for design engineers. Verification is the cost line that grows
  faster than the design itself.
  <https://dvcon-proceedings.org/wp-content/uploads/trends-in-functional-verification-a-2016-industry-study.pdf>

- Ganapathy Parthasarathy et al. (Synopsys), "RTL Regression Test Selection
  Using Machine Learning," ASP-DAC 2022.
  <https://doi.org/10.1109/ASP-DAC52403.2022.9712550>
  They state that iterative RTL regression can consume as much as 70% of
  hardware design cost, counting people, machines, simulator licenses, and
  time. That is the clearest published sentence that regression itself, not
  only "verification" in the abstract, is the expensive loop.

- Nan Wu, Yingjie Li, and Hang Yang, "Survey of Machine Learning for
  Software-assisted Hardware Design Verification," ACM TODAES, 2024.
  <https://doi.org/10.1145/3661308>
  Verification is about half of development cost and dominates schedule.
  They cite the same industry picture: a large share of ASIC and FPGA
  projects finish late.

- Aruna Jayasena and Prabhat Mishra (University of Florida), "Directed Test
  Generation for Hardware Validation: A Survey," ACM Computing Surveys, 2024.
  <https://doi.org/10.1145/3638046>
  Constrained-random simulation covers a lot and still leaves an
  unacceptable bill for the remaining corner cases. The verification-to-design
  engineer ratio has been rising.

## Work that tries to run fewer regressions

These papers shrink the suite. They do not ask which bugs hide each other.

| Work | How they cut the suite |
| --- | --- |
| Parthasarathy et al., ASP-DAC 2022 | Learn from RTL edits and past tests which tests are likely to fail on this change. Reported about 35% to 10x fewer tests, with median failure recall above 90%. |
| Rongjian Liang, Nathaniel Pinckney, Yuji Chai (Harvard), Mark Ren, Brucek Khailany (NVIDIA), "Test Selection For RTL Coverage By Unsupervised Learning From Fast Functional Simulation," DAC 2023 late-breaking. <https://research.nvidia.com/publication/2023-07_late-breaking-results-test-selection-rtl-coverage-unsupervised-learning-fast> | Pick constrained-random tests from fast functional coverage, then spend RTL simulation only on that subset. Up to about 85% less RTL simulation time on two units of a production GPU, at the same functional coverage. |
| S. Ikram and J. Ellis, "Dynamic Regression Suite Generation Using Coverage-Based Clustering," DVCon 2017 | Cluster tests by coverage. A smaller dynamic suite matched the original suite's fault-simulation quality (Certitude) with fewer tests, less runtime, and fewer licenses. |
| Marek Cieplucha (Warsaw University of Technology), "Metric-Driven Verification Methodology with Regression Management," Journal of Electronic Testing, 2019. <https://doi.org/10.1007/s10836-019-05777-0> | Split tests into segments that restart from checkpoints. Do not replay the prefix once coverage says it no longer helps. The saving grows at high coverage targets. |
| Shai Fine and Avi Ziv, "Probabilistic regression suites for functional verification," DAC 2004 | Build a short regression whose probability of exposing a bug is explicit, instead of replaying the whole random suite. |

Software has a longer line of the same idea (Yoo and Harman, STVR 2012;
Rothermel et al., TSE 2001). The hardware papers above are the ones that
apply it to RTL.

## Who already talks about masked bugs

The grounding, strongest first:

**1. Safety standards require exactly this kind of analysis.** ISO 26262-5:2018
(road vehicles, functional safety, hardware) clause 7.4.3.2 requires that, for
ASIL B–D, safety analyses identify single-point, residual, and
**multiple-point** faults — a fault that only violates the safety goal *in
combination with another independent fault*. The note says dual-point analysis
normally suffices, and explicitly names the case of "the combination of two
faults where one fault affects a safety-related element and another fault
affects the corresponding safety mechanism" — that is our masked-by-upstream-bug
case, written into law. Latent-fault metrics (LFM) and PMHF calculations depend
on classifying these pairs correctly. ISO 26262-11:2018 extends this to
semiconductors and recommends fault-injection simulation with fault models.
ISO 26262-10:2018 clause 8.1 defines the dual-point fault taxonomy formally.
Nobody's tooling does the RTL-mutant version of this exhaustively — that gap is
what this lab measures.

**2. Commercial EDA tools exist for the single-fault version.** Synopsys
Testbench Quality Assurance (formerly Certitude) is an industry product that
injects systematic faults into RTL, runs the existing testbench, and reports
activation/propagation/detection per fault. Its datasheet says it provides
"evidence-based verification quality analysis for ISO 26262 Part 8-9
assessments." It is one-fault-at-a-time. Cadence JasperGold FSV App does the
same via formal propagation instead of simulation. Fault simulation (Synopsys
Z01X) is a real industrial workload. This proves the single-fault question has
a paying market and a regulatory reason to exist.

**3. The double-fault software analogue is small but real.** "An insight of
double-faults interactions in program: An empirical study" (fault injection on
Siemens suites) found: two faults interfere less than 1% of the time, masking
is more common than constructive interaction, and interference concentrates on
pairs touching the same variable. That study is exactly our experimental design,
transplanted to C. Nobody appears to have published the hardware analogue.

**4. Reliability work says independence is unsafe to assume.** "Scalable
Reliability Assessment of DNNs through Simultaneous Fault Injection" (2024)
found that in densely connected DNNs, simultaneously-injected faults interact
enough to create artificial masking — false negatives — and proposes mitigation.
The explicit warning is: do not treat simultaneous faults as independent. Our
AXI results are a hardware instance of that warning (3,472 of 7,675 pairs
produced signatures neither member produced alone).

**5. Post-silicon masking analysis exists.** BugMAPI (Lee, Kolan,
Morgenshtein, Sokhin, Morad, Ziv, Bertacco — University of Michigan and IBM,
DAC 2016) estimates the probability that a bug in a post-silicon test program
is never observed by the end-of-test checkers. Static analysis of instruction
streams, ~77% of the accuracy of dynamic fault injection at ~1000x less time.
Closest published relative to this lab; still one-fault, instruction-level.

**6. Functional qualification practice.** The DVCon talk "Who's Watching the
Watchmen" and tools like Certitude formalized the warning that a testbench bug
can mask an RTL bug. The experiment remains single-fault.

Closest published relatives, and how they differ from this lab:

- Doowon Lee, Tom Kolan, Arkadiy Morgenshtein, Vitali Sokhin, Ronny Morad,
  Avi Ziv, and Valeria Bertacco (University of Michigan and IBM),
  "Probabilistic bug-masking analysis for post-silicon tests in
  microprocessor verification," DAC 2016.
  <https://doi.org/10.1145/2897937.2898040>
  BugMAPI estimates the probability that a bug in a post-silicon test
  program is invisible to the end-of-test checkers. It is a static
  information-flow analysis of instructions (Power and Alpha), not a
  simulation of two RTL edits at once. They report about 77% of the
  accuracy of injecting bugs and simulating, at roughly 1000x less time.

- "An insight of double-faults interactions in program: An empirical study."
  Fault-injection study on Siemens C suites. Two faults interfere in under
  1% of pairs; masking dominates construction; interference clusters on
  pairs sharing a variable. This is the software version of our pairwise
  design; the hardware version is not in the literature we found.

- "Scalable Reliability Assessment of DNNs through Simultaneous Fault
  Injection" (2024). Injecting many faults at once to speed up reliability
  campaigns is only valid if faults do not interact. In dense DNNs they do,
  producing false "masked" verdicts, so the paper adds an interaction-aware
  correction. Directly relevant: our AXI pair sweep is the RTL analogue,
  and it found plenty of interaction.

- Functional qualification (the DVCon talk "Who's Watching the Watchmen,"
  and commercial tools such as Certitude) inserts one artificial fault and
  scores activation, propagation, and detection. The explicit warning in
  that talk is that a testbench bug can mask an RTL bug. The experiment is
  still one fault at a time.

- VeriBugBench (arXiv:2609.18022, submitted to IEEE TCAD; extends the DAC
  2023 paper "MANTRA: Mutation Testing of Hardware Design Code Based on
  Real Bugs," <https://doi.org/10.1109/DAC56929.2023.10247962>) builds the
  19-operator mutant library this repo uses. It keeps a mutant only when
  that single fault changes a design output. Equivalent mutants are
  dropped. It does not stack two retained faults and ask whether one
  output erases the other.

We did not find a paper that injects pairs of RTL mutants, simulates them
on the same test, and counts a bug as masked when the joint output equals
exactly one of the two single-bug outputs. BugMAPI is the nearest idea.
It targets instruction streams after silicon, and it predicts masking
instead of measuring it by running both bugs.

## Who to contact for grounding or collaboration

The goal is one of two replies: "yes, this matters, here is the industrial
form of it," or "this exists in group X's work, here is the paper."

**BugMAPI authors (closest prior work).**
- Valeria Bertacco, University of Michigan — <bertacco@umich.edu>. Leads the
  Michigan EECS verification group; co-authored BugMAPI and a long line of
  fault-injection/validation work.
- Doowon Lee, now at Samsung AI; first author of BugMAPI.
Ask: whether pairwise RTL-mutant masking has been studied in their group,
and whether an Icarus-based open pipeline is of interest as a teaching or
benchmark artifact.

**MANTRA / VeriBugBench authors (our mutant source).**
- Jiang Wu / Xiaoguang Mao, National University of Defense Technology.
  Contact via the repository issues at <https://github.com/wndif/VeriBugBench>.
Ask: (a) confirm the arXiv paper's TCAD status, (b) point to any multi-fault
retention experiments they deliberately excluded, (c) interest in pairwise
masking as a v2 benchmark axis. As the maintainers of the benchmark we use,
they are the single most relevant group.

**ISO 26262 practitioners (the regulatory demand side).**
- Synopsys Testbench Quality Assurance / Cadence Safety Solutions teams —
  via their verification consulting pages. Practitioners answer concrete
  questions like "does dual-point fault analysis ever get done by RTL
  simulation campaigns rather than FMEA-style spreadsheets?" Ask that exact
  question.

**Test-selection groups (the regression-cost side).**
- Rongjian Liang or Brucek Khailany (NVIDIA research), via the DAC 2023
  publication page. Ask whether coverage-based test selection has ever been
  validated against *masked-bug* ground truth rather than coverage alone.

**Closer to home.** A professor of digital-design verification at a local
university (Lebanese University, AUB, LAU) can read one page and say
whether the framing is sound, which is the cheapest way to get an honest
first signal.

Email template:

> Subject: Is pairwise RTL bug masking a studied problem?
>
> Hi Professor <name>,
>
> I am an independent researcher working on a simulation experiment that
> injects pairs of RTL mutations (from VeriBugBench/MANTRA) into an AXI
> interconnect and checks, for each pair, whether the joint simulation
> output matches exactly one of the two single-fault outputs. When it does,
> one bug is masked by the other. In a recent run, 3,472 of 7,675 pairs
> produced an output neither bug produced alone.
>
> I am trying to find prior work on pairwise/multi-fault masking for RTL
> and on whether this can ground test-selection decisions. ISO 26262-5
> requires dual-point fault analysis, but I have not found an RTL
> simulation campaign implementing it at mutant granularity.
>
> Is this a studied problem I have missed? If not, do you think a
> measurement of pairwise masking rates at RTL level would be a
> publishable/usable contribution?
>
> Repo: <https://github.com/HasanAkel/Chip-Verification>

## What this repo has actually measured

Design: OpenCores `verilog_axi-interconnect` (4 masters, 4 slaves, SRAM
controllers). Simulator: Icarus Verilog on an i5-13500H.

The strict run (`lab/axi_mask_search.py strict`) does three things the
first SRAM-only run did not:

1. Mutates three address-path files PyVerilog used to reject (`addr_wdata_mux_m4`, `addr_wdata_mux_2to1`, `addr_wdata_demux_1to2`) by giving empty `else` / `default` arms an empty `begin/end` so the parser can see them.
2. Bounds every handshake wait in the master BFM and in the test tasks, so one stuck response does not throw away the rest of the test.
3. Scores a handshake trace (AW, W, B, AR, R on all four masters) together with the four SRAM dumps.

| Quantity | Value |
| --- | --- |
| Mutants from the original VeriBugBench drop | 359 |
| Newly generated on the three address-path files | 2,260 |
| Total simulated | 2,619 |
| Compile failures | 946 |
| Timeouts | 11 |
| Ran and matched the clean design | 288 |
| Changed the output | 1,374 |
| Distinct wrong outputs | 88 |

The largest class holds 1,042 bugs, almost all in the address muxes: many
different edits, one trace. The next holds 135 `sram_controller` bugs.

Full pair enumeration of those 1,374 bugs is 391,281 cross-signature
simulations. The committed run used a panel of 125 bugs (up to two per
output class, taken from different files) and simulated 7,675 stackable
pairs.

| Pair result | Count |
| --- | --- |
| Joint output matched neither single bug | 3,472 |
| Joint output matched exactly one of the two | 4,179 |
| Both singles already shared that output | 17 |
| Error | 7 |

3,472 of those pairs are the case the first experiment never saw: the two
bugs together produce an output that neither produced alone. 2,793 of the
new signatures are cross-file (for example a demux edge flip with a mux
operator edit).

## Limitations of the current experiment

- One interconnect and one directed test. This is not a chipset regression
  and not a nightly suite of thousands of tests. The literature above is
  about that industrial suite. We have not yet shown that a masked-bug
  label predicts which of those tests can be dropped.

- The scoreboard is a sampled handshake log plus the SRAM image. It does
  not check every AXI rule (ID ordering across the whole fabric, exclusive
  accesses, narrow transfers, `WSTRB` byte lanes, backpressure held for a
  long time). Two bugs can interact on a rule we do not log and still hash
  the same.

- "Masked" means the joint hash equals one single-bug hash. That is an
  observation about this test, not a proof that the hidden bug is covered
  on every future test.

- "New signature" means the hash differs. We have not yet decoded those
  traces into a protocol story (which beat, which master, which slave).

- 946 mutants never became a design. Operators such as pointer and
  part-select insert often emit Verilog Icarus will not compile. They are
  absent from the 1,374, so the observable set is biased toward edits that
  happen to be legal.

- The master BFM is not mutated. `while` loops inside `always` blocks are
  outside the parser, and the BFM is stimulus rather than the bus.

- Pairs are a panel, not the full cross product, and triples were not run.
  The panel can show that interactions exist. It cannot give the rate of
  interactions over all 1,374 bugs.

- A class of 1,042 bugs sharing one trace means the test still cannot tell
  those edits apart. Finer checks would split that class, and might create
  more masking and more new signatures.

- Generation rewrites a whole file through PyVerilog. For the three newly
  parsed files the empty statements were normalized first. A mutant is
  trusted only because its output differs from the clean run, which does
  not prove the codegen preserved every unrelated line.

- Some operators (`ExprUpdate` and others) pick the replacement at random.
  The run seeds that choice from the syntax-node id, so it is repeatable,
  but it is one sample of the operator, not every legal replacement.

- Simulator is Icarus, not VCS. The module name `interconnect` is renamed
  to `axi_fabric` because it is a SystemVerilog keyword. Results are for
  that compile path.
