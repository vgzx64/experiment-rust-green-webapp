# rust-green

> **AI-powered Rust code security analysis platform**

rust-green is a full-stack web application that automatically detects security vulnerabilities in Rust code, generates safe remediations, and verifies fixes — combining static analysis tools (Clippy, Semgrep) with a large language model (Deepseek) in a unified pipeline.

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com)
[![Rust](https://img.shields.io/badge/Rust-1.70+-orange)](https://rust-lang.org)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)

---

## What it does

1. **Submit** a Rust Git repository URL or paste code directly
2. **SAST scan** — Clippy and Semgrep scan the code and apply auto-fixes
3. **LLM analysis** — Deepseek identifies vulnerabilities with CWE/OWASP mapping, generates safe remediations
4. **Verification** — a final SAST scan scores how many issues were resolved
5. **Download** — get unified diffs and patched files

---

## Quick Start

### Prerequisites

- Python 3.11+
- Rust + Clippy: `rustup component add clippy`
- Semgrep: `pip install semgrep`
- A [Deepseek API key](https://platform.deepseek.com/)

### Install & Run

```bash
# Clone
git clone https://github.com/vgdaut/experiment-rust-green-webapp
cd rust-green-webapp

# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add your LLM_API_KEY
./start.sh                    # → http://localhost:8000

# Frontend (separate terminal)
cd ../frontend
# Open index.html in a browser, or serve with:
python -m http.server 3000    # → http://localhost:3000
```

### Documentation site

```bash
pip install mkdocs mkdocs-material
mkdocs serve    # → http://127.0.0.1:8000/docs
mkdocs build    # → site/ (static HTML)
```

---

## Architecture

```
Browser (frontend/)
    │  REST API
    ▼
FastAPI (backend/)
    │
    ├── Git Service          — clone repositories
    ├── SAST Service         — orchestrate Clippy + Semgrep
    │     ├── Clippy Service — Rust linter + auto-fix
    │     └── Semgrep Service— pattern scanner + auto-fix
    ├── LLM Service          — Deepseek vulnerability analysis
    ├── Patch Generator      — unified diffs + ZIP
    └── Analysis Worker      — async pipeline orchestration
          │
          ▼
    SQLite (sessions, analyses, SAST results)
```

**Pipeline phases:**

| Phase | What happens |
|-------|-------------|
| 1. Initial SAST | Clippy + Semgrep scan the raw code |
| 2. Auto-fix | Tools apply safe fixes automatically |
| 3. Post-fix SAST | Re-scan to measure auto-fix impact |
| 4. LLM Analysis | Deepseek analyses remaining issues with SAST context |
| 5. LLM Fixes | Apply LLM-suggested remediations |
| 6. Verification | Final SAST scan; compute resolution score |

---

## Documentation

| Page | Description |
|------|-------------|
| [Architecture](docs/architecture.md) | System design, component breakdown, data flow |
| [API Reference](docs/api.md) | REST endpoints, request/response schemas |
| [SAST Integration](docs/sast.md) | Clippy, Semgrep, configuration, output format |
| [Security](docs/security.md) | Threat model, STRIDE analysis, mitigations |
| [Development](docs/development.md) | Setup, testing, code style |

---

## Project Structure

```
rust-green-webapp/
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── api/v1/           # REST endpoints
│   │   ├── config/           # LLM + SAST configuration
│   │   ├── models/           # SQLAlchemy + Pydantic models
│   │   └── services/         # Business logic
│   │       ├── pipeline/     # Async analysis worker
│   │       ├── clippy_service.py
│   │       ├── semgrep_service.py
│   │       ├── sast_service.py
│   │       ├── llm_service.py
│   │       └── git_service.py
│   ├── tests/
│   └── docs/
├── frontend/                 # Vanilla JS + CSS
│   ├── index.html            # Analysis submission
│   ├── sessions.html         # Session list
│   ├── session-detail.html   # Results view
│   └── js/
├── docs/                     # MkDocs documentation
└── mkdocs.yml
```

---

## License

MIT — see [LICENSE](LICENSE).
