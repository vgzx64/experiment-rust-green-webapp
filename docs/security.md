# Security

This page documents the threat model, risk assessment, and mitigation measures for rust-green. The analysis follows the STRIDE methodology applied to the system's data flow diagram.

---

## Trust boundaries

```
[User Browser] ──HTTP──► [FastAPI Backend] ──HTTPS──► [Deepseek LLM API]
                                │
                         [SQLite + Files]   (local filesystem, trusted)
```

| Boundary | Trust level |
|----------|-------------|
| User browser → Backend | Untrusted (public internet) |
| Backend → Deepseek API | Semi-trusted (external service) |
| Backend → SQLite | Trusted (local) |

---

## STRIDE threat analysis

### Spoofing

| # | Threat | Component | Mitigation |
|---|--------|-----------|------------|
| S1 | Forged API requests | FastAPI endpoints | API key authentication (planned) |
| S2 | LLM API key theft | LLM Service | Environment variables; key rotation |
| S3 | CSRF attacks | Web Interface | CORS restrictions; SameSite cookies |
| S4 | Session ID prediction | Session Manager | UUID v4 session IDs |

### Tampering

| # | Threat | Component | Mitigation |
|---|--------|-----------|------------|
| T1 | SQL injection | API endpoints | SQLAlchemy parameterised queries (implemented) |
| T2 | Path traversal | File Storage | UUID-based filenames; path validation |
| T3 | Prompt injection | LLM Service | Structured JSON prompts; output validation |
| T4 | Analysis result modification | Database | Checksums on results (planned) |

### Repudiation

| # | Threat | Component | Mitigation |
|---|--------|-----------|------------|
| R1 | No audit trail for submissions | API Gateway | Structured logging (planned) |
| R2 | No LLM call logging | LLM Service | Request/response logging (planned) |

### Information Disclosure

| # | Threat | Component | Mitigation |
|---|--------|-----------|------------|
| I1 | Source code sent to external LLM | LLM Service | Data masking for secrets; user consent |
| I2 | Stack traces in error responses | API Gateway | Custom error handlers (implemented) |
| I3 | Unencrypted code storage | File Storage | Filesystem encryption (planned) |
| I4 | API key in logs | LLM Service | Redact keys from log output |

### Denial of Service

| # | Threat | Component | Mitigation |
|---|--------|-----------|------------|
| D1 | Large file uploads | File Storage | File size limits (10 MB) |
| D2 | LLM API quota exhaustion | LLM Service | Per-IP rate limiting (planned) |
| D3 | Analysis queue flooding | Analysis Worker | Queue depth limit; timeout per job |
| D4 | Database connection exhaustion | SQLite | Connection pool limits (QueuePool) |
| D5 | Disk space exhaustion | File Storage | Automatic session cleanup (planned) |

### Elevation of Privilege

| # | Threat | Component | Mitigation |
|---|--------|-----------|------------|
| E1 | Accessing other users' results | Session API | No authentication currently (research prototype) |
| E2 | Worker process with excess permissions | Analysis Worker | Run as unprivileged user |
| E3 | File system privilege escalation | File Storage | Restricted directory; no symlink following |

---

## Risk prioritisation (CVSS v3.1)

| Threat | CVSS Score | Priority | Status |
|--------|-----------|----------|--------|
| T1 — SQL injection | 9.8 | **P0 Critical** | ✅ Mitigated (parameterised queries) |
| I1 — Code sent to external LLM | 8.6 | P1 High | ⚠️ Accepted (by design) |
| I2 — Stack traces in errors | 8.6 | P1 High | ✅ Mitigated |
| S2 — API key theft | 8.6 | P1 High | ✅ Mitigated (env vars) |
| D1 — Large file DoS | 7.8 | P1 High | ✅ Mitigated (size limits) |
| D2 — API quota exhaustion | 7.8 | P2 Medium | ⬜ Planned |
| T3 — Prompt injection | 7.5 | P2 Medium | ✅ Partially mitigated |
| E1 — No access control | 6.3 | P3 Low | ⚠️ Accepted (research prototype) |

---

## Implemented mitigations

### SQL injection prevention

All database queries use SQLAlchemy ORM with parameterised statements. Raw SQL is never constructed from user input.

```python
# Safe — SQLAlchemy ORM
session = await db.get(Session, session_id)

# Safe — explicit parameterisation
result = await db.execute(
    select(Session).where(Session.id == session_id)
)
```

### Error message sanitisation

Production error responses return only a `detail` string — no stack traces, file paths, or internal state.

### API key management

The Deepseek API key is loaded exclusively from environment variables:

```python
api_key: str = os.getenv("LLM_API_KEY", "")
```

The `.env` file is listed in `.gitignore` and never committed.

### File path safety

Uploaded and cloned files are stored under a session-specific UUID directory. File names are sanitised and symlinks are not followed.

### Connection pool limits

```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=5,
    pool_timeout=30,
)
```

---

## Accepted risks (research prototype)

The following risks are accepted for the current research/prototype context:

| Risk | Reason accepted |
|------|----------------|
| No user authentication | Single-user research tool; no sensitive multi-tenant data |
| Code sent to Deepseek API | Core functionality; users are informed |
| No HTTPS | Development environment only; production deployment should add TLS |
| No audit logging | Planned for production version |

---

## Security recommendations for production deployment

1. **Add TLS** — deploy behind nginx/Caddy with HTTPS
2. **Add authentication** — JWT or API key auth on all endpoints
3. **Rate limiting** — `slowapi` middleware, 10 req/min per IP for session creation
4. **Structured audit logging** — log all session creation, LLM calls, file access
5. **Database encryption** — SQLCipher for SQLite at rest
6. **Secret scanning** — mask API keys, passwords, tokens before sending to LLM
7. **Container isolation** — run analysis worker in a restricted container
8. **Dependency scanning** — `cargo audit` in CI pipeline
