# Copilot Instructions for netherland

These instructions are the default operating guide for cloud agents in this repository.
Always trust this file first, and only search the codebase when information here is missing or demonstrably incorrect.

## 1) Repository purpose and shape

- Repository type: Python library (scientific/modeling domain), not a web app/service.
- Purpose: Simulate below-ground biomass and sediment dynamics for salt marsh morphodynamics, based on Morris & Bowden (1986).
- Core model unit: a single `Cell` made of layered sediment/biomass stocks; multi-cell orchestration in `Marsh`.
- Language/runtime: Python 3.12.
- Dependency/env manager: `uv` (authoritative workflow).
- Packaging backend: setuptools via `pyproject.toml`.
- Approximate size: small codebase (single `src/` package with focused modules + unittest suite).

## 2) Canonical commands (validated)

Run commands from repo root.

### Tool versions observed during validation

- `uv 0.9.26`
- Python interpreter used by uv: CPython 3.12.x

### One-time/bootstrap

1. `uv lock`
- Status: works.
- Result: creates/updates `uv.lock` with reproducible dependency resolution.

2. `uv sync --group dev`
- Status: works.
- Result: creates `.venv` and installs project + dev tooling (`pytest`, `build`, `twine`).
- Observed runtime: roughly 20s on first sync in this environment.

### Test

1. `uv run python -B -m pytest -q`
- Status: works.
- Result: `87 passed`.
- Observed runtime: about 0.55s.

2. `uv run python -m unittest discover -s tests -p "*test*.py"`
- Status: works.
- Result: `Ran 87 tests ... OK`.
- Observed runtime: about 0.04s.

### Build/package

1. Optional clean before build:
- PowerShell:
  - `if (Test-Path dist) { Remove-Item -Recurse -Force dist }`
  - `if (Test-Path build) { Remove-Item -Recurse -Force build }`
  - `if (Test-Path src/netherland.egg-info) { Remove-Item -Recurse -Force src/netherland.egg-info }`

2. `uv run python -m build`
- Status: works.
- Result: produces `dist/netherland-0.0.0.tar.gz` and wheel.

## 3) Known failure modes and mitigations (important)

These failures were observed before uv migration and are still useful diagnostics:

- `python -m pytest` can fail with `No module named pytest` if not using uv-managed env.
- `python -m build` can fail with `No module named build` if build frontend is not installed.
- Bare `pytest` in some machines may resolve to another repository's virtualenv on PATH (false confidence risk).

Mitigation to always use:

- Always run test/build commands through `uv run ...` after `uv sync --group dev`.
- Do not rely on globally installed `pytest`.

## 4) Required order for reliable local validation

Always execute in this order for PR-quality changes:

1. `uv lock` (if dependencies changed)
2. `uv sync --group dev`
3. `uv run python -B -m pytest -q`
4. `uv run python -m build`

If step 3 fails, do not proceed to step 4.
If step 4 fails, include full error text in PR notes.

## 5) CI and pre-checkin parity

Primary workflow file:

- `.github/workflows/publish.yml`

Current build job behavior:

1. Setup Python 3.12
2. Setup uv
3. `uv sync --group dev`
4. `uv run python -B -m pytest`
5. `uv run python -m build`
6. Upload `dist/` artifacts

Release/publish jobs trigger on tags and publish to TestPyPI/PyPI, then create a GitHub release.

## 6) Project layout and where to edit

### Root files (high value)

- `pyproject.toml`: authoritative metadata/dependencies/tool config.
- `uv.lock`: locked dependency graph for reproducibility.
- `README.md`: model description, assumptions, and usage narrative.
- `setup.py`: setuptools shim (`setup()`), metadata lives in `pyproject.toml`.
- `requirements.txt`: legacy snapshot; do not use as primary workflow source.
- `.github/workflows/publish.yml`: CI/CD + package publish pipeline.
- `data/morris_constants.toml`: default model constants.

### Source map (`src/`)

- `cell.py`: primary simulation stepping logic (`Layer`, `Cell`, `step_forward`, `factory`).
- `live.py`: below-ground biomass distribution/integration/turnover/erosion/burial.
- `sediment.py`: labile/refractory/inorganic sediment transfers and erosion/deposition handling.
- `constants.py`: constants schema + TOML parsing (`import_file`).
- `marsh.py`: multi-cell orchestration wrapper.
- `stock.py`: stock tags, measurement conversion protocol/helpers.
- `validators.py`: numeric validation guards.
- `data.py`: CSV logging utility.

### Tests (`tests/`)

- `cell_test.py`, `constants_test.py`, `live_test.py`, `workflow_test.py`
- Test style: `unittest.TestCase` classes; runnable by both unittest discovery and pytest.

## 7) Behavioral constraints to preserve when editing

- Keep `Cell.step_forward` layer-processing order intact unless intentionally changing model semantics.
- Maintain validation behavior for non-negative and ordering checks in `validators.py` and callsites.
- Preserve compatibility of default constants file parsing in `constants.import_file`.
- Ensure changes continue to satisfy both pytest and unittest command paths above.

## 8) README contents summary (for quick context)

README documents:

- Scientific origin (Morris & Bowden 1986 DOI)
- Cell/layer conceptual model
- Timestep compute sequence and assumptions
- Example integration pattern for coupled models
- Non-conservative mass assumptions and discrete-time limitations

Use README assumptions as domain intent when choosing between competing code changes.

## 9) Practical agent policy for this repo

- Prefer surgical edits in `src/` + targeted tests.
- Avoid broad refactors unless explicitly requested.
- After code changes, always run the canonical validation order from section 4.
- When touching dependencies or packaging, update both `pyproject.toml` and `uv.lock`.
- Use search only if this instruction file does not answer a question.

## 10) Repository custom skills

- Repository-local skills live under `.github/skills/`.
- If a task matches a skill name/description in that directory, use that skill workflow before doing ad-hoc exploration.
- Always read the matching `SKILL.md` file for operating details when invoking a repository-local skill.
- Do not create extra index files for skills unless explicitly requested; this section is the canonical reminder for skill discovery.
