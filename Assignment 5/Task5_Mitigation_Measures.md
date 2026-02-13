# Task 5: Mitigation Measures - Rust Code Safety Analyzer

## 5.1 Mitigation Strategy Overview

This document provides comprehensive mitigation measures for the 16 threats identified in the Threat Dragon model and evaluated with CVSS v3.1 in Task 4. The mitigations follow a defense-in-depth approach with prioritization based on CVSS scores.

### Mitigation Principles
1. **Prevention First**: Stop attacks before they occur
2. **Detection & Response**: Identify and contain successful attacks
3. **Recovery & Resilience**: Restore operations after incidents
4. **Continuous Improvement**: Learn from incidents and adapt defenses

### Implementation Priority Levels
- **P0 (Critical)**: Immediate implementation required (SQL injection)
- **P1 (High)**: Short-term implementation (1-2 weeks)
- **P2 (Medium)**: Medium-term implementation (1-2 months)
- **P3 (Low)**: Long-term consideration (3+ months)

## 5.2 Comprehensive Mitigation Table

| Threat ID | Threat Title | CVSS Score | Mitigation Category | Specific Controls | Implementation Priority | Implementation Complexity | Expected Effectiveness |
|-----------|--------------|------------|---------------------|-------------------|------------------------|--------------------------|------------------------|
| 1 | Phishing endpoints | 6.1 | Authentication & Network Security | 1. Implement API key authentication<br>2. Use HTTPS with valid certificates<br>3. Implement request signing<br>4. DNS security (DNSSEC, DANE) | P2 | Medium | High (90%) |
| 2 | MitM (API response manipulation) | 7.5 | Encryption & Integrity | 1. Enforce TLS 1.3 for all external API calls<br>2. Implement certificate pinning<br>3. Add response integrity checks (HMAC)<br>4. Use mutual TLS authentication | P1 | High | High (95%) |
| 3 | Code leaks | 8.6 | Data Protection & Privacy | 1. Implement code encryption before sending to LLM API<br>2. Add data masking for sensitive patterns<br>3. Implement data retention policies<br>4. Use secure data deletion | P1 | Medium | High (85%) |
| 4 | API outages | 7.8 | Resilience & Dependency Management | 1. Implement circuit breaker pattern<br>2. Add request queuing with exponential backoff<br>3. Implement fallback analysis mode<br>4. Monitor API quotas and costs | P2 | Medium | Medium (75%) |
| 5 | API key leak | 8.6 | Secrets Management | 1. Use environment variables or secret manager<br>2. Implement key rotation (automated)<br>3. Add usage monitoring and alerts<br>4. Restrict API key permissions | P1 | Low | High (90%) |
| 6 | Malicious prompt injection (no accountability) | 5.0 | Authentication & Auditing | 1. Implement user registration/login<br>2. Add request signing with timestamps<br>3. Implement comprehensive audit logging<br>4. Add user reputation scoring | P3 | High | Medium (70%) |
| 7 | Malicious prompt injection (excessive requests) | 3.6 | Rate Limiting & Resource Management | 1. Implement IP-based rate limiting<br>2. Add user-based quotas<br>3. Implement request prioritization<br>4. Add CAPTCHA for high-volume users | P3 | Low | High (80%) |
| 8 | API endpoint impersonation | 6.1 | Authentication & Authorization | 1. Implement API key authentication<br>2. Add request validation middleware<br>3. Use JWT tokens with expiration<br>4. Implement CORS restrictions | P2 | Medium | High (85%) |
| 9 | Lack of request logging | 6.1 | Monitoring & Auditing | 1. Implement structured logging (JSON)<br>2. Add audit trail for all API calls<br>3. Implement log aggregation and retention<br>4. Add real-time monitoring dashboard | P2 | Medium | High (90%) |
| 10 | Log leaks (error messages with stack traces) | 8.6 | Error Handling & Information Security | 1. Implement custom error handlers<br>2. Separate development and production error messages<br>3. Add error message sanitization<br>4. Implement error logging without sensitive data | P1 | Low | High (95%) |
| 11 | DDOS (unauthenticated endpoint flooding) | 8.6 | Network Security & Rate Limiting | 1. Implement Web Application Firewall (WAF)<br>2. Add DDoS protection service (Cloudflare)<br>3. Implement request rate limiting<br>4. Add connection pooling limits | P1 | Medium | High (90%) |
| 12 | Code analysis result manipulation | 7.8 | Data Integrity & Validation | 1. Implement input validation and sanitization<br>2. Add checksums for analysis results<br>3. Implement result signing<br>4. Add tamper detection mechanisms | P2 | High | Medium (80%) |
| 13 | Direct database manipulation | 7.2 | Database Security & Access Control | 1. Implement database encryption at rest<br>2. Add file system permissions (read-only for app)<br>3. Use database auditing features<br>4. Implement regular backup and integrity checks | P2 | Medium | High (85%) |
| 14 | Unencrypted sensitive data | 6.3 | Data Protection & Encryption | 1. Implement database encryption (SQLCipher)<br>2. Add field-level encryption for sensitive data<br>3. Implement key management system<br>4. Add data classification and handling policies | P2 | High | High (90%) |
| 15 | SQL injection attacks | 9.8 | Input Validation & Database Security | 1. Use SQLAlchemy parameterized queries exclusively<br>2. Implement input validation middleware<br>3. Add SQL injection detection (WAF rules)<br>4. Implement least privilege database users | P0 | Low | High (99%) |
| 16 | Unauthorized file access | 6.3 | File System Security & Access Control | 1. Implement secure file path handling<br>2. Add file permission controls (chmod)<br>3. Use UUIDs for file names<br>4. Implement file access logging | P2 | Low | High (85%) |

## 5.3 Detailed Mitigation Implementation Guidance

### Critical Threat: SQL Injection Attacks (Threat 15)

#### Immediate Actions (P0)
1. **Parameterized Queries Enforcement**
   ```python
   # Current vulnerable pattern (DO NOT USE):
   # query = f"SELECT * FROM sessions WHERE id = '{user_input}'"
   
   # Secure pattern with SQLAlchemy:
   from sqlalchemy import text
   safe_query = text("SELECT * FROM sessions WHERE id = :session_id")
   result = await db.execute(safe_query, {"session_id": user_input})
   ```

2. **Input Validation Middleware**
   ```python
   # Add to FastAPI middleware stack
   from fastapi import Request
   import re
   
   async def sql_injection_middleware(request: Request, call_next):
       # Check for SQL injection patterns in query params and body
       sql_patterns = [r"(\%27)|(\')|(\-\-)|(\%23)|(#)", r"((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))"]
       
       # Check query parameters
       for param in request.query_params.values():
           for pattern in sql_patterns:
               if re.search(pattern, param, re.IGNORECASE):
                   raise HTTPException(status_code=400, detail="Invalid input detected")
       
       # Check JSON body for POST requests
       if request.method == "POST":
           body = await request.body()
           body_str = body.decode('utf-8')
           for pattern in sql_patterns:
               if re.search(pattern, body_str, re.IGNORECASE):
                   raise HTTPException(status_code=400, detail="Invalid input detected")
       
       return await call_next(request)
   ```

3. **Database User Privilege Reduction**
   ```sql
   -- Create limited privilege user for application
   CREATE USER 'rust_green_app'@'localhost' IDENTIFIED BY 'strong_password';
   GRANT SELECT, INSERT, UPDATE ON rust_green.sessions TO 'rust_green_app'@'localhost';
   GRANT SELECT, INSERT ON rust_green.analyses TO 'rust_green_app'@'localhost';
   GRANT SELECT, INSERT ON rust_green.code_blocks TO 'rust_green_app'@'localhost';
   -- NO DROP, DELETE, or ALTER privileges
   ```

### High Priority: API Key Leak (Threat 5)

#### Short-term Implementation (P1)
1. **Environment Variable Configuration**
   ```python
   # backend/app/config/llm_config.py - Updated
   import os
   from dotenv import load_dotenv
   
   load_dotenv()
   
   class LLMConfig:
       api_key: str = os.getenv("DEEPSEEK_API_KEY")
       
       @classmethod
       def validate_key(cls):
           if not cls.api_key or cls.api_key == "your_api_key_here":
               raise ValueError("API key not configured. Set DEEPSEEK_API_KEY environment variable.")
   ```

2. **Key Rotation Automation**
   ```python
   # Key rotation service
   import asyncio
   from datetime import datetime, timedelta
   
   class KeyRotationService:
       def __init__(self):
           self.key_age_days = 30
           self.last_rotation = datetime.now()
           
       async def rotate_if_needed(self):
           if datetime.now() - self.last_rotation > timedelta(days=self.key_age_days):
               await self.rotate_key()
               
       async def rotate_key(self):
           # Call key management service or admin API
           new_key = await self.generate_new_key()
           os.environ["DEEPSEEK_API_KEY"] = new_key
           self.last_rotation = datetime.now()
           print(f"API key rotated at {self.last_rotation}")
   ```

3. **Usage Monitoring**
   ```python
   # API usage monitoring decorator
   import functools
   from collections import defaultdict
   
   class APIMonitor:
       def __init__(self):
           self.usage = defaultdict(int)
           self.alerts_sent = set()
           
       def monitor(self, func):
           @functools.wraps(func)
           async def wrapper(*args, **kwargs):
               api_key = kwargs.get('api_key') or args[0]
               self.usage[api_key] += 1
               
               # Alert on unusual usage
               if self.usage[api_key] > 1000 and api_key not in self.alerts_sent:
                   await self.send_alert(api_key, self.usage[api_key])
                   self.alerts_sent.add(api_key)
                   
               return await func(*args, **kwargs)
           return wrapper
   ```

### High Priority: Code Leaks (Threat 3)

#### Data Protection Implementation
1. **Code Encryption Before LLM Submission**
   ```python
   from cryptography.fernet import Fernet
   import base64
   
   class CodeEncryptionService:
       def __init__(self):
           # Store key in environment variable
           key = os.getenv("CODE_ENCRYPTION_KEY")
           if not key:
               key = Fernet.generate_key()
               os.environ["CODE_ENCRYPTION_KEY"] = key.decode()
           self.cipher = Fernet(key)
           
       def encrypt_code(self, code: str) -> str:
           """Encrypt code before sending to external API."""
           encrypted = self.cipher.encrypt(code.encode())
           return base64.b64encode(encrypted).decode()
           
       def decrypt_code(self, encrypted_code: str) -> str:
           """Decrypt code after receiving from external API."""
           encrypted = base64.b64decode(encrypted_code.encode())
           return self.cipher.decrypt(encrypted).decode()
   ```

2. **Data Masking for Sensitive Patterns**
   ```python
   import re
   
   class DataMaskingService:
       def mask_sensitive_patterns(self, code: str) -> str:
           """Mask potential secrets in code before analysis."""
           patterns = [
               (r'API_KEY\s*=\s*["\'][^"\']+["\']', 'API_KEY = "***MASKED***"'),
               (r'password\s*=\s*["\'][^"\']+["\']', 'password = "***MASKED***"'),
               (r'secret\s*=\s*["\'][^"\']+["\']', 'secret = "***MASKED***"'),
               (r'key\s*=\s*["\'][^"\']+["\']', 'key = "***MASKED***"'),
           ]
           
           masked_code = code
           for pattern, replacement in patterns:
               masked_code = re.sub(pattern, replacement, masked_code, flags=re.IGNORECASE)
               
           return masked_code
   ```

### High Priority: DDOS Protection (Threat 11)

#### Rate Limiting Implementation
1. **FastAPI Rate Limiting Middleware**
   ```python
   from slowapi import Limiter, _rate_limit_exceeded_handler
   from slowapi.util import get_remote_address
   from slowapi.errors import RateLimitExceeded
   
   limiter = Limiter(key_func=get_remote_address)
   
   # Apply to FastAPI app
   app.state.limiter = limiter
   app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
   
   # Apply rate limits to endpoints
   @router.post("/sessions")
   @limiter.limit("10/minute")  # 10 requests per minute per IP
   async def create_session(session_data: CreateSessionInput, db: AsyncSession = Depends(get_db)):
       # Existing implementation
   ```

2. **Connection Pool Management**
   ```python
   # backend/app/database.py - Updated
   from sqlalchemy.pool import QueuePool
   
   engine = create_async_engine(
       DATABASE_URL,
       poolclass=QueuePool,
       pool_size=10,  # Maximum connections
       max_overflow=5,  # Additional connections allowed
       pool_timeout=30,  # Seconds to wait for connection
       pool_recycle=3600,  # Recycle connections after 1 hour
   )
   ```

## 5.4 Implementation Roadmap

### Phase 1: Critical & High Priority (Weeks 1-2)
1. **SQL Injection Prevention** (P0)
   - Implement parameterized queries
   - Add input validation middleware
   - Reduce database privileges

2. **Secrets Management** (P1)
   - Move API keys to environment variables
   - Implement key rotation
   - Add usage monitoring

3. **Error Handling** (P1)
   - Implement custom error handlers
   - Sanitize error messages
   - Separate dev/prod error reporting

### Phase 2: Medium Priority (Weeks 3-6)
1. **Authentication & Authorization** (P2)
   - Implement API key authentication
   - Add request logging
   - Implement CORS restrictions

2. **Data Protection** (P2)
   - Implement code encryption
   - Add database encryption
   - Implement file system security

3. **Monitoring & Auditing** (P2)
   - Implement structured logging
   - Add audit trail
   - Create monitoring dashboard

### Phase 3: Low Priority & Resilience (Months 2-3)
1. **Rate Limiting & DDOS** (P3)
   - Implement comprehensive rate limiting
   - Add WAF integration
   - Implement circuit breakers

2. **Resilience Improvements** (P3)
   - Add fallback mechanisms
   - Implement backup systems
   - Add disaster recovery procedures

## 5.5 AI-Assisted Mitigation Design Process

### AI Contributions
1. **Initial Mitigation Ideas**: AI generated baseline mitigation strategies for each STRIDE category
2. **Industry Best Practices**: AI suggested standard security controls for web applications
3. **Implementation Examples**: AI provided code snippets for common security patterns
4. **Risk-Based Prioritization**: AI helped prioritize based on CVSS scores and impact

### Manual Refinements
1. **System-Specific Tailoring**: Adapted generic mitigations to Rust Code Safety Analyzer architecture
2. **Complexity Assessment**: Evaluated implementation feasibility within current codebase
3. **Research Context Consideration**: Adjusted mitigations for academic/research environment
4. **Integration Planning**: Mapped mitigations to existing code files and components
5. **Effectiveness Validation**: Cross-checked mitigations against threat root causes

### Key Manual Adjustments
1. **Simplified Authentication**: Reduced complexity for research system while maintaining security
2. **Practical Encryption**: Balanced security with performance for code analysis system
3. **Gradual Implementation**: Created phased roadmap considering resource constraints
4. **Monitoring Emphasis**: Enhanced logging and monitoring for research integrity

## 5.6 Effectiveness Metrics

### Quantitative Measures
1. **SQL Injection Prevention**: 99% effectiveness with parameterized queries
2. **Data Leakage Reduction**: 85-95% reduction with encryption and masking
3. **DDOS Resilience**: 90% attack mitigation with rate limiting and WAF
4. **Audit Coverage**: 90%+ of security-relevant events logged

### Qualitative Improvements
1. **Defense-in-Depth**: Multiple layers of security controls
2. **Proactive Detection**: Early warning systems for suspicious activities
3. **Incident Response**: Clear procedures for security incidents
4. **Continuous Monitoring**: Ongoing security posture assessment

## 5.7 Next Steps for Task 6

This mitigation plan provides the foundation for the final report in Task 6, which will integrate:
1. System definition and DFD from Tasks 1-2
2. STRIDE threat analysis from Task 3
3. CVSS risk evaluation from Task 4
4. Mitigation measures from this Task 5
5. AI usage documentation and conclusions

The prioritized implementation roadmap enables systematic security improvement while maintaining research system functionality.