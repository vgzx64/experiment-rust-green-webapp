# SAST Integration Documentation

This document describes the Static Application Security Testing (SAST) integration in the rust-green-webapp backend.

## Overview

The SAST integration provides automated security scanning of Rust code using multiple tools:

- **Clippy**: Rust's official linter with security-focused lints
- **Semgrep**: Modern SAST scanner with security pattern detection
- **Cargo-audit**: Dependency vulnerability scanner (planned)

## Architecture

### Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     Analysis Pipeline                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Git Clone / Code Upload                                     │
│         ↓                                                        │
│  2. SAST Phase 1: Initial Scan                                  │
│         ├── Clippy scan (Rust-specific issues)                  │
│         └── Semgrep scan (security patterns)                    │
│         ↓                                                        │
│  3. SAST Phase 2: Auto-fix                                      │
│         ├── Clippy --fix (apply safe fixes)                     │
│         └── Semgrep --autofix (apply security fixes)            │
│         ↓                                                        │
│  4. SAST Phase 3: Post-auto-fix Scan                            │
│         └── Re-scan to verify fixes                             │
│         ↓                                                        │
│  5. LLM Analysis Phase                                          │
│         ├── Format SAST results for LLM context                 │
│         ├── LLM vulnerability analysis                           │
│         └── LLM remediation suggestions                          │
│         ↓                                                        │
│  6. Apply LLM Fixes                                             │
│         └── Apply suggested code changes                        │
│         ↓                                                        │
│  7. SAST Phase 4: Verification Scan                             │
│         └── Final scan to verify all fixes                      │
│         ↓                                                        │
│  8. Generate Verification Report                                │
│         └── Compare before/after issues                         │
│         ↓                                                        │
│  9. Complete                                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Components

#### Services

| Service | File | Description |
|---------|------|-------------|
| `ClippyService` | `app/services/clippy_service.py` | Runs Clippy linter, parses output, applies fixes |
| `SemgrepService` | `app/services/semgrep_service.py` | Runs Semgrep scanner, parses output, applies fixes |
| `SastService` | `app/services/sast_service.py` | Orchestrates all SAST tools, generates verification |

#### Models

| Model | File | Description |
|-------|------|-------------|
| `SastIssue` | `app/models/sast_result.py` | Pydantic model for a single SAST finding |
| `SastReport` | `app/models/sast_result.py` | Pydantic model for a complete scan report |
| `SastVerification` | `app/models/sast_result.py` | Pydantic model for verification results |
| `SastResult` | `app/models/sast_result.py` | SQLAlchemy model for storing scan results |
| `SastVerificationResult` | `app/models/sast_result.py` | SQLAlchemy model for storing verification |

## Configuration

### Environment Variables

All SAST configuration uses the `SAST_` prefix:

#### General Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SAST_ENABLED` | bool | `true` | Enable/disable SAST scanning |
| `SAST_MAX_ISSUES_PER_SCAN` | int | `1000` | Maximum issues to report per scan |
| `SAST_FAIL_ON_TIMEOUT` | bool | `false` | Fail pipeline if SAST times out |

#### Clippy Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SAST_CLIPPY_ENABLED` | bool | `true` | Enable Clippy scanning |
| `SAST_CLIPPY_AUTO_FIX` | bool | `true` | Apply Clippy auto-fixes |
| `SAST_CLIPPY_TIMEOUT` | int | `120` | Timeout in seconds |
| `SAST_CLIPPY_WARN_LINTS` | list | `["suspicious", "correctness", "style", "complexity", "perf"]` | Lint categories to warn on |

#### Semgrep Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SAST_SEMGREP_ENABLED` | bool | `true` | Enable Semgrep scanning |
| `SAST_SEMGREP_AUTO_FIX` | bool | `true` | Apply Semgrep auto-fixes |
| `SAST_SEMGREP_TIMEOUT` | int | `300` | Timeout in seconds |
| `SAST_SEMGREP_CONFIG` | string | `"auto"` | Semgrep rule configuration |
| `SAST_SEMGREP_USE_CONTAINER` | bool | `false` | Run Semgrep in Podman container |
| `SAST_SEMGREP_CONTAINER_IMAGE` | string | `"semgrep/semgrep:latest"` | Container image to use |

#### Cargo-audit Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SAST_CARGO_AUDIT_ENABLED` | bool | `true` | Enable dependency scanning |
| `SAST_CARGO_AUDIT_TIMEOUT` | int | `60` | Timeout in seconds |

#### Podman Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SAST_PODMAN_PATH` | string | `"podman"` | Path to Podman executable |

### Example .env File

```env
# SAST Configuration
SAST_ENABLED=true

# Clippy
SAST_CLIPPY_ENABLED=true
SAST_CLIPPY_AUTO_FIX=true
SAST_CLIPPY_TIMEOUT=120

# Semgrep
SAST_SEMGREP_ENABLED=true
SAST_SEMGREP_AUTO_FIX=true
SAST_SEMGREP_TIMEOUT=300
SAST_SEMGREP_CONFIG=auto
SAST_SEMGREP_USE_CONTAINER=false

# Cargo-audit
SAST_CARGO_AUDIT_ENABLED=true
SAST_CARGO_AUDIT_TIMEOUT=60
```

## Usage

### Running SAST on a Session

SAST is automatically integrated into the analysis pipeline. When a session is created with a Git repository:

1. The repository is cloned
2. SAST tools scan the code
3. Auto-fixes are applied
4. LLM analysis uses SAST context
5. Verification scan confirms fixes

### Accessing SAST Results

SAST results are stored in the database and can be accessed via:

```python
from app.models import SastResult, SastVerificationResult

# Get SAST results for a session
sast_results = await db.execute(
    select(SastResult).where(SastResult.session_id == session_id)
)

# Get verification results
verification = await db.execute(
    select(SastVerificationResult).where(SastVerificationResult.session_id == session_id)
)
```

### SAST Issue Format

Each `SastIssue` contains:

```python
{
    "issue_id": "abc123",
    "rule_id": "clippy::unwrap_used",
    "tool": "clippy",
    "severity": "major",
    "message": "Called unwrap() on an Option",
    "file_path": "src/main.rs",
    "line_start": 42,
    "line_end": 42,
    "column_start": 5,
    "column_end": 15,
    "snippet": "let x = opt.unwrap();",
    "cwe_id": "CWE-476",
    "category": "security",
    "auto_fixable": false,
    "fix_suggestion": null
}
```

### Verification Status

The verification status indicates the result of comparing before/after scans:

| Status | Description |
|--------|-------------|
| `resolved` | All issues fixed, no new issues |
| `partial` | Some issues fixed, some remain |
| `unresolved` | No issues fixed |
| `degraded` | New issues introduced |

### Verification Score

The verification score is a percentage (0-100) calculated as:

```
score = (resolved_issues / total_before_issues) - (new_issues * 0.1)
```

## Running Semgrep in Container

To run Semgrep in a Podman container:

1. Set environment variables:
```env
SAST_SEMGREP_USE_CONTAINER=true
SAST_SEMGREP_CONTAINER_IMAGE=semgrep/semgrep:latest
```

2. Ensure Podman is installed and running:
```bash
podman info
```

3. Pull the Semgrep image:
```bash
podman pull semgrep/semgrep:latest
```

## LLM Integration

SAST results are formatted and included in the LLM prompt:

```
============================================================
SAST ANALYSIS RESULTS
============================================================

Total issues found: 5

--- CLIPPY Issues ---

Clippy found the following issues:

1. [MAJOR] clippy::unwrap_used
   File: src/main.rs:42
   Message: Called unwrap() on an Option value

--- SEMGREP Issues ---

Semgrep found the following security issues:

1. [CRITICAL] rust.security.buffer-overflow
   File: src/buffer.rs:15
   Message: Potential buffer overflow in unsafe block
   CWE: CWE-787

============================================================
Please consider these SAST findings in your analysis.
============================================================
```

## Database Schema

### sast_results Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | String(36) | Primary key |
| `session_id` | String(36) | Foreign key to sessions |
| `scan_phase` | String(20) | `before_auto_fix`, `after_auto_fix`, `after_llm` |
| `tool` | String(20) | `clippy`, `semgrep`, `cargo-audit` |
| `status` | String(20) | `success`, `timeout`, `error` |
| `issues` | JSON | List of SastIssue dicts |
| `total_issues` | Integer | Count of issues |
| `summary` | JSON | Severity breakdown |
| `auto_fixes_applied` | Integer | Fixes applied count |
| `auto_fixes_failed` | Integer | Fixes failed count |
| `error_message` | Text | Error if failed |
| `raw_output` | JSON | Raw tool output |
| `created_at` | DateTime | Timestamp |

### sast_verifications Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | String(36) | Primary key |
| `session_id` | String(36) | Foreign key to sessions |
| `analysis_id` | String(36) | Foreign key to analyses |
| `verification_status` | String(20) | `resolved`, `partial`, `unresolved`, `degraded` |
| `verification_score` | Integer | 0-100 percentage |
| `issues_before` | Integer | Issues before fixes |
| `issues_after` | Integer | Issues after fixes |
| `issues_resolved` | Integer | Resolved count |
| `issues_remaining` | Integer | Remaining count |
| `issues_new` | Integer | New issues count |
| `resolved_issues` | JSON | List of resolved issue IDs |
| `remaining_issues` | JSON | List of remaining issue IDs |
| `new_issues` | JSON | List of new issue IDs |
| `severity_before` | JSON | Severity breakdown before |
| `severity_after` | JSON | Severity breakdown after |
| `verification_notes` | Text | Human-readable notes |
| `created_at` | DateTime | Timestamp |

## Troubleshooting

### Clippy Not Found

Ensure Rust and Clippy are installed:
```bash
rustup component add clippy
```

### Semgrep Not Found

Install Semgrep:
```bash
pip install semgrep
```

### Timeout Errors

Increase timeout values:
```env
SAST_CLIPPY_TIMEOUT=300
SAST_SEMGREP_TIMEOUT=600
```

### Container Permission Issues

Ensure Podman has access to the project directory:
```bash
podman run --rm -v $(pwd):/src:Z semgrep/semgrep semgrep --config=auto /src
```

## Testing

Run SAST service tests:
```bash
cd backend
python -m pytest tests/test_sast_service.py -v
```

Run all tests:
```bash
cd backend
python -m pytest tests/ -v