# Dot-source this so the PATH and the veribugbench function stay in your window:
#   . .\scripts\env.ps1
#
# Do not run as ".\scripts\env.ps1" alone if you want PATH changes to persist
# in the current session; the leading dot (dot-source) is required.

$root = Split-Path -Parent $PSScriptRoot
$machine = [Environment]::GetEnvironmentVariable("Path", "Machine")
$user = [Environment]::GetEnvironmentVariable("Path", "User")

# Prefer project-local tools, then machine/user PATH.
$gtkwaveBin = Join-Path $root "tools\gtkwave\gtkwave64\bin"
$env:Path = @(
    "C:\iverilog\bin",
    (Join-Path $root ".venv\Scripts"),
    $gtkwaveBin,
    $machine,
    $user
) -join ";"

# Short-path VeriBugBench checkout (see docs/LAPTOP_SETUP.md).
if (-not $env:VERIBUGBENCH_ROOT) {
    $env:VERIBUGBENCH_ROOT = "C:\cv\VeriBugBench"
}

# Override the bare veribugbench.exe so --root is never forgotten.
function global:veribugbench {
    $exe = Join-Path $root ".venv\Scripts\veribugbench.exe"
    if (-not (Test-Path $exe)) {
        throw "veribugbench.exe missing. Run .\scripts\setup_laptop.ps1 first."
    }
    & $exe --root $env:VERIBUGBENCH_ROOT @args
}

Set-Location $root
Write-Host "iverilog: $((Get-Command iverilog -ErrorAction SilentlyContinue).Source)"
Write-Host "python:   $((Get-Command python -ErrorAction SilentlyContinue).Source)"
Write-Host "VeriBugBench: $env:VERIBUGBENCH_ROOT"
Write-Host "This window can run iverilog, vvp, gtkwave, python, and veribugbench."
Write-Host "veribugbench is a function here, so it always uses --root $env:VERIBUGBENCH_ROOT."
