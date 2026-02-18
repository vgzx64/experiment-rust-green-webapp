# rust-green

> **AI-powered Rust code security analysis platform**

rust-green automatically detects security vulnerabilities in Rust code, generates safe remediations, and verifies fixes — combining static analysis (Clippy, Semgrep) with a large language model (Deepseek) in a unified six-phase pipeline.

---

## Key capabilities

- **Git repository analysis** — point at any public Rust repo; rust-green clones it and analyses all `.rs` files
- **Multi-tool SAST** — Clippy and Semgrep scan in parallel, auto-fixes applied before LLM analysis
- **LLM vulnerability analysis** — Deepseek identifies issues with CWE/OWASP mapping, risk level, and confidence score
- **Verified remediations** — a final SAST scan scores how many issues were resolved (0–100%)
- **Downloadable patches** — unified diffs and ZIP archives of fixed files

---

## Navigation

| Page | Description |
|------|-------------|
| [Architecture](architecture.md) | System design, component breakdown, pipeline diagram |
| [API Reference](api.md) | REST endpoints, request/response schemas |
| [SAST Integration](sast.md) | Clippy, Semgrep, configuration, output format |
| [Security](security.md) | Threat model, STRIDE analysis, mitigations |
| [Development](development.md) | Setup, testing, code style |

---

## Quick start

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set LLM_API_KEY
./start.sh             # → http://localhost:8000

# Frontend
cd ../frontend
python -m http.server 3000   # → http://localhost:3000
```

See [Development](development.md) for full setup instructions.

---

## Test case: RUSTSEC-2026-0009

The primary test case used during development is the `time-rs` crate at tag `v0.3.7`, specifically the `time-macros` subcrate. This version contains deprecated lint names and removed lints that cause Clippy to fail with hard errors — a realistic scenario where SAST tooling must handle legacy code gracefully.

- **Repository**: `https://github.com/time-rs/time`
- **Tag**: `0.3.7`
- **Focus**: `time-macros/src/` — `combinator`, `rfc2822` modules
- **Advisory**: [RUSTSEC-2026-0009](https://osv.dev/vulnerability/RUSTSEC-2026-0009)
