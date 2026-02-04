# Task 2: Data Flow Diagrams (DFD) - Rust Code Safety Analyzer

## 2.1 DFD Level 0 - Context Diagram

The context diagram shows the system boundaries and interactions with external entities.

```mermaid
title DFD Level 0 - Rust Code Safety Analyzer Context Diagram

User->Rust_Code_Safety_Analyzer:Submit Rust code for analysis
User<--Rust_Code_Safety_Analyzer:Receive analysis results
Rust_Code_Safety_Analyzer->Deepseek_LLM_API:Send code for vulnerability analysis
Rust_Code_Safety_Analyzer<--Deepseek_LLM_API:Receive vulnerability assessment
note over Rust_Code_Safety_Analyzer:External Entities:\n- User (Rust Developer)\n- Deepseek LLM API
```

**Diagram Description:**
- **External Entity 1**: User (Rust Developer) - Submits code and receives results
- **External Entity 2**: Deepseek LLM API - Provides AI-powered vulnerability analysis
- **System Boundary**: Rust Code Safety Analyzer (complete application)
- **Data Flows**: 
  - Code submission → System
  - Analysis results → User
  - Code analysis request → LLM API
  - Vulnerability assessment → System

## 2.2 DFD Level 1 - Detailed Diagram

The Level 1 DFD decomposes the main system into key processes and data stores.

```mermaid
title DFD Level 1 - Rust Code Safety Analyzer Detailed Diagram

User->Web_Interface:1. Submit Rust code\n(via form/editor)
Web_Interface->API_Gateway:2. HTTP POST /api/v1/sessions\n{code: "rust_code"}
API_Gateway->Session_Manager:3. Create session record\nstore in database
Session_Manager->Session_DB:4. Store session metadata\n(id, status, timestamps)
API_Gateway<--Session_Manager:5. Return session ID\nand initial status
Web_Interface<--API_Gateway:6. Return session details\nfor progress tracking
API_Gateway->Analysis_Queue:7. Enqueue session ID\nfor processing
Analysis_Worker->Analysis_Queue:8. Dequeue next session ID\nfor processing
Analysis_Worker->File_Storage:9. Retrieve uploaded code\nfrom file system
Analysis_Worker->LLM_Service:10. Send code for\nvulnerability analysis
LLM_Service->Deepseek_API:11. API call with code\nand analysis prompts
Deepseek_API<--LLM_Service:12. Receive JSON response\nwith vulnerability findings
Analysis_Worker<--LLM_Service:13. Processed analysis results\nwith CWE/OWASP classifications
Analysis_Worker->Analysis_DB:14. Store analysis results\n(vulnerabilities, fixes)
Analysis_Worker->Session_Manager:15. Update session status\nto COMPLETED
Session_Manager->Session_DB:16. Update session progress\nand completion timestamp
User->Web_Interface:17. Poll for results\n(GET /api/v1/sessions/{id})
Web_Interface->API_Gateway:18. Request session details\nand analysis results
API_Gateway->Session_Manager:19. Retrieve session data\nfrom database
Session_Manager->Session_DB:20. Query session metadata\nand status
Session_Manager->Analysis_DB:21. Retrieve analysis results\nfor this session
API_Gateway<--Session_Manager:22. Return complete session data\nwith analysis findings
Web_Interface<--API_Gateway:23. Return formatted results\nfor display
User<--Web_Interface:24. Display analysis results\nwith vulnerabilities and fixes

note over Web_Interface,API_Gateway:Processes:\n1. Web Interface\n2. API Gateway\n3. Session Manager\n4. Analysis Worker\n5. LLM Service
note over Session_DB,Analysis_DB:Data Stores:\n- Session Database\n- Analysis Database\n- File Storage
note over Deepseek_API:External Entity:\n- Deepseek LLM API
```

## 2.3 DFD Components Description

### External Entities
1. **User** (Rust Developer)
   - Submits Rust code for analysis via web interface
   - Receives vulnerability reports and safe code alternatives
   - Monitors analysis progress in real-time

2. **Deepseek LLM API**
   - External AI service for code vulnerability analysis
   - Receives code snippets and analysis prompts
   - Returns structured vulnerability assessments

### System Processes
1. **Web Interface** (Frontend Application)
   - Provides user interface for code submission
   - Displays analysis results and progress
   - Handles user interactions and real-time updates

2. **API Gateway** (FastAPI Backend)
   - RESTful endpoint handler for all API requests
   - Input validation and request routing
   - Response formatting and error handling

3. **Session Manager**
   - Creates and manages analysis sessions
   - Updates session status and progress
   - Coordinates between different system components

4. **Analysis Worker**
   - Processes analysis jobs from queue
   - Coordinates LLM analysis pipeline
   - Stores results in database
   - Updates session completion status

5. **LLM Service**
   - Interfaces with Deepseek API
   - Formats prompts and parses responses
   - Handles API errors and retries

### Data Stores
1. **Session Database** (SQLite)
   - Stores session metadata (ID, status, timestamps)
   - Tracks analysis progress (0-100%)
   - Maintains error messages for failed sessions

2. **Analysis Database** (SQLite)
   - Stores vulnerability findings and classifications
   - Contains safe code alternatives and explanations
   - Records confidence scores and risk levels

3. **File Storage** (Local Filesystem)
   - Stores uploaded Rust code files
   - Maintains temporary code artifacts
   - Provides code retrieval for analysis

### Data Flows
1. **Code Submission Flow**
   - User → Web Interface → API Gateway → Session Manager → Session DB
   - Creates new session with PENDING status

2. **Analysis Processing Flow**
   - Analysis Queue → Analysis Worker → File Storage → LLM Service → Deepseek API
   - Processes code through AI analysis pipeline

3. **Results Storage Flow**
   - LLM Service → Analysis Worker → Analysis DB → Session Manager → Session DB
   - Stores findings and updates session completion

4. **Results Retrieval Flow**
   - User → Web Interface → API Gateway → Session Manager → Session DB/Analysis DB
   - Retrieves and displays analysis results

## 2.4 Data Dictionary

### Data Elements
1. **Rust Code**
   - Type: Text/File
   - Format: Rust source code (.rs files or plain text)
   - Size: Up to 10,000 characters
   - Sensitivity: High (potential intellectual property)

2. **Session Metadata**
   - ID: UUID string
   - Status: Enum (PENDING, PROCESSING, COMPLETED, FAILED)
   - Progress: Integer (0-100%)
   - Timestamps: created_at, updated_at, completed_at
   - Error Message: Text (nullable)

3. **Analysis Results**
   - Vulnerability Type: Text description
   - CWE ID: String (e.g., "CWE-787")
   - OWASP Category: String (e.g., "A1: Injection")
   - Risk Level: Enum (LOW, MEDIUM, HIGH, CRITICAL)
   - Confidence Score: Float (0.0-1.0)
   - Safe Code Alternative: Rust code text
   - Line Numbers: Array [start, end]

4. **LLM API Requests/Responses**
   - Request: JSON with code and analysis prompts
   - Response: JSON with structured vulnerability analysis
   - Metadata: Token usage, model information

## 2.5 Trust Boundaries

### Boundary 1: External ↔ System
- Between User and Web Interface (untrusted ↔ trusted)
- Between Deepseek API and LLM Service (external ↔ internal)

### Boundary 2: Frontend ↔ Backend
- Between Web Interface and API Gateway (client ↔ server)
- Cross-origin requests with CORS configuration

### Boundary 3: Application ↔ Data Stores
- Between Processes and Databases (application ↔ persistence)
- Between Analysis Worker and File Storage (processing ↔ storage)

## 2.6 Assumptions and Constraints

### Diagram Assumptions
1. All communication is synchronous unless specified
2. Error handling flows are omitted for clarity
3. Authentication/authorization is not implemented (per system definition)
4. Network protocols: HTTP for web, internal calls for processes

### System Constraints
1. Single analysis worker limits parallel processing
2. LLM API dependency may introduce latency
3. File storage is local filesystem (no cloud storage)
4. Database is SQLite (single-file, no replication)

---

*These DFDs provide visual representation of data flows through the Rust Code Safety Analyzer system, identifying external entities, processes, data stores, and trust boundaries for subsequent STRIDE analysis.*