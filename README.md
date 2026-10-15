# Chip Verification Research

Owner: [@HasanAkel](https://github.com/HasanAkel)

Two research tracks on bug masking in hardware verification:

| Track | Folder | One-liner |
| --- | --- | --- |
| Masked bug injection (parked) | [`masked-bug-injection/`](masked-bug-injection/) | Synthesize labeled visible/masked bugs with VeriBugBench mutants (AXI lab, pipe lab) |
| Masked bug archaeology (active) | [`masked-bug-archaeology/`](masked-bug-archaeology/) | Measure what fraction of a real chip's eventual bugs its day-one testbench could have caught, per funnel stage |

Read `masked-bug-archaeology/docs/RESEARCH_PLAN.md` for the active plan and
`masked-bug-archaeology/docs/SOURCES.md` for the literature grounding.

## Shared infrastructure

| Path | Purpose |
| --- | --- |
| `scripts/env.ps1` | Shell activation (iverilog, vvp, gtkwave, python, veribugbench) |
| `scripts/setup_laptop.ps1` | One-time bootstrap: venv, VeriBugBench at `C:\cv`, patches, junction |
| `patches/` (moved) | Windows fixes now live under `masked-bug-injection/patches/` |
| `third_party/` | Junction to the short-path VeriBugBench checkout (not committed) |
| `tools/` | Local GTKWave (not committed) |

## Quick start (Windows laptop)

1. Install [Git](https://git-scm.com/), [Python 3.12+](https://www.python.org/),
   and [Icarus Verilog](https://bleyer.org/icarus/) (`winget install Icarus.Verilog`).
2. Clone this repo, then:

```powershell
.\scripts\setup_laptop.ps1
. .\scripts\env.ps1
python masked-bug-injection\lab\check_env.py     # injection track still runnable
python masked-bug-archaeology\env\check_env.py   # archaeology track readiness
```

## Track status

- **masked-bug-injection:** parked but maintained; lab scenarios verified
  working after the reorganization (labels.csv regenerated, all classes match).
- **masked-bug-archaeology:** Phase 0 (scoping) — see the research plan.

## Collaborators

Repo owner: **HasanAkel**. Teammates with write access: **Omar-ocorp**,
**Mohamed-Aaqib**, **salimakell**. Add more under Settings → Collaborators.

## License / upstream

Original lab and scripts in this repo are for the team project.
VeriBugBench and imported RTL retain their upstream licenses
(see that project's `LICENSE` / `THIRD_PARTY_NOTICES.md`).
