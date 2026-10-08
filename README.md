# Masked Bug Injection / Chip Verification Lab

Owner: [@HasanAkel26](https://github.com/HasanAkel26)

Research sandbox for **masked bug injection** into RTL, using
[VeriBugBench](https://github.com/wndif/VeriBugBench) as the mutation /
benchmark framework. Goal: build a labeled mixture of visible bugs and
masked bugs so a model can learn which components a testbench fails to
exercise, then target those components with tighter tests (and later TPI).

## What is in this repo

| Path | Purpose |
| --- | --- |
| `lab/` | Tiny RTL + testbench that demonstrates visible bugs, downstream masking, starvation, and upstream-bug masking |
| `scripts/` | Environment activation and laptop bootstrap |
| `patches/veribugbench/` | Windows-required fixes for PyVerilog path handling and Icarus `$fatal` exit codes |
| `requirements.txt` | Python deps for the lab + VeriBugBench extras |
| `docs/` | Setup notes and collaborator checklist |

Generated simulation outputs (`lab/results/`, `work/`), virtualenvs, and the
full VeriBugBench dataset tree are **not** committed. Clone VeriBugBench
separately (see setup).

## Quick start (Windows laptop)

1. Install [Git](https://git-scm.com/), [Python 3.12+](https://www.python.org/),
   and [Icarus Verilog](https://bleyer.org/icarus/) (`winget install Icarus.Verilog`).
2. Optional: GTKWave for waveforms
   ([win64 zip](https://sourceforge.net/projects/gtkwave/files/gtkwave-3.3.100-bin-win64/)).
3. Clone this repo, then:

```powershell
cd "Chip-Verification"   # or whatever folder you cloned into
.\scripts\setup_laptop.ps1
. .\scripts\env.ps1
python lab\check_env.py
python lab\run_lab.py
```

`setup_laptop.ps1` creates `.venv`, installs `requirements.txt`, clones
VeriBugBench to `C:\cv\VeriBugBench` (short path avoids Windows MAX_PATH),
installs it editable, and applies the Windows patches under `patches/`.

Open a waveform after the lab run:

```powershell
gtkwave lab\results\downstream_mask\wave.vcd
```

## VeriBugBench commands (after env.ps1)

```powershell
veribugbench validate
veribugbench list-projects
veribugbench show first_counter_overflow
```

`veribugbench` is a PowerShell function that always passes
`--root $env:VERIBUGBENCH_ROOT` (default `C:\cv\VeriBugBench`).

## Masking labels the lab teaches

| Scenario | Meaning |
| --- | --- |
| `visible` | Bug changes the checked pin |
| `downstream_mask` | Bug runs locally; mux/cover-up hides it from the pin |
| `starvation` | Upstream enable never reaches the bug site |
| `masked_by_upstream_bug` | A second bug hides the first one's effect |

## AXI masking experiment

`lab/axi_mask_search.py strict` stacks VeriBugBench mutants on the OpenCores
AXI interconnect, scores handshake traces plus SRAM dumps, and labels pairs
whose joint output matches only one of the two bugs. Literature, measured
counts, and the limits of that run are in
[`docs/LITERATURE_AND_STATUS.md`](docs/LITERATURE_AND_STATUS.md).

## Collaborators

Repo owner: **HasanAkel26**. Teammates with write access: **Mohamed-Aaqib**,
**salimakell**. Add more under Settings → Collaborators.

## License / upstream

Original lab and scripts in this repo are for the team project.
VeriBugBench and imported RTL retain their upstream licenses
(see that project's `LICENSE` / `THIRD_PARTY_NOTICES.md`).
