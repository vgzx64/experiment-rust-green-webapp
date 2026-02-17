"""Shared test fixtures and configuration.

To run with REAL LLM API:
  export LLM_ENABLED=true
  export LLM_API_KEY=your-key
  export LLM_BASE_URL=https://api.deepseek.com/v1
  python -m pytest tests/ -v

Default: Uses mock LLM (no API calls, no cost)
"""
import asyncio
import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient, ASGITransport

# Set testing environment variables before imports
# Override with real values if LLM_ENABLED=true
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("LLM_API_KEY", "test-api-key")
os.environ.setdefault("LLM_BASE_URL", "https://api.deepseek.com/v1")
# Default: disabled (mock mode) - set LLM_ENABLED=true to use real API
os.environ.setdefault("LLM_ENABLED", "false")


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_db_engine():
    """Create test database engine."""
    from app.database import Base
    
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def test_db(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session_maker = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""
    from app.main import app
    
    # Import and override get_db dependency
    from app.database import get_db
    from app.api.v1.sessions import router
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def sample_rust_code() -> str:
    """Sample vulnerable Rust code for testing."""
    return """
fn unsafe_read(path: &str) -> String {
    let mut content = String::new();
    let file = std::fs::File::open(path).unwrap();
    file.read_to_string(&mut content).unwrap();
    content
}
"""


@pytest.fixture
def sample_safe_rust_code() -> str:
    """Sample safe Rust code for testing."""
    return """
fn safe_read(path: &str) -> Result<String, std::io::Error> {
    std::fs::read_to_string(path)
}
"""


@pytest.fixture
def mock_llm_response() -> dict:
    """Mock LLM vulnerability analysis response."""
    return {
        "vulnerability_type": "CWE-252: Unchecked Return Value",
        "cwe_id": "CWE-252",
        "owasp_category": "A9: Using Components with Known Vulnerabilities",
        "risk_level": "high",
        "confidence_score": 0.95,
        "vulnerability_description": "The code uses unwrap() which can panic if the operation fails",
        "exploitation_scenario": "An attacker could cause denial of service by providing invalid input",
        "line_numbers": [1, 6]
    }


@pytest.fixture
def mock_remediation_response() -> dict:
    """Mock LLM remediation response."""
    return {
        "fixed_code": """fn safe_read(path: &str) -> Result<String, std::io::Error> {
    std::fs::read_to_string(path)
}""",
        "explanation": "Use Result type instead of unwrap() to handle errors gracefully",
        "compatibility_notes": "This is a breaking change as the function now returns a Result"
    }


# ==================== Additional Fixtures ====================

@pytest.fixture
def mock_session():
    """Create a mock Session object for testing."""
    from app.models.session import Session, SessionStatus
    session = Session()
    session.id = "test-session-id"
    session.orig_location = "https://github.com/user/repo"
    session.git_ref = "main"
    session.status = SessionStatus.COMPLETED
    session.progress = 100
    session.error_message = None
    return session


@pytest.fixture
def mock_code_block():
    """Create a mock CodeBlock object for testing."""
    from app.models.code_block import CodeBlock
    block = CodeBlock()
    block.id = "test-block-id"
    block.raw_code = "unsafe { *ptr }"
    block.line_start = 10
    block.line_end = 12
    block.file_path = "src/main.rs"
    return block


@pytest.fixture
def mock_analysis(mock_code_block):
    """Create a mock Analysis object for testing."""
    from app.models.analysis import Analysis, CodeBlockType, RiskLevel
    analysis = Analysis()
    analysis.id = "test-analysis-id"
    analysis.session_id = "test-session-id"
    analysis.code_block_id = "test-block-id"
    analysis.code_block_type = CodeBlockType.REPLACEABLE
    analysis.suggested_replacement = "safe_deref(ptr)"
    analysis.cwe_id = "CWE-787"
    analysis.owasp_category = "A1: Injection"
    analysis.risk_level = RiskLevel.HIGH
    analysis.confidence_score = 0.95
    analysis.vulnerability_description = "Buffer overflow vulnerability"
    analysis.exploitation_scenario = "Attacker can overwrite memory"
    analysis.remediation_explanation = "Use safe bounds checking"
    analysis.code_block = mock_code_block
    return analysis


@pytest.fixture
def sample_buffer_overflow_code() -> str:
    """Sample buffer overflow vulnerable code."""
    return """
fn vulnerable_copy(data: &[u8]) -> Vec<u8> {
    let mut buffer = [0u8; 10];
    unsafe {
        std::ptr::copy_nonoverlapping(data.as_ptr(), buffer.as_mut_ptr(), data.len());
    }
    buffer.to_vec()
}
"""


@pytest.fixture
def sample_sql_injection_code() -> str:
    """Sample SQL injection vulnerable code (conceptual for Rust)."""
    return """
fn query_user(conn: &mut sqlite::Connection, user_id: &str) -> Result<User, Error> {
    let query = format!("SELECT * FROM users WHERE id = {}", user_id);
    conn.execute(query)
}
"""


@pytest.fixture
def sample_unsafe_code() -> str:
    """Sample code with unsafe block."""
    return """
fn unsafe_deref(ptr: *const i32) -> i32 {
    unsafe { *ptr }
}
"""


@pytest.fixture
def original_files_sample() -> dict:
    """Sample original files for patch generator tests."""
    return {
        "src/main.rs": """fn main() {
    let ptr: *const i32 = &42;
    unsafe { *ptr }
    println!("Done");
}""",
        "src/lib.rs": "pub fn helper() {}",
        "src/utils.rs": "pub fn utility() {}"
    }
