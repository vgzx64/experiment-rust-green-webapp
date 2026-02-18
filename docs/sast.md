# SAST Integration

rust-green integrates two static analysis tools — **Clippy** (Rust's official linter) and **Semgrep** (pattern-based scanner) — into a four-phase pipeline that runs before and after LLM analysis.

---

## Pipeline phases

| Phase | When | Tools | Purpose |
|-------|------|-------|---------|
| `before_auto_fix` | Start of pipeline | Clippy + Semgrep | Baseline scan — measure initial issue count |
| `after_auto_fix` | After tool auto-fixes | Clippy + Semgrep | Measure what tools fixed automatically |
| `after_llm` | After LLM fixes applied | Clippy + Semgrep | Measure what LLM fixed |
| `verification` | Final | Clippy + Semgrep | Compute verification score |

Results from all phases are stored in `sast_results` and returned in the session API response.

---

## Clippy

Clippy is Rust's built-in linter. rust-green runs it via `cargo clippy`.

### Scan command

```bash
cargo clippy --all-targets --all-features -- \
  -D warnings \
  -W clippy::suspicious \
  -W clippy::correctness \
  -W clippy::style \
  -W clippy::complexity \
  -W clippy::perf
```

### Auto-fix command

```bash
cargo clippy --fix --allow-dirty --allow-staged -- \
  -W clippy::suspicious \
  -W clippy::correctness \
  -W clippy::style \
  -W clippy::complexity \
  -W clippy::perf
```

### Known issue: deprecated lint names

Older Rust code (e.g. `time-macros` v0.3.7) may use bare lint names like `suspicious` instead of `clippy::suspicious`. These cause hard errors with modern Clippy:

```
error: lint name `suspicious` is deprecated and may not have an effect in the future
  = help: change it to clippy::suspicious
```

rust-green handles this gracefully — the SAST result is stored with `status=error` and the error message is surfaced in the UI. The LLM analysis still proceeds using the error output as context.

### Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SAST_CLIPPY_ENABLED` | `true` | Enable Clippy |
| `SAST_CLIPPY_AUTO_FIX` | `true` | Apply `--fix` |
| `SAST_CLIPPY_TIMEOUT` | `120` | Seconds before timeout |
| `SAST_CLIPPY_WARN_LINTS` | `["clippy::suspicious", "clippy::correctness", "clippy::style", "clippy::complexity", "clippy::perf"]` | Lint groups |

---

## Semgrep

Semgrep is a pattern-based SAST scanner with a large rule library for Rust security patterns.

### Scan command

```bash
semgrep --config=auto --json src/
```

Or in Podman:

```bash
podman run --rm -v /path/to/repo:/src:Z semgrep/semgrep \
  semgrep --config=auto --json /src
```

### Auto-fix command

```bash
semgrep --config=auto --autofix src/
```

### Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SAST_SEMGREP_ENABLED` | `true` | Enable Semgrep |
| `SAST_SEMGREP_AUTO_FIX` | `true` | Apply `--autofix` |
| `SAST_SEMGREP_TIMEOUT` | `300` | Seconds before timeout |
| `SAST_SEMGREP_CONFIG` | `"auto"` | Semgrep rule config |
| `SAST_SEMGREP_USE_CONTAINER` | `false` | Run in Podman |
| `SAST_SEMGREP_CONTAINER_IMAGE` | `"semgrep/semgrep:latest"` | Container image |

---

## Issue format

Each SAST finding (`SastIssue`) has the following fields:

```json
{
  "issue_id": "a1b2c3",
  "rule_id": "clippy::unwrap_used",
  "tool": "clippy",
  "severity": "major",
  "message": "called `unwrap()` on an `Option` value",
  "file_path": "src/main.rs",
  "line_start": 42,
  "line_end": 42,
  "column_start": 5,
  "column_end": 20,
  "snippet": "let x = opt.unwrap();",
  "cwe_id": "CWE-476",
  "auto_fixable": false
}
```

### Severity mapping

| Tool level | rust-green severity |
|------------|-------------------|
| `error` | `major` |
| `warning` | `minor` |
| `note` / `help` | `info` |

---

## Verification score

After all fixes are applied, the final SAST scan computes:

```
score = (resolved / total_before) - (new_issues × 0.1)
```

Clamped to [0, 1]. The verification status is one of:

| Status | Meaning |
|--------|---------|
| `resolved` | All issues fixed, no new issues |
| `partial` | Some issues fixed |
| `unresolved` | No issues fixed |
| `degraded` | New issues introduced |

---

## LLM context

SAST results are formatted and injected into the LLM prompt before vulnerability analysis:

```
============================================================
SAST ANALYSIS RESULTS
============================================================
Total issues found: 13

--- CLIPPY Issues ---
1. [MAJOR] renamed-and-removed-lints
   File: time-macros/src/lib.rs:4
   Message: lint name `suspicious` is deprecated

--- SEMGREP Issues ---
(none found)
============================================================
Primary objective: fix the vulnerability in the code.
Secondary objective: address SAST findings only if fully confident.
============================================================
```

This framing ensures the LLM prioritises semantic security fixes over mechanical lint fixes.

---

## Troubleshooting

**Clippy not found**
```bash
rustup component add clippy
```

**Semgrep not found**
```bash
pip install semgrep
```

**Timeout errors** — increase timeouts in `.env`:
```env
SAST_CLIPPY_TIMEOUT=300
SAST_SEMGREP_TIMEOUT=600
```

**Podman permission errors**
```bash
podman run --rm -v $(pwd):/src:Z semgrep/semgrep semgrep --config=auto /src
```
