# Laptop setup (detailed)

## Tools to install once

```powershell
winget install --id Git.Git -e
winget install --id Python.Python.3.12 -e
winget install --id Icarus.Verilog -e
winget install --id GitHub.cli -e   # optional, for PRs / invites
```

Optional waveform viewer: extract GTKWave win64 under `tools\gtkwave\` so
`tools\gtkwave\gtkwave64\bin\gtkwave.exe` exists, or set `$env:GTKWAVE`.

## Why VeriBugBench lives at `C:\cv\VeriBugBench`

Some mutant filenames are longer than 260 characters when nested under
`Documents\Chip Verification\...`. Checkout under `C:\cv\` keeps paths short.
`third_party\VeriBugBench` is a junction for convenience; open very long
paths from `C:\cv\VeriBugBench` if Explorer fails.

Enable Windows long paths (admin, once) if you want deeper trees:

```powershell
reg add HKLM\SYSTEM\CurrentControlSet\Control\FileSystem /v LongPathsEnabled /t REG_DWORD /d 1 /f
```

## Sanity checks

```powershell
. .\scripts\env.ps1
python lab\check_env.py
python lab\run_lab.py
veribugbench validate
```

Synopsys VCS is **not** required for the lab or for Icarus-compatible
VeriBugBench projects. It is only needed to reproduce the paper's VCS/URG
coverage experiments.
