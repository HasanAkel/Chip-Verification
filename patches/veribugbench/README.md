# Windows patches for VeriBugBench

These files are **not** upstream VeriBugBench. Apply them after
`pip install -e` of a VeriBugBench checkout (see `scripts/setup_laptop.ps1`).

## `pyverilog_patch/parser.py`

Upstream builds the preprocessor output name with:

```python
filelist[0].split("/")[-1].replace(".v", "")
```

On Windows the path uses `\`, so the drive letter stays in the name and
Icarus `ivlpp` fails. We use `pathlib.Path(filelist[0]).stem` instead.

Also keep the other files from VeriBugBench's vendor patch directory
(`ast.py`, `codegen.py`, …); `setup_laptop.ps1` runs their official
`apply_pyverilog_patch.py` first, then overwrites `parser.py` with this copy.

## `benchmark.py`

Icarus runs that hit `$fatal` / `$error` after writing the observation CSV
exit non-zero. Treating that as a hard failure hid **observable** mutants.
If the CSV exists and is non-empty, we keep comparing; a missing CSV is
still a hard error.
