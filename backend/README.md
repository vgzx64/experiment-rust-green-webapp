# rust-green-webapp Backend

A FastAPI-based backend for automated Rust code security analysis with LLM-powered remediation and SAST integration.

## Features

- **Git Repository Analysis**: Clone and analyze Rust repositories
- **Code Upload**: Direct code submission for analysis
- **SAST Integration**: Multi-tool static analysis with Clippy and Semgrep
- **LLM Analysis**: Deepseek-powered vulnerability detection and remediation
- **Auto-fix**: Automatic application of safe fixes before LLM analysis
- **Verification**: Post-remediation SAST verification with scoring
- **Patch Generation**: Unified diff and ZIP file generation for fixes

## Quick Start

### Prerequisites

- Python 3.11+
- Rust and Clippy (`rustup component add clippy`)
- Semgrep (`pip install semgrep`) or Podman for containerized scanning

### Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the server:
```bash
./start.sh
# Or: uvicorn app.main:app --reload
```

### Using Podman for Semgrep

If you prefer containerized scanning:

```bash
# Pull the Semgrep image
podman pull semgrep/semgrep:latest

# Set in .env
SAST_SEMGREP_USE_CONTAINER=true
```

## API Endpoints

### Sessions

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/sessions` | Create a new analysis session |
| `GET` | `/api/v1/sessions` | List all sessions |
| `GET` | `/api/v1/sessions/{id}` | Get session details |
| `GET` | `/api/v1/sessions/{id}/status` | Get session status |
| `PATCH` | `/api/v1/sessions/{id}` | Update session |
| `GET` | `/api/v1/sessions/{id}/download/fixed` | Download fixed files |
| `GET` | `/api/v1/sessions/{id}/download/patches` | Download patches |

### Repos

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/repos/refs` | List Git refs for a repository |
| `GET` | `/api/v1/repos/tree` | List files in a repository |

## Configuration

See `.env.example` for all configuration options.

### LLM Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_API_KEY` | Deepseek API key | Required |
| `LLM_MODEL` | Model to use | `deepseek-chat` |
| `LLM_BASE_URL` | API base URL | `https://api.deepseek.com/v1` |
| `LLM_ENABLED` | Enable LLM analysis | `true` |
| `LLM_MAX_TOKENS` | Max tokens per request | `4000` |
| `LLM_TEMPERATURE` | Response temperature | `0.1` |
| `LLM_TIMEOUT` | Request timeout (seconds) | `180` |

### SAST Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `SAST_ENABLED` | Enable SAST scanning | `true` |
| `SAST_CLIPPY_ENABLED` | Enable Clippy | `true` |
| `SAST_CLIPPY_AUTO_FIX` | Apply Clippy fixes | `true` |
| `SAST_SEMGREP_ENABLED` | Enable Semgrep | `true` |
| `SAST_SEMGREP_AUTO_FIX` | Apply Semgrep fixes | `true` |
| `SAST_SEMGREP_USE_CONTAINER` | Run in Podman | `false` |

See [SAST_INTEGRATION.md](docs/SAST_INTEGRATION.md) for detailed documentation.

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── dto/              # Data Transfer Objects
│   │   └── v1/               # API v1 endpoints
│   ├── config/               # Configuration modules
│   │   ├── llm_config.py     # LLM settings
│   │   └── sast_config.py    # SAST settings
│   ├── models/               # SQLAlchemy models
│   │   ├── session.py        # Session model
│   │   ├── analysis.py       # Analysis model
│   │   ├── code_block.py     # CodeBlock model
│   │   └── sast_result.py    # SAST result models
│   ├── services/
│   │   ├── clippy_service.py # Clippy integration
│   │   ├── semgrep_service.py# Semgrep integration
│   │   ├── sast_service.py   # SAST orchestration
│   │   ├── llm_service.py    # LLM integration
│   │   ├── git_service.py    # Git operations
│   │   ├── patch_generator.py# Patch generation
│   │   └── pipeline/
│   │       └── analysis_worker.py  # Main pipeline
│   └── main.py               # FastAPI application
├── tests/                    # Test suite
├── docs/
│   └── SAST_INTEGRATION.md   # SAST documentation
├── requirements.txt
├── .env.example
└── README.md
```

## Analysis Pipeline

```
1. Session Created
       ↓
2. Git Clone / Code Upload
       ↓
3. SAST Phase 1: Initial Scan
   - Clippy scan
   - Semgrep scan
       ↓
4. SAST Phase 2: Auto-fix
   - Clippy --fix
   - Semgrep --autofix
       ↓
5. SAST Phase 3: Post-fix Scan
       ↓
6. LLM Analysis (with SAST context)
       ↓
7. Apply LLM Fixes
       ↓
8. SAST Phase 4: Verification
       ↓
9. Generate Results
   - Analysis records
   - Verification report
   - Patch files
       ↓
10. Session Complete
```

## Testing

Run all tests:
```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ -v --cov=app --cov-report=html
```

Run specific test file:
```bash
pytest tests/test_sast_service.py -v
```

## Database

The application uses SQLite by default with SQLAlchemy async support.

### Migrations

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Development

### Code Style

Format code:
```bash
black app tests
isort app tests
```

### Type Checking

```bash
mypy app
```

## License

MIT License