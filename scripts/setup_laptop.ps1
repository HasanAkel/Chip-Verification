# Bootstrap this project on a new Windows machine so teammates can continue
# without re-discovering tool paths or Windows VeriBugBench quirks.
#
# Usage (from the repo root):
#   .\scripts\setup_laptop.ps1
#
# What it does:
#   1. Creates .venv and installs requirements.txt
#   2. Clones VeriBugBench to C:\cv\VeriBugBench (short path = fewer MAX_PATH failures)
#   3. pip install -e VeriBugBench with mutation/analysis extras
#   4. Applies patches/veribugbench Windows fixes
#   5. Junctions third_party\VeriBugBench -> C:\cv\VeriBugBench

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$pyCandidates = @(
    (Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source),
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
) | Where-Object { $_ -and (Test-Path $_) }
if (-not $pyCandidates) {
    throw "Python 3.10+ not found. Install Python.Python.3.12 via winget, then re-run."
}
$py = $pyCandidates[0]
Write-Host "Using Python: $py"

$venvPy = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    & $py -m venv (Join-Path $root ".venv")
}
& $venvPy -m pip install --upgrade pip
& $venvPy -m pip install -r (Join-Path $root "requirements.txt")

# Icarus on PATH for PyVerilog / VeriBugBench
$iverilogBin = "C:\iverilog\bin"
if (Test-Path (Join-Path $iverilogBin "iverilog.exe")) {
    $env:Path = "$iverilogBin;" + $env:Path
} else {
    Write-Warning "Icarus Verilog not found at C:\iverilog\bin. Install with: winget install Icarus.Verilog"
}

$vbb = "C:\cv\VeriBugBench"
if (-not (Test-Path (Join-Path $vbb "src\veribugbench"))) {
    New-Item -ItemType Directory -Force -Path "C:\cv" | Out-Null
    $git = Get-Command git -ErrorAction SilentlyContinue
    if (-not $git) { throw "git not on PATH" }
    Write-Host "Cloning VeriBugBench to $vbb (this is large)..."
    & git -c core.longpaths=true clone --depth 1 https://github.com/wndif/VeriBugBench.git $vbb
}

& $venvPy -m pip install -e "${vbb}[mutation,analysis,test]"

# Apply upstream VeriBugBench pyverilog patch, then overwrite with our Windows-safe parser.
$apply = Join-Path $vbb "scripts\apply_pyverilog_patch.py"
if (Test-Path $apply) {
    & $venvPy $apply --yes
}
$patchParser = Join-Path $root "patches\veribugbench\pyverilog_patch\parser.py"
$siteParser = Join-Path $root ".venv\Lib\site-packages\pyverilog\vparser\parser.py"
if ((Test-Path $patchParser) -and (Test-Path $siteParser)) {
    Copy-Item $patchParser $siteParser -Force
    Write-Host "Applied Windows Path.stem fix to pyverilog parser"
}
$benchSrc = Join-Path $root "patches\veribugbench\benchmark.py"
$benchDst = Join-Path $vbb "src\veribugbench\benchmark.py"
if ((Test-Path $benchSrc) -and (Test-Path $benchDst)) {
    Copy-Item $benchSrc $benchDst -Force
    Write-Host "Applied Icarus `$fatal tolerance to veribugbench.benchmark"
}

$link = Join-Path $root "third_party\VeriBugBench"
New-Item -ItemType Directory -Force -Path (Join-Path $root "third_party") | Out-Null
if (Test-Path $link) {
    $item = Get-Item $link -Force
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        Write-Host "third_party\VeriBugBench junction already present"
    } else {
        Write-Warning "third_party\VeriBugBench exists and is not a junction; leave it as-is"
    }
} else {
    New-Item -ItemType Junction -Path $link -Target $vbb | Out-Null
    Write-Host "Created junction third_party\VeriBugBench -> $vbb"
}

Write-Host ""
Write-Host "Setup done. In every new terminal:"
Write-Host "  . .\scripts\env.ps1"
Write-Host "  python lab\check_env.py"
Write-Host "  python lab\run_lab.py"
