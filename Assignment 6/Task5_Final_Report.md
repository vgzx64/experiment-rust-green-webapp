# AI Secure Refactoring Agent - Final Report

## Assignment 6: Development of an AI Agent for Advanced Software Engineering Tasks

---

## 1. Selected Topic and Problem Formulation

### 1.1 Topic Selection
**Topic B: AI Secure Refactoring Agent**

This project implements an AI-powered agent that detects security vulnerabilities in Rust code, proposes remediation fixes, and generates unified diffs showing the changes between vulnerable and safe code.

### 1.2 Problem Statement
Manual security code review is time-consuming and error-prone. This project addresses the challenge of automatically:
1. Detecting security vulnerabilities in Rust code using OWASP/CWE classifications
2. Generating safe remediation code
3. Presenting clear diffs between original and fixed code for human review

### 1.3 Motivation
Rust memory safety features make it a popular choice for systems programming, but developers can still introduce vulnerabilities through unsafe blocks, improper error handling, and other patterns. An AI agent can assist developers by:
- Reducing time spent on routine security reviews
- Providing consistent vulnerability detection
- Generating remediation suggestions that follow best practices

---

## 2. Justification of Chosen Framework and Toolset

### 2.1 Backend Framework: FastAPI
**Reason for selection:**
- Native async support for handling multiple concurrent analysis requests
- Built-in validation with Pydantic models
- Automatic OpenAPI documentation
- Easy integration with SQLAlchemy ORM

### 2.2 AI Integration: Deepseek LLM
**Reason for selection:**
- Cost-effective compared to GPT-4
- Strong code understanding capabilities
- OpenAI-compatible API for easy integration
- JSON response format support for structured outputs

### 2.3 Database: SQLite with SQLAlchemy
**Reason for selection:**
- Simple setup with aiosqlite for async operations
- No external database server required
- Sufficient for prototype/demo purposes

### 2.4 Frontend: Vanilla JavaScript
**Reason for selection:**
- Lightweight - no build step required
- Easy to understand and modify
- Fast loading times

---

## 3. Detailed Agent Architecture

### 3.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Frontend (Browser)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐   │
│  │ index.html  │  │session.html │  │  session-detail.html   │   │
│  │ (analyze)  │  │ (list)      │  │  (view results + diff)│   │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘   │
└──────────┼─────────────────┼──────────────────────┼────────────────┘
           │                 │                      │
           ▼                 ▼                      ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                   REST API (FastAPI)                       │
    │  ┌─────────────────────────────────────────────────────┐  │
    │  │  POST /sessions     - Create analysis session       │  │
    │  │  GET  /sessions    - List all sessions            │  │
    │  │  GET  /sessions/id - Get session with analysis    │  │
    │  │  GET  /sessions/id/status - Poll status           │  │
    │  └─────────────────────────────────────────────────────┘  │
    └────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                   Core Services                            │
    │  ┌────────────────┐  ┌────────────────┐  ┌───────────┐  │
    │  │ LLM Service    │  │ Diff Generator │  │ File      │  │
    │  │ (Deepseek API)│  │ (unified diff)│  │ Storage   │  │
    │  └───────┬────────┘  └───────┬────────┘  └───────────┘  │
    │          │                    │                              │
    │          ▼                    │                              │
    │  ┌─────────────────────────────┴───────────────────────┐  │
    │  │            Analysis Worker (Async Queue)            │  │
    │  │  - Analyze vulnerability → Generate remediation      │  │
    │  │  - Generate diff → Save to database                 │  │
    │  └───────────────────────────────────────────────────────┘  │
    └────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                   Database (SQLite)                       │
    │  ┌─────────┐  ┌────────────┐  ┌──────────────────────┐  │
    │  │Session  │  │ CodeBlock  │  │ Analysis             │  │
    │  │(status) │  │(raw code)  │  │(vulnerability+diff) │  │
    │  └─────────┘  └────────────┘  └──────────────────────┘  │
    └─────────────────────────────────────────────────────────────┘
```

### 3.2 Agent Components

#### LLM Service (`llm_service.py`)
- **analyze_vulnerability()**: Sends code to LLM, receives vulnerability analysis
- **generate_remediation()**: Generates safe alternative code
- **complete_analysis_pipeline()**: Orchestrates analysis + remediation

#### Diff Generator (`diff_generator.py`)
- **generate_unified_diff()**: Creates git-style unified diff
- **generate_diff_stats()**: Counts lines added/removed
- **generate_diff_result()**: Complete result with diff + statistics

### 3.3 Data Flow

1. User submits Rust code via frontend
2. Backend creates session with PENDING status
3. Analysis worker picks up session from queue
4. LLM analyzes code → returns vulnerability details
5. If vulnerability found, LLM generates remediation
6. Diff generator creates unified diff
7. Results saved to database with diff
8. Frontend displays vulnerability + diff for review

---

## 4. Implementation Details and Representative Prompts

### 4.1 LLM System Prompt
```python
"""You are a security expert specializing in Rust code analysis.
Analyze the provided Rust code for security vulnerabilities.
Return your analysis in JSON format with the following structure:
{
    "vulnerability_type": "Description of vulnerability",
    "cwe_id": "CWE-XXX",
    "owasp_category": "A1: Injection",
    "risk_level": "low|medium|high|critical",
    "confidence_score": 0.95,
    "vulnerability_description": "Detailed explanation",
    "exploitation_scenario": "How attackers could exploit",
    "line_numbers": [start_line, end_line]
}
Be specific, technical, and concise in your analysis."""
```

### 4.2 Sample Vulnerability Analysis

**Input Code:**
```rust
fn unsafe_read(path: &str) -> String {
    let mut content = String::new();
    let file = std::fs::File::open(path).unwrap();
    file.read_to_string(&mut content).unwrap();
    content
}
```

**LLM Response:**
```json
{
    "vulnerability_type": "CWE-252: Unchecked Return Value",
    "cwe_id": "CWE-252",
    "owasp_category": "A9: Using Components with Known Vulnerabilities",
    "risk_level": "high",
    "confidence_score": 0.95,
    "vulnerability_description": "The code uses unwrap() which can panic",
    "exploitation_scenario": "Invalid input causes panic/DoS",
    "line_numbers": [1, 6]
}
```

### 4.3 Sample Remediation

**Fixed Code:**
```rust
fn safe_read(path: &str) -> Result<String, std::io::Error> {
    std::fs::read_to_string(path)
}
```

### 4.4 Sample Unified Diff Output
```diff
--- vulnerable_code
+++ remediated_code
@@ -1,6 +1,2 @@
- fn unsafe_read(path: &str) -> String {
-     let mut content = String::new();
-     let file = std::fs::File::open(path).unwrap();
-     file.read_to_string(&mut content).unwrap();
-     content
+ fn safe_read(path: &str) -> Result<String, std::io::Error> {
+     std::fs::read_to_string(path)
 }
```

---

## 5. Testing Methodology and Results

### 5.1 Test Infrastructure

#### Test Files Structure
```
backend/tests/
├── test_diff_generator.py    # 15 tests for diff generation
├── test_llm_service.py     # 20 mock-based tests
├── test_runner.py          # Dynamic test case discovery
├── conftest.py            # Shared fixtures
└── test_cases/
    └── buffer_overflow/
        ├── original.rs     # Vulnerable code
        ├── fixed.rs       # Expected fix
        ├── result_suggestion.rs   # LLM output
        └── result_explanation.txt # LLM explanation
```

### 5.2 Test Categories

#### Unit Tests (No API Cost)
- Diff generation correctness
- JSON response parsing
- Error handling
- Edge cases (empty code, identical code)

#### Integration Tests
- API endpoint functionality
- Database operations
- Async pipeline flow

#### Manual Review Tests
- LLM-generated suggestions saved for human review
- Result files: `result_suggestion.rs`, `result_explanation.txt`

### 5.3 Test Results
```
============================= test session starts ==============================
tests/test_diff_generator.py::TestDiffGenerator::test_generate_unified_diff_with_changes PASSED
tests/test_diff_generator.py::TestDiffGenerator::test_generate_unified_diff_identical_code PASSED
...
============================== 41 passed in 0.10s ==============================
```

### 5.4 Running Tests

```bash
# Default: Mock mode (no API calls)
cd backend && python -m pytest tests/ -v

# With real LLM API
export LLM_ENABLED=true
export LLM_API_KEY=your-key
python -m pytest tests/ -v
```

---

## 6. Analysis of Failures, Risks, and Limitations

### 6.1 Accuracy and Correctness

**Potential Issues:**
- **False Positives**: LLM may flag safe code as vulnerable
- **False Negatives**: May miss subtle vulnerabilities
- **Incorrect Fixes**: Generated code may not compile or maintain functionality

**Mitigation:**
- All LLM outputs require expert human review
- Diff allows easy comparison of changes
- Confidence scores help prioritize review

### 6.2 Consistency and Stability

**Observations:**
- Same code may produce slightly different fixes with different temperature settings
- API responses may vary between calls

**Mitigation:**
- Low temperature (0.0) for deterministic outputs
- Fixed prompts for consistency
- Human review catches inconsistencies

### 6.3 Potential Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| API key exposure | High | Use environment variables, not hardcoded |
| Unexpected costs | Medium | Mock testing, cost tracking |
| Incorrect security advice | High | Always require human review |
| Service availability | Low | Graceful degradation when LLM unavailable |

### 6.4 Ethical Concerns

- **Over-reliance on AI**: Developers may trust AI suggestions without understanding
- **Security theater**: False sense of security from automated tools
- **Bias**: LLM may have training biases affecting recommendations

---

## 7. Conclusions on Applicability of AI Agents in Software Engineering

### 7.1 Benefits

1. **Productivity**: Automates routine security analysis tasks
2. **Consistency**: Applies security rules uniformly
3. **Learning**: Helps developers understand vulnerabilities
4. **Speed**: Analyzes code faster than manual review
5. **Scalability**: Can handle large codebases

### 7.2 Limitations

1. **Not a Replacement**: Human expertise still essential
2. **Context Awareness**: May miss business logic vulnerabilities
3. **False Security**: Automated tools can miss issues
4. **Cost**: Real API calls have monetary cost
5. **Maintenance**: Prompt engineering requires ongoing effort

### 7.3 Recommendations for Production Use

1. **Human-in-the-loop**: All AI suggestions require expert review
2. **Incremental adoption**: Start with non-critical code
3. **Feedback loop**: Track false positives/negatives to improve
4. **Cost controls**: Set API spending limits
5. **Documentation**: Maintain audit trail of AI decisions

### 7.4 Future Improvements

- Fine-tune LLM on security-specific Rust code
- Add compile-time verification of suggested fixes
- Integrate with CI/CD pipelines
- Support for additional languages
- Multi-agent architecture (detector + fixer + verifier)

---

## 8. References

- CWE (Common Weakness Enumeration): https://cwe.mitre.org/
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Rust Security Guidelines: https://rustsec.org/
- FastAPI Documentation: https://fastapi.tiangolo.com/
- Deepseek API: https://platform.deepseek.com/

---

## Appendix: File Structure

```
rust-green-webapp/
├── backend/
│   ├── app/
│   │   ├── api/v1/sessions.py       # REST endpoints
│   │   ├── services/
│   │   │   ├── llm_service.py        # LLM integration
│   │   │   ├── diff_generator.py    # Diff generation
│   │   │   └── pipeline/             # Async worker
│   │   ├── models/                   # SQLAlchemy models
│   │   └── config/                   # Configuration
│   ├── tests/
│   │   ├── test_runner.py            # Dynamic test runner
│   │   ├── test_diff_generator.py   # Unit tests
│   │   └── test_cases/               # Test data
│   └── requirements.txt
├── frontend/
│   ├── index.html                    # Main page
│   ├── script.js                    # Frontend logic
│   └── css/                         # Styles
└── Assignment 6/
    └── Final Report (this document)
```
