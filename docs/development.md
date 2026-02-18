# Development

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | [python.org](https://python.org) |
| Rust + Cargo | 1.70+ | `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \| sh` |
| Clippy | latest | `rustup component add clippy` |
| Semgrep | latest | `pip install semgrep` |
| Podman (optional) | latest | [podman.io](https://podman.io) |

---

## Setup

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — at minimum set:
#   LLM_API_KEY=sk-...
#   LLM_ENABLED=true

# Start the server
./start.sh
# Or directly:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API is now available at `http://localhost:8000`.  
Swagger UI: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
python -m http.server 3000
# Open http://localhost:3000
```

Or simply open `frontend/index.html` directly in a browser (CORS is configured to allow `localhost`).

### Documentation site

```bash
pip install mkdocs mkdocs-material
mkdocs serve        # → http://127.0.0.1:8000 (use a different port if backend is running)
mkdocs build        # → site/ directory (static HTML)
```

To serve docs on a different port:
```bash
mkdocs serve --dev-addr=127.0.0.1:8001
```

---

## Environment variables

See `backend/.env.example` for the full list. Key variables:

### LLM

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_API_KEY` | Deepseek API key | **required** |
| `LLM_MODEL` | Model name | `deepseek-chat` |
| `LLM_BASE_URL` | API base URL | `https://api.deepseek.com/v1` |
| `LLM_ENABLED` | Enable LLM calls | `true` |
| `LLM_TEMPERATURE` | Response temperature | `0.1` |
| `LLM_TIMEOUT` | Request timeout (s) | `180` |
| `LLM_MAX_TOKENS` | Max tokens per call | `4000` |

### SAST

| Variable | Description | Default |
|----------|-------------|---------|
| `SAST_ENABLED` | Enable SAST pipeline | `true` |
| `SAST_CLIPPY_ENABLED` | Enable Clippy | `true` |
| `SAST_CLIPPY_AUTO_FIX` | Apply Clippy fixes | `true` |
| `SAST_SEMGREP_ENABLED` | Enable Semgrep | `true` |
| `SAST_SEMGREP_USE_CONTAINER` | Run Semgrep in Podman | `false` |

---

## Testing

### Run all tests

```bash
cd backend
pytest tests/ -v
```

### Run with coverage

```bash
pytest tests/ -v --cov=app --cov-report=html
# Open htmlcov/index.html
```

### Run specific test file

```bash
pytest tests/test_sast_service.py -v
pytest tests/test_diff_generator.py -v
pytest tests/test_llm_service.py -v   # uses mocks by default
```

### Test with real LLM API

```bash
export LLM_ENABLED=true
export LLM_API_KEY=sk-...
pytest tests/test_llm_service.py -v -k "not mock"
```

### Test structure

```
backend/tests/
├── conftest.py              # Shared fixtures (async DB, test client)
├── test_api_sessions.py     # Session CRUD endpoint tests
├── test_api_repos.py        # Repo listing endpoint tests
├── test_diff_generator.py   # Diff generation unit tests (15 tests)
├── test_llm_service.py      # LLM service mock tests (20 tests)
├── test_sast_service.py     # SAST orchestration tests
├── test_session_service.py  # Session service tests
├── test_git_service.py      # Git clone/list tests
├── test_file_storage.py     # File storage tests
├── test_patch_generator.py  # Patch generation tests
├── test_models.py           # SQLAlchemy model tests
└── test_cases/
    └── buffer_overflow/
        ├── original.rs          # Vulnerable code
        ├── fixed.rs             # Expected fix
        ├── result_suggestion.rs # LLM output
        └── result_explanation.txt
```

---

## Code style

### Format

```bash
black app tests
isort app tests
```

### Type checking

```bash
mypy app
```

### Lint

```bash
flake8 app tests --max-line-length=100
```

---

## Database

The application uses SQLite with SQLAlchemy async support (`aiosqlite`).

### Location

```
backend/rust_green.db   (created automatically on first run)
```

### Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "add sast_results table"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

### Reset database (development)

```bash
rm backend/rust_green.db
# Restart the server — tables are recreated automatically
```

---

## Project structure

```
rust-green-webapp/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── dto/              # Pydantic request/response models
│   │   │   └── v1/               # FastAPI routers
│   │   │       ├── sessions/
│   │   │       │   ├── crud.py   # Session CRUD endpoints
│   │   │       │   └── downloads.py
│   │   │       └── repos.py
│   │   ├── config/
│   │   │   ├── llm_config.py
│   │   │   └── sast_config.py
│   │   ├── models/               # SQLAlchemy ORM models
│   │   ├── schemas/              # Additional Pydantic schemas
│   │   ├── services/
│   │   │   ├── pipeline/
│   │   │   │   └── analysis_worker.py
│   │   │   ├── clippy_service.py
│   │   │   ├── semgrep_service.py
│   │   │   ├── sast_service.py
│   │   │   ├── llm_service.py
│   │   │   ├── git_service.py
│   │   │   ├── patch_generator.py
│   │   │   ├── diff_generator.py
│   │   │   └── file_storage_service.py
│   │   ├── database.py           # SQLAlchemy engine + session
│   │   └── main.py               # FastAPI app + startup
│   ├── tests/
│   ├── docs/
│   │   └── SAST_INTEGRATION.md
│   ├── requirements.txt
│   ├── .env.example
│   └── start.sh
├── frontend/
│   ├── index.html
│   ├── sessions.html
│   ├── session-detail.html
│   ├── style.css
│   ├── css/                      # BEM component CSS
│   └── js/
│       ├── main.js
│       ├── api.js
│       ├── git-handlers.js
│       ├── findings.js
│       └── utils.js
├── docs/                         # MkDocs pages
├── mkdocs.yml
└── README.md
```

---

## Adding a new SAST tool

1. Create `backend/app/services/my_tool_service.py` following the pattern of `clippy_service.py`
2. Implement `run_scan(project_path) -> SastReport` and `_apply_fixes(project_path)`
3. Register the tool in `sast_service.py` → `run_all_tools()`
4. Add configuration variables to `sast_config.py` and `.env.example`
5. Write tests in `tests/test_sast_service.py`
