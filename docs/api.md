# API Reference

Base URL: `http://localhost:8000/api/v1`

Interactive docs (Swagger UI): `http://localhost:8000/docs`

---

## Sessions

### Create session

```
POST /sessions
```

**Request body**

```json
{
  "git_url": "https://github.com/time-rs/time",
  "git_ref": "v0.3.7",
  "selected_files": ["time-macros/src/lib.rs", "time-macros/src/date.rs"],
  "code": null
}
```

Either `git_url` + `git_ref` (+ optional `selected_files`) **or** `code` (raw Rust string) must be provided.

**Response** `201 Created`

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "pending",
  "progress": 0,
  "created_at": "2026-02-18T10:00:00Z"
}
```

---

### List sessions

```
GET /sessions?page=1&page_size=20&status=completed
```

**Query parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Items per page (max 100) |
| `status` | string | — | Filter by status |

**Response** `200 OK`

```json
{
  "sessions": [ { "id": "...", "status": "completed", "progress": 100, ... } ],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

---

### Get session

```
GET /sessions/{id}
```

Returns full session data including all analyses and SAST results.

**Response** `200 OK`

```json
{
  "id": "3fa85f64-...",
  "status": "completed",
  "progress": 100,
  "git_url": "https://github.com/time-rs/time",
  "git_ref": "v0.3.7",
  "created_at": "2026-02-18T10:00:00Z",
  "completed_at": "2026-02-18T10:02:30Z",
  "error_message": null,
  "verification_status": "partial",
  "verification_score": 0.72,
  "issues_resolved": 8,
  "issues_remaining": 3,
  "analyses": [
    {
      "id": "abc123",
      "code_block_type": "replaceable",
      "vulnerability_type": "Use of deprecated lint names",
      "cwe_id": "CWE-710",
      "owasp_category": "A05:2021",
      "risk_level": "medium",
      "confidence_score": 0.91,
      "exploitation_scenario": "...",
      "suggested_replacement": "...",
      "diff": "--- a/src/lib.rs\n+++ b/src/lib.rs\n..."
    }
  ],
  "sast_results": [
    {
      "tool": "clippy",
      "scan_phase": "before_auto_fix",
      "status": "error",
      "total_issues": 13,
      "summary": { "blocker": 0, "critical": 0, "major": 8, "minor": 5, "info": 0 },
      "issues": [ { "rule_id": "renamed-and-removed-lints", "severity": "major", ... } ],
      "auto_fixes_applied": 0,
      "error_message": "could not compile `time-macros`"
    }
  ]
}
```

---

### Get session status

```
GET /sessions/{id}/status
```

Lightweight endpoint for polling. Returns only status and progress.

**Response** `200 OK`

```json
{
  "id": "3fa85f64-...",
  "status": "processing",
  "progress": 60,
  "error_message": null
}
```

**Status values**

| Status | Description |
|--------|-------------|
| `pending` | Queued, not yet started |
| `processing` | Pipeline running |
| `completed` | All phases finished successfully |
| `failed` | Pipeline encountered a fatal error |

---

### Update session

```
PATCH /sessions/{id}
```

**Request body** (all fields optional)

```json
{
  "status": "failed",
  "error_message": "LLM API timeout"
}
```

---

### Delete session

```
DELETE /sessions/{id}
```

Deletes the session and all associated analyses, SAST results, and files.

**Response** `204 No Content`

---

### Download fixed files

```
GET /sessions/{id}/download/fixed
```

Returns a ZIP archive containing all files after LLM fixes were applied.

**Response** `200 OK` — `application/zip`

---

### Download patches

```
GET /sessions/{id}/download/patches
```

Returns a ZIP archive of unified diff patch files (`.patch`).

**Response** `200 OK` — `application/zip`

---

## Repositories

### List Git refs

```
GET /repos/refs?url=https://github.com/time-rs/time
```

**Query parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | ✓ | Git repository URL |

**Response** `200 OK`

```json
{
  "branches": ["main", "master", "v0.3-dev"],
  "tags": ["v0.3.7", "v0.3.6", "v0.3.5"],
  "default_branch": "main"
}
```

---

### List repository files

```
GET /repos/tree?url=https://github.com/time-rs/time&ref=v0.3.7
```

**Query parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | ✓ | Git repository URL |
| `ref` | string | ✓ | Branch, tag, or commit SHA |

**Response** `200 OK`

```json
{
  "files": [
    "src/lib.rs",
    "src/date.rs",
    "time-macros/src/lib.rs",
    "time-macros/src/format_description/parse.rs"
  ],
  "total": 24
}
```

Only `.rs` files are returned.

---

## Error responses

All errors follow the same shape:

```json
{
  "detail": "Session not found"
}
```

| HTTP code | Meaning |
|-----------|---------|
| `400` | Bad request (validation error) |
| `404` | Resource not found |
| `422` | Unprocessable entity (Pydantic validation) |
| `500` | Internal server error |
