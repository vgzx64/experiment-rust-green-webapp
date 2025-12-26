# Rust-Green Backend Implementation Checklist

## Component-Based Task Breakdown

### 1. API Gateway (FastAPI Foundation)
- [ ] Set up FastAPI application structure
- [ ] Configure SQLite database with SQLAlchemy
- [ ] Implement CORS middleware
- [ ] Create request/response schemas (Pydantic)
- [ ] Set up logging and error handling

### 2. SessionService
- [ ] Create Session model (UUID, status, timestamps)
- [ ] Implement session creation endpoint (POST /api/v1/sessions)
- [ ] Implement session retrieval endpoints (GET /api/v1/sessions/{id}, GET /api/v1/sessions/{id}/status)
- [ ] Integrate with message queue for job enqueuing
- [ ] Implement session status tracking

### 3. Message Queue System
- [ ] Implement `asyncio.Queue` for job processing
- [ ] Create background worker that consumes from queue
- [ ] Implement job enqueuing in SessionService
- [ ] Handle worker lifecycle (startup/shutdown)

### 4. CodeExtractionService
- [ ] Create service interface for code extraction
- [ ] Implement basic Rust code parsing (extract code blocks)
- [ ] Integrate with analysis pipeline
- [ ] Store extracted blocks in database

### 5. UnsafeBlockDetectionService
- [ ] Create service interface for unsafe detection
- [ ] Implement simple pattern matching for `unsafe` keyword
- [ ] Extract unsafe blocks with line numbers
- [ ] Generate structured block data

### 6. ClassificationService
- [ ] Create service interface for classification
- [ ] Implement basic risk classification (memory_safety, concurrency, etc.)
- [ ] Assign risk levels (low, medium, high)
- [ ] Store classification results

### 7. Suggestion Services
- [ ] **LLMBasedSuggestionService**: Create stub returning empty list
- [ ] **RuleBasedSuggestionService**: Implement simple pattern-based suggestions
- [ ] Create suggestion aggregation logic
- [ ] Store suggestions with code blocks

### 8. Pipeline Orchestrator
- [ ] Create orchestrator that runs services sequentially
- [ ] Implement error handling between services
- [ ] Connect pipeline to message queue worker
- [ ] Update session status through pipeline stages

### 9. Testing & Documentation
- [ ] Write unit tests for each service
- [ ] Create integration tests for API endpoints
- [ ] Generate OpenAPI documentation
- [ ] Create README with setup instructions

## Implementation Order
1. API Gateway + SessionService (foundation)
2. Message Queue + Worker (async infrastructure)
3. Pipeline services (CodeExtraction → UnsafeDetection → Classification → Suggestions)
4. Integration and testing

## Key Requirements
- Use SQLite (not PostgreSQL) for database
- Use `asyncio.Queue` for message queue (no Redis dependency)
- AI/ML services as stubs only for pre-MVP
- No authentication system for pre-MVP
- Remove "confidence" concept from suggestions
- Rename "unsafe_blocks" to "code_blocks" in API responses
- Focus on core workflow: code submission → analysis → recommendations

## API Endpoints
1. **POST /api/v1/sessions** - Submit code for analysis
2. **GET /api/v1/sessions/{session_id}** - Get analysis results
3. **GET /api/v1/sessions/{session_id}/status** - Quick status check

## Component Architecture
```
API Gateway (FastAPI)
    ↓ (HTTP Request)
SessionService (creates session, enqueues job)
    ↓ (to asyncio.Queue)
AnalysisWorker (consumes from queue)
    ↓
Sequential Pipeline:
    1. CodeExtractionService
    2. UnsafeBlockDetectionService  
    3. ClassificationService
    4. SuggestionServices (LLM stub + Rule-based)
    ↓
Store results in database
    ↓
Update session status
