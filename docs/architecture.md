# Architecture

## Overview

rust-green is a three-tier web application:

- **Frontend** — vanilla HTML/CSS/JavaScript served statically
- **Backend** — FastAPI (Python) with async processing
- **Storage** — SQLite database + local filesystem

```
┌──────────────────────────────────────────────────────────────┐
│                    Browser (frontend/)                        │
│  index.html        sessions.html      session-detail.html    │
│  (submit code)     (list sessions)    (view results)         │
└────────────────────────────┬─────────────────────────────────┘
                             │  HTTP REST API
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (port 8000)                  │
│                                                              │
│  POST /api/v1/sessions      ← create analysis session        │
│  GET  /api/v1/sessions      ← list sessions                  │
│  GET  /api/v1/sessions/{id} ← get results                    │
│  GET  /api/v1/repos/refs    ← list Git branches/tags         │
│  GET  /api/v1/repos/tree    ← list Rust files in repo        │
└────────────────────────────┬─────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
       ┌────────────┐ ┌───────────┐ ┌────────────┐
       │ Git Service│ │SAST Svc   │ │ LLM Service│
       │ (clone)    │ │(Clippy +  │ │ (Deepseek) │
       └────────────┘ │ Semgrep)  │ └────────────┘
                      └───────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Analysis Worker │
                    │  (async queue)   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  SQLite + Files  │
                    │  sessions/       │
                    │  analyses/       │
                    │  sast_results/   │
                    └─────────────────┘
```

---

## Components

### Frontend (`frontend/`)

| File | Purpose |
|------|---------|
| `index.html` + `js/main.js` | Code/repo submission form, real-time progress polling |
| `sessions.html` + `sessions.js` | Paginated session list with status badges |
| `session-detail.html` + `session-detail.js` | Full results: SAST cards, findings, diffs |
| `js/git-handlers.js` | Git URL → fetch refs → fetch files (multi-select) |
| `js/api.js` | Centralised fetch wrapper |
| `css/` | BEM + utility CSS architecture |

### Backend (`backend/app/`)

#### API Layer (`api/v1/`)

| Module | Endpoints |
|--------|-----------|
| `sessions/crud.py` | CRUD for analysis sessions |
| `sessions/downloads.py` | Download fixed files and patches |
| `repos.py` | Git ref and file tree listing |

#### Services (`services/`)

| Service | Responsibility |
|---------|---------------|
| `git_service.py` | Clone repositories, list refs and files |
| `clippy_service.py` | Run `cargo clippy`, parse output, apply `--fix` |
| `semgrep_service.py` | Run Semgrep (native or Podman), parse JSON output, apply `--autofix` |
| `sast_service.py` | Orchestrate Clippy + Semgrep, compute verification score |
| `llm_service.py` | Deepseek API calls: analyse, remediate, verify |
| `patch_generator.py` | Generate unified diffs and ZIP archives |
| `diff_generator.py` | Git-style diff between original and fixed code |
| `file_storage_service.py` | Manage uploaded/cloned code on disk |
| `pipeline/analysis_worker.py` | Async job queue; orchestrates all phases |

#### Models (`models/`)

| Model | Type | Description |
|-------|------|-------------|
| `Session` | SQLAlchemy | Analysis session (status, progress, timestamps) |
| `CodeBlock` | SQLAlchemy | A single Rust code block submitted for analysis |
| `Analysis` | SQLAlchemy | LLM analysis result (vulnerability, remediation, diff) |
| `SastResult` | SQLAlchemy | One SAST tool run (phase, tool, issues, summary) |
| `SastIssue` | Pydantic | A single SAST finding |
| `SastReport` | Pydantic | Complete scan report |
| `SastVerification` | Pydantic | Before/after comparison with score |

---

## Analysis Pipeline

The pipeline runs asynchronously after a session is created. Progress is reported as a percentage (0–100%) polled by the frontend every 2 seconds.

```
Session Created (status: pending)
        │
        ▼  10%
1. Git Clone / Code Upload
        │
        ▼  20%
2. SAST Phase 1 — Initial Scan
   ├── cargo clippy --all-targets --all-features
   └── semgrep --config=auto
        │
        ▼  35%
3. SAST Phase 2 — Auto-fix
   ├── cargo clippy --fix --allow-dirty
   └── semgrep --autofix
        │
        ▼  50%
4. SAST Phase 3 — Post-fix Scan
   └── Re-scan to measure auto-fix impact
        │
        ▼  60%
5. LLM Analysis
   ├── Format SAST results as context
   ├── Deepseek: detect vulnerabilities (CWE/OWASP/risk/confidence)
   └── Deepseek: generate remediations
        │
        ▼  80%
6. Apply LLM Fixes
        │
        ▼  90%
7. SAST Phase 4 — Verification Scan
   └── Final scan; compute verification score
        │
        ▼  100%
Session Complete (status: completed)
```

### Verification Score

```
score = (resolved_issues / total_before_issues) - (new_issues × 0.1)
```

Clamped to [0, 1]. Displayed as a percentage in the UI.

---

## Data Flow

### Session creation (Git repository)

```
User → POST /api/v1/sessions { git_url, git_ref, selected_files }
     → Session created (id, status=pending)
     → Analysis worker picks up session
     → git clone <url> --branch <ref>
     → Filter to selected .rs files
     → SAST Phase 1 → Phase 2 → Phase 3
     → LLM analysis (with SAST context)
     → Apply fixes
     → SAST Phase 4 (verification)
     → Session status=completed
```

### Polling

```
Frontend polls GET /api/v1/sessions/{id}/status every 2s
  → { status, progress, ... }
  → When status=completed: fetch full GET /api/v1/sessions/{id}
  → Render SAST cards + findings + diffs
```

---

## Database Schema (simplified)

```sql
sessions        (id, status, progress, git_url, git_ref, created_at, completed_at, ...)
code_blocks     (id, session_id, raw_code, file_path, ...)
analyses        (id, session_id, code_block_id, vulnerability_type, cwe_id,
                 risk_level, confidence_score, suggested_replacement, diff, ...)
sast_results    (id, session_id, scan_phase, tool, status, issues JSON,
                 total_issues, summary JSON, auto_fixes_applied, created_at)
```
