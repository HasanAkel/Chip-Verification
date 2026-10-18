# Masked Bug Archaeology

**Research question:** of all the bugs a real chip eventually had, what fraction
could the *day-one* verification environment (first functional testbench +
first regression suite) have detected — and for the rest, *where* in the
detection funnel did they hide?

```
P(found) = P(activate) x P(propagate to checker) x P(checker fails)
```

This is an empirical measurement project, not a tool project. We take the
public verification history of an open-source silicon project (OpenTitan,
CVA6), reconstruct the environment as it existed at time zero, and *replay*
every bug found later against it. Each replayed bug is classified:

| Class | Meaning | Remedy it points to |
| --- | --- | --- |
| (a) not activated | day-one stimulus never hit the trigger | more / different stimulus |
| (b) activated, not propagated | wrong value never reached an output | observability / propagation |
| (c) propagated, not checked | wrong output seen but no checker complained | missing / weak checkers |
| (d) detected | day-one suite fails on the buggy RTL | (none — it was never masked) |

Classes (a)-(c) are the **masked population**, with the masking *cause*
attributed. No published work measures this on real bugs; synthetic-mutation
tools (Certitude, VeriBugBench) measure it on artificial faults only.

## Why this matters

- Puts a number on hidden risk at sign-off: "the day-one environment was
  blind to X% of this block's eventual bugs."
- Validates or falsifies the 50/25/12.5 regression decay heuristic using
  real detection power instead of raw failure counts.
- Gives any future masked-bug *detector* a measured baseline to beat.
- Complements the sibling track `../masked-bug-injection/`: synthetic
  mutants vs. real bugs on the same blocks — the gap between the two scores
  is itself a publishable result.

## Directory layout

```
docs/RESEARCH_PLAN.md   phased plan with commands and go/no-go gates
docs/SOURCES.md         literature and prior art, with links
env/check_env.py        environment sanity check for this track
data/                   mined bug database and replay results (committed)
survey/                 exploratory counts pulled from commit history
work/                   simulation products (not committed)
```

## Status

Phase 0 (scoping). See `docs/RESEARCH_PLAN.md` for the active phase.

The project's research statement — the full literature-grounded case for
masked-bug archaeology, the per-regression-cycle evidence base, the
regression workflow, and our falsifiable predictions — is in
[`DELIVERABLES.md`](DELIVERABLES.md) (2026-10-18); the per-cycle study
stands alone in [`docs/BUGS_PER_REGRESSION.md`](docs/BUGS_PER_REGRESSION.md).
