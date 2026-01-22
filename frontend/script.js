// rust-green Frontend with Backend Integration
// Using IIFE and Module Pattern to avoid global namespace pollution

(function() {
    'use strict';
    
    // Configuration
    const API_BASE_URL = 'http://localhost:8000/api/v1';
    const POLLING_INTERVAL = 2000; // 2 seconds
    const MAX_POLLING_TIME = 10 * 60 * 1000; // 10 minutes
    
    // Main Application Namespace
    const RustGreenApp = {
        // Current session state
        currentSessionId: null,
        pollingInterval: null,
        pollingStartTime: null,
        
        // Public initialization method
        init: function() {
            console.log('rust-green frontend loaded with backend integration');
            
            // Initialize all components
            this.initInputOptions();
            this.initCodeInput();
            this.initActionButtons();
            this.initFindingActions();
            this.initResponsiveBehavior();
            
            // Set up example interactions
            this.setupExampleInteractions();
            
            // Update live data (simulated)
            this.updateLiveData();
            
            // Set up periodic updates
            setInterval(() => this.updateLiveData(), 30000);
        },
        
        // ==================== Input Options ====================
        initInputOptions: function() {
            const optionButtons = document.querySelectorAll('.option-btn');
            const codeInput = document.getElementById('rust-code');
            
            optionButtons.forEach(button => {
                button.addEventListener('click', () => {
                    // Update active button
                    optionButtons.forEach(btn => btn.classList.remove('active'));
                    button.classList.add('active');
                    
                    // Update input placeholder based on selection
                    const option = button.textContent.toLowerCase();
                    this.updateInputForOption(option, codeInput);
                });
            });
        },
        
        updateInputForOption: function(option, codeInput) {
            const placeholders = {
                'paste': 'Paste your Rust code here...',
                'upload': 'File will be uploaded and displayed here...',
                'git': 'Git repository contents will be displayed here...'
            };
            
            const infoTexts = {
                'paste': '<i class="fas fa-ruler-combined"></i> 8 lines<span><i class="fas fa-exclamation-triangle"></i> 1 unsafe block</span>',
                'upload': '<i class="fas fa-file-upload"></i> No file selected<span><i class="fas fa-info-circle"></i> Upload .rs or .zip</span>',
                'git': '<i class="fab fa-git"></i> Enter Git URL<span><i class="fas fa-branch"></i> Supports GitHub, GitLab</span>'
            };
            
            codeInput.placeholder = placeholders[option] || placeholders.paste;
            
            // Update info display
            const inputInfo = document.querySelector('.input-info');
            if (inputInfo) {
                inputInfo.innerHTML = infoTexts[option] || infoTexts.paste;
            }
            
            // For demo purposes, show a message
            if (option !== 'paste') {
                this.showMessage(`Switched to ${option} mode. In a real implementation, this would handle ${option} functionality.`);
            }
        },
        
        // ==================== Code Input ====================
        initCodeInput: function() {
            const codeInput = document.getElementById('rust-code');
            
            if (!codeInput) return;
            
            // Update line count and unsafe block detection
            codeInput.addEventListener('input', () => {
                this.updateCodeStats(codeInput.value);
            });
            
            // Initial stats update
            this.updateCodeStats(codeInput.value);
        },
        
        updateCodeStats: function(code) {
            const inputInfo = document.querySelector('.input-info');
            if (!inputInfo) return;
            
            const lines = this.countLines(code);
            const unsafeBlocks = this.countUnsafeBlocks(code);
            
            inputInfo.innerHTML = `
                <span><i class="fas fa-ruler-combined"></i> ${lines} lines</span>
                <span><i class="fas fa-exclamation-triangle"></i> ${unsafeBlocks} unsafe block${unsafeBlocks !== 1 ? 's' : ''}</span>
            `;
        },
        
        // ==================== Action Buttons ====================
        initActionButtons: function() {
            const analyzeBtn = document.getElementById('analyze-btn');
            const quickScanBtn = document.getElementById('quick-scan');
            const clearBtn = document.getElementById('clear-btn');
            
            if (analyzeBtn) {
                analyzeBtn.addEventListener('click', () => this.startAnalysis());
            }
            
            if (quickScanBtn) {
                quickScanBtn.addEventListener('click', () => this.performQuickScan());
            }
            
            if (clearBtn) {
                clearBtn.addEventListener('click', () => this.clearCodeInput());
            }
        },
        
        // ==================== API Service Functions ====================
        apiRequest: async function(endpoint, options = {}) {
            const url = `${API_BASE_URL}${endpoint}`;
            const defaultOptions = {
                headers: {
                    'Content-Type': 'application/json',
                },
            };
            
            try {
                const response = await fetch(url, { ...defaultOptions, ...options });
                
                if (!response.ok) {
                    let errorMessage = `API error: ${response.status} ${response.statusText}`;
                    try {
                        const errorData = await response.json();
                        errorMessage = errorData.detail || errorMessage;
                    } catch (e) {
                        // Ignore JSON parsing errors
                    }
                    throw new Error(errorMessage);
                }
                
                return await response.json();
            } catch (error) {
                console.error('API request failed:', error);
                throw error;
            }
        },
        
        createSession: async function(code) {
            return this.apiRequest('/sessions', {
                method: 'POST',
                body: JSON.stringify({ code })
            });
        },
        
        getSessionStatus: async function(sessionId) {
            return this.apiRequest(`/sessions/${sessionId}/status`);
        },
        
        getSession: async function(sessionId) {
            return this.apiRequest(`/sessions/${sessionId}`);
        },
        
        // ==================== Analysis Flow ====================
        startAnalysis: async function() {
            const codeInput = document.getElementById('rust-code');
            const analyzeBtn = document.getElementById('analyze-btn');
            
            const code = codeInput.value.trim();
            if (!code) {
                this.showMessage('Please enter some Rust code to analyze.', 'warning');
                return;
            }
            
            // Show loading state
            const originalText = analyzeBtn.innerHTML;
            analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
            analyzeBtn.disabled = true;
            
            // Also disable other buttons during analysis
            const quickScanBtn = document.getElementById('quick-scan');
            const clearBtn = document.getElementById('clear-btn');
            if (quickScanBtn) quickScanBtn.disabled = true;
            if (clearBtn) clearBtn.disabled = true;
            
            try {
                // Create session via API
                const session = await this.createSession(code);
                this.currentSessionId = session.id;
                
                // Show initial status
                this.showMessage(`Analysis started! Session ID: ${session.id.substring(0, 8)}...`, 'success');
                
                // Start polling for status updates
                this.startPolling(session.id);
                
            } catch (error) {
                this.showMessage(`Failed to start analysis: ${error.message}`, 'error');
                
                // Restore buttons
                analyzeBtn.innerHTML = originalText;
                analyzeBtn.disabled = false;
                if (quickScanBtn) quickScanBtn.disabled = false;
                if (clearBtn) clearBtn.disabled = false;
            }
        },
        
        startPolling: function(sessionId) {
            // Clear any existing polling
            this.stopPolling();
            
            this.currentSessionId = sessionId;
            this.pollingStartTime = Date.now();
            
            // Show progress display
            this.showProgressDisplay(sessionId);
            
            // Start polling immediately
            this.pollSessionStatus();
            
            // Set up interval for polling
            this.pollingInterval = setInterval(() => {
                this.pollSessionStatus();
            }, POLLING_INTERVAL);
            
            // Start time elapsed counter
            this.startTimeElapsedCounter();
        },
        
        showProgressDisplay: function(sessionId) {
            const progressDisplay = document.getElementById('progress-display');
            if (progressDisplay) {
                progressDisplay.style.display = 'block';
                
                // Update session ID
                const sessionIdElement = document.getElementById('session-id');
                if (sessionIdElement) {
                    sessionIdElement.textContent = sessionId.substring(0, 8) + '...';
                }
                
                // Reset time elapsed
                const timeElapsedElement = document.getElementById('time-elapsed');
                if (timeElapsedElement) {
                    timeElapsedElement.textContent = '0s';
                }
            }
        },
        
        hideProgressDisplay: function() {
            const progressDisplay = document.getElementById('progress-display');
            if (progressDisplay) {
                progressDisplay.style.display = 'none';
            }
        },
        
        startTimeElapsedCounter: function() {
            // Clear any existing counter
            if (this.timeElapsedInterval) {
                clearInterval(this.timeElapsedInterval);
            }
            
            const startTime = Date.now();
            this.timeElapsedInterval = setInterval(() => {
                const elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
                const timeElapsedElement = document.getElementById('time-elapsed');
                if (timeElapsedElement) {
                    timeElapsedElement.textContent = `${elapsedSeconds}s`;
                }
            }, 1000);
        },
        
        stopTimeElapsedCounter: function() {
            if (this.timeElapsedInterval) {
                clearInterval(this.timeElapsedInterval);
                this.timeElapsedInterval = null;
            }
        },
        
        stopPolling: function() {
            if (this.pollingInterval) {
                clearInterval(this.pollingInterval);
                this.pollingInterval = null;
            }
            this.currentSessionId = null;
            this.pollingStartTime = null;
            
            // Hide progress display and stop time counter
            this.hideProgressDisplay();
            this.stopTimeElapsedCounter();
        },
        
        pollSessionStatus: async function() {
            if (!this.currentSessionId) return;
            
            // Check if we've been polling too long
            if (Date.now() - this.pollingStartTime > MAX_POLLING_TIME) {
                this.showMessage('Analysis timed out after 10 minutes. Please try again.', 'error');
                this.stopPolling();
                this.restoreAnalysisButtons();
                return;
            }
            
            try {
                const status = await this.getSessionStatus(this.currentSessionId);
                
                // Update UI with progress
                this.updateProgress(status.progress, status.status);
                
                // Check if analysis is complete
                if (status.status === 'completed') {
                    const sessionId = this.currentSessionId; // Save before clearing
                    this.stopPolling();
                    this.fetchAndDisplayResults(sessionId);
                } else if (status.status === 'failed') {
                    const sessionId = this.currentSessionId; // Save before clearing
                    this.stopPolling();
                    this.showMessage('Analysis failed. Please try again.', 'error');
                    this.restoreAnalysisButtons();
                    // Optionally fetch results even for failed session
                    // this.fetchAndDisplayResults(sessionId);
                }
                // If still PROCESSING or PENDING, continue polling
                
            } catch (error) {
                console.error('Polling error:', error);
                // Don't show error for every failed poll, just log it
                // The next poll might succeed
            }
        },
        
        updateProgress: function(progress, status) {
            // Update progress bar if exists
            const progressBar = document.querySelector('.progress-bar');
            if (progressBar) {
                progressBar.style.width = `${progress}%`;
                progressBar.textContent = `${progress}%`;
            }
            
            // Update status message
            const statusElement = document.querySelector('.analysis-status');
            if (statusElement) {
                statusElement.textContent = `Status: ${status} (${progress}%)`;
            }
            
            // Update analyze button text
            const analyzeBtn = document.getElementById('analyze-btn');
            if (analyzeBtn && status !== 'COMPLETED' && status !== 'FAILED') {
                analyzeBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${status} (${progress}%)`;
            }
        },
        
        fetchAndDisplayResults: async function(sessionId) {
            // Validate session ID
            if (!sessionId) {
                this.showMessage('Cannot fetch results: invalid session ID', 'error');
                this.restoreAnalysisButtons();
                return;
            }
            
            try {
                const session = await this.getSession(sessionId);
                
                // Update results summary with actual analyses
                this.updateResultsSummary(session.analyses);
                
                // Display findings
                this.displayFindings(session.analyses);
                
                // Show success message
                this.showMessage(`Analysis complete! Found ${session.analyses.length} safety issue${session.analyses.length !== 1 ? 's' : ''}.`, 'success');
                
                // Restore buttons
                this.restoreAnalysisButtons();
                
            } catch (error) {
                this.showMessage(`Failed to fetch results: ${error.message}`, 'error');
                this.restoreAnalysisButtons();
            }
        },
        
        displayFindings: function(analyses) {
            const findingsContainer = document.querySelector('.findings-container');
            if (!findingsContainer) return;
            
            // Clear existing findings (except status message)
            const existingFindings = findingsContainer.querySelectorAll('.finding-card');
            existingFindings.forEach(finding => finding.remove());
            
            if (analyses.length === 0) {
                const noFindings = document.createElement('div');
                noFindings.className = 'no-findings';
                noFindings.innerHTML = `
                    <div class="status-message">
                        <i class="fas fa-check-circle"></i>
                        <p>No safety issues found! Your Rust code appears to be safe.</p>
                    </div>
                `;
                findingsContainer.prepend(noFindings);
                return;
            }
            
            // Create finding cards for each analysis
            analyses.forEach((analysis, index) => {
                const findingCard = this.createFindingCard(analysis, index);
                findingsContainer.prepend(findingCard);
            });
        },
        
        createFindingCard: function(analysis, index) {
            // Use code_block_type directly instead of severity
            const codeBlockType = analysis.code_block_type;
            const typeClass = codeBlockType.replace('_', '-'); // replaceable, non-replaceable, conditionally-replaceable
            
            // Format display text for code block type
            const typeDisplayText = this.formatCodeBlockType(codeBlockType);
            
            // Extract code snippets
            const unsafeCode = analysis.code_block?.raw_code || 'No code available';
            const safeCode = analysis.suggested_replacement || null;
            
            // Extract security metadata
            const cweId = analysis.cwe_id;
            const owaspCategory = analysis.owasp_category;
            const riskLevel = analysis.risk_level;
            const confidenceScore = analysis.confidence_score;
            const vulnerabilityDescription = analysis.vulnerability_description;
            const exploitationScenario = analysis.exploitation_scenario;
            const remediationExplanation = analysis.remediation_explanation;
            const verificationResult = analysis.verification_result;
            
            const card = document.createElement('div');
            card.className = `finding-card ${typeClass}`;
            card.innerHTML = `
                <div class="finding-header">
                    <span class="finding-badge ${typeClass}">${typeDisplayText}</span>
                    <span class="finding-title">${this.getFindingTitle(codeBlockType)}</span>
                    <span class="finding-confidence">${this.getConfidenceText(analysis)}</span>
                </div>
                
                <!-- Security Metadata -->
                <div class="security-metadata">
                    ${cweId ? `<span class="security-badge cwe"><i class="fas fa-bug"></i> ${cweId}</span>` : ''}
                    ${owaspCategory ? `<span class="security-badge owasp"><i class="fas fa-shield-alt"></i> ${owaspCategory}</span>` : ''}
                    ${riskLevel ? `<span class="security-badge risk-${riskLevel.toLowerCase()}"><i class="fas fa-exclamation-triangle"></i> ${riskLevel.toUpperCase()}</span>` : ''}
                    ${confidenceScore ? `<span class="security-badge confidence"><i class="fas fa-chart-line"></i> ${Math.round(confidenceScore * 100)}% confidence</span>` : ''}
                </div>
                
                <div class="finding-content">
                    <!-- Vulnerability Description -->
                    ${vulnerabilityDescription ? `
                    <div class="description-section">
                        <div class="section-label"><i class="fas fa-info-circle"></i> Vulnerability Description</div>
                        <div class="section-content">${this.escapeHtml(vulnerabilityDescription)}</div>
                    </div>
                    ` : ''}
                    
                    <!-- Exploitation Scenario -->
                    ${exploitationScenario ? `
                    <div class="description-section">
                        <div class="section-label"><i class="fas fa-bolt"></i> Exploitation Scenario</div>
                        <div class="section-content">${this.escapeHtml(exploitationScenario)}</div>
                    </div>
                    ` : ''}
                    
                    <!-- Code Blocks -->
                    <div class="code-block">
                        <div class="code-label"><i class="fas fa-code"></i> Unsafe Code (Lines ${analysis.code_block?.line_start || 1}-${analysis.code_block?.line_end || 1})</div>
                        <pre><code>${this.escapeHtml(unsafeCode)}</code></pre>
                    </div>
                    
                    <!-- Safe Alternative -->
                    ${safeCode ? `
                    <div class="code-block safe">
                        <div class="code-label"><i class="fas fa-check-circle"></i> Safe Alternative</div>
                        <pre><code>${this.escapeHtml(safeCode)}</code></pre>
                    </div>
                    ` : ''}
                    
                    <!-- Remediation Explanation -->
                    ${remediationExplanation ? `
                    <div class="description-section">
                        <div class="section-label"><i class="fas fa-wrench"></i> Remediation Explanation</div>
                        <div class="section-content">${this.escapeHtml(remediationExplanation)}</div>
                    </div>
                    ` : ''}
                    
                    <!-- Verification Result -->
                    ${verificationResult ? `
                    <div class="description-section verification">
                        <div class="section-label"><i class="fas fa-check-double"></i> Verification Result</div>
                        <div class="section-content">${this.escapeHtml(verificationResult)}</div>
                    </div>
                    ` : ''}
                </div>

                <div class="finding-actions">
                    ${safeCode ? `
                    <button class="action-btn apply" data-analysis-id="${analysis.id}">
                        <i class="fas fa-check"></i> Apply Fix
                    </button>
                    ` : ''}
                    <button class="action-btn false-positive" data-analysis-id="${analysis.id}">
                        <i class="fas fa-times"></i> False Positive
                    </button>
                    <button class="action-btn note" data-analysis-id="${analysis.id}">
                        <i class="fas fa-comment"></i> Add Note
                    </button>
                    <button class="action-btn details" data-analysis-id="${analysis.id}">
                        <i class="fas fa-ellipsis-h"></i> More Details
                    </button>
                </div>
            `;
            
            // Add event listeners
            const applyBtn = card.querySelector('.action-btn.apply');
            if (applyBtn) {
                applyBtn.addEventListener('click', () => this.applyFix(analysis.id));
            }
            
            const falsePositiveBtn = card.querySelector('.action-btn.false-positive');
            if (falsePositiveBtn) {
                falsePositiveBtn.addEventListener('click', () => this.markAsFalsePositive(analysis.id));
            }
            
            const noteBtn = card.querySelector('.action-btn.note');
            if (noteBtn) {
                noteBtn.addEventListener('click', () => this.addNoteToAnalysis(analysis.id));
            }
            
            const detailsBtn = card.querySelector('.action-btn.details');
            if (detailsBtn) {
                detailsBtn.addEventListener('click', () => this.showAnalysisDetails(analysis));
            }
            
            return card;
        },
        
        formatCodeBlockType: function(codeBlockType) {
            // Format code block type for display
            const formatMap = {
                'replaceable': 'Replaceable',
                'non_replaceable': 'Non-Replaceable',
                'conditionally_replaceable': 'Conditionally Replaceable'
            };
            return formatMap[codeBlockType] || codeBlockType;
        },
        
        getFindingTitle: function(codeBlockType) {
            const titleMap = {
                'replaceable': 'Replaceable Safety Issue',
                'non_replaceable': 'Non-Replaceable Pattern',
                'conditionally_replaceable': 'Conditionally Replaceable'
            };
            return titleMap[codeBlockType] || 'Code Analysis Finding';
        },
        
        getConfidenceText: function(analysis) {
            // In future, add confidence scores from backend
            return "High confidence";
        },
        
        applyFix: function(analysisId) {
            this.showMessage(`Applying fix for analysis ${analysisId.substring(0, 8)}...`, 'success');
            // In a real implementation, this would update the code editor
        },
        
        markAsFalsePositive: function(analysisId) {
            this.showMessage(`Marked analysis ${analysisId.substring(0, 8)} as false positive.`, 'info');
        },
        
        addNoteToAnalysis: function(analysisId) {
            const note = prompt(`Add a note for analysis ${analysisId.substring(0, 8)}:\n\nYour note:`, '');
            if (note) {
                this.showMessage(`Note added to analysis ${analysisId.substring(0, 8)}: "${note}"`, 'success');
            }
        },
        
        showAnalysisDetails: function(analysis) {
            const details = `
Analysis ID: ${analysis.id}
Code Block Type: ${analysis.code_block_type}
CWE: ${analysis.cwe_id || 'N/A'}
OWASP: ${analysis.owasp_category || 'N/A'}
Risk Level: ${analysis.risk_level || 'N/A'}
Confidence: ${analysis.confidence_score ? Math.round(analysis.confidence_score * 100) + '%' : 'N/A'}
Created: ${analysis.created_at || 'N/A'}
            `.trim();
            
            alert(`Analysis Details:\n\n${details}`);
        },
        
        escapeHtml: function(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        },
        
        restoreAnalysisButtons: function() {
            const analyzeBtn = document.getElementById('analyze-btn');
            const quickScanBtn = document.getElementById('quick-scan');
            const clearBtn = document.getElementById('clear-btn');
            
            if (analyzeBtn) {
                analyzeBtn.innerHTML = '<i class="fas fa-play"></i> Start Analysis';
                analyzeBtn.disabled = false;
            }
            if (quickScanBtn) quickScanBtn.disabled = false;
            if (clearBtn) clearBtn.disabled = false;
        },
        
        performQuickScan: function() {
            const codeInput = document.getElementById('rust-code');
            const code = codeInput.value.trim();
            
            if (!code) {
                this.showMessage('Please enter some code to scan.', 'warning');
                return;
            }
            
            // Show loading on quick scan button
            const quickScanBtn = document.getElementById('quick-scan');
            const originalText = quickScanBtn.innerHTML;
            quickScanBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scanning...';
            quickScanBtn.disabled = true;
            
            setTimeout(() => {
                const lines = this.countLines(code);
                const unsafeBlocks = this.countUnsafeBlocks(code);
                
                this.showMessage(`Quick scan complete: ${lines} lines, ${unsafeBlocks} unsafe block${unsafeBlocks !== 1 ? 's' : ''} detected.`, 'info');
                
                // Restore button
                quickScanBtn.innerHTML = originalText;
                quickScanBtn.disabled = false;
            }, 1000);
        },
        
        clearCodeInput: function() {
            const codeInput = document.getElementById('rust-code');
            codeInput.value = '';
            this.updateCodeStats('');
            this.showMessage('Code input cleared.', 'info');
        },
        
        // ==================== Finding Actions ====================
        initFindingActions: function() {
            // Apply Fix buttons
            document.querySelectorAll('.action-btn.apply').forEach(btn => {
                btn.addEventListener('click', () => {
                    const findingTitle = btn.closest('.finding-card').querySelector('.finding-title').textContent;
                    this.applyFix(findingTitle);
                });
            });
            
            // False Positive buttons
            document.querySelectorAll('.action-btn.false-positive').forEach(btn => {
                btn.addEventListener('click', () => {
                    const findingTitle = btn.closest('.finding-card').querySelector('.finding-title').textContent;
                    this.markAsFalsePositive(findingTitle);
                });
            });
            
            // Add Note buttons
            document.querySelectorAll('.action-btn.note').forEach(btn => {
                btn.addEventListener('click', () => {
                    const findingTitle = btn.closest('.finding-card').querySelector('.finding-title').textContent;
                    this.addNoteToFinding(findingTitle);
                });
            });
            
            // View All Sessions button
            const viewAllBtn = document.querySelector('.view-all-btn');
            if (viewAllBtn) {
                viewAllBtn.addEventListener('click', () => {
                    this.showMessage('This would navigate to the full sessions page.', 'info');
                });
            }
        },
        
        applyFix: function(findingTitle) {
            this.showMessage(`Applying fix for: ${findingTitle}. The safe alternative code would replace the unsafe code.`, 'success');
        },
        
        markAsFalsePositive: function(findingTitle) {
            this.showMessage(`Marked as false positive: ${findingTitle}. This feedback helps improve the AI model.`, 'info');
        },
        
        addNoteToFinding: function(findingTitle) {
            const note = prompt(`Add a note for: ${findingTitle}\n\nYour note:`, '');
            if (note) {
                this.showMessage(`Note added to ${findingTitle}: "${note}"`, 'success');
            }
        },
        
        // ==================== Results Summary ====================
        updateResultsSummary: function(analyses) {
            const summaryItems = document.querySelectorAll('.summary-item');
            if (summaryItems.length >= 4) {
                // Calculate counts by code block type
                let replaceableCount = 0;
                let nonReplaceableCount = 0;
                let conditionallyReplaceableCount = 0;
                
                analyses.forEach(analysis => {
                    switch (analysis.code_block_type) {
                        case 'replaceable':
                            replaceableCount++;
                            break;
                        case 'non_replaceable':
                            nonReplaceableCount++;
                            break;
                        case 'conditionally_replaceable':
                            conditionallyReplaceableCount++;
                            break;
                    }
                });
                
                const totalIssues = analyses.length;
                
                // Update total issues
                const totalElement = summaryItems[0].querySelector('.summary-value');
                if (totalElement) {
                    totalElement.textContent = totalIssues;
                }
                
                // Update replaceable count
                const replaceableElement = summaryItems[1].querySelector('.summary-value');
                if (replaceableElement) {
                    replaceableElement.textContent = replaceableCount;
                    // Add styling class if needed
                    replaceableElement.parentElement.classList.toggle('has-issues', replaceableCount > 0);
                }
                
                // Update non-replaceable count
                const nonReplaceableElement = summaryItems[2].querySelector('.summary-value');
                if (nonReplaceableElement) {
                    nonReplaceableElement.textContent = nonReplaceableCount;
                }
                
                // Update conditionally replaceable count
                const conditionallyReplaceableElement = summaryItems[3].querySelector('.summary-value');
                if (conditionallyReplaceableElement) {
                    conditionallyReplaceableElement.textContent = conditionallyReplaceableCount;
                }
            }
        },
        
        // ==================== Responsive Behavior ====================
        initResponsiveBehavior: function() {
            // Update layout on window resize
            window.addEventListener('resize', () => {
                const contentGrid = document.querySelector('.content-grid');
                if (contentGrid) {
                    const isMobile = window.innerWidth <= 900;
                    contentGrid.classList.toggle('mobile-layout', isMobile);
                }
            });
        },
        
        // ==================== Example Interactions ====================
        setupExampleInteractions: function() {
            // Auto-update session statuses for demo
            setInterval(() => this.updateSessionStatuses(), 5000);
            
            // Add click handlers to session items
            document.querySelectorAll('.session-item').forEach(item => {
                item.addEventListener('click', () => {
                    const sessionName = item.querySelector('.session-name').textContent;
                    const status = item.querySelector('.session-status').textContent;
                    this.showMessage(`Session: ${sessionName} (${status}). Click "View All Sessions" for details.`, 'info');
                });
            });
            
            // Settings change handlers
            document.querySelectorAll('.setting select').forEach(select => {
                select.addEventListener('change', () => {
                    console.log(`Setting changed: ${select.id} = ${select.value}`);
                });
            });
        },
        
        updateSessionStatuses: function() {
            // Randomly update session statuses for demo purposes
            document.querySelectorAll('.session-status').forEach(statusEl => {
                if (Math.random() > 0.7) { // 30% chance to change
                    const currentStatus = statusEl.textContent;
                    const statusClasses = ['completed', 'in-progress', 'queued'];
                    const statusTexts = ['Completed', 'In Progress', 'Queued'];
                    
                    const currentIndex = statusTexts.findIndex(text => currentStatus.includes(text));
                    if (currentIndex !== -1) {
                        const newIndex = (currentIndex + 1) % statusClasses.length;
                        
                        // Update classes
                        statusClasses.forEach(cls => statusEl.classList.remove(cls));
                        statusEl.classList.add(statusClasses[newIndex]);
                        
                        // Update text
                        statusEl.textContent = statusTexts[newIndex];
                    }
                }
            });
        },
        
        // ==================== Live Data Updates ====================
        updateLiveData: function() {
            // Simulate live data updates
            this.updateActiveSessions();
            this.updatePerformanceMetrics();
            this.updateSystemStatus();
        },
        
        updateActiveSessions: function() {
            const sessionItems = document.querySelectorAll('.session-item');
            sessionItems.forEach(item => {
                const status = item.querySelector('.session-status');
                if (status.classList.contains('in-progress')) {
                    // Update progress bars
                    const progressFill = item.querySelector('.progress-fill');
                    if (progressFill) {
                        const currentWidth = parseInt(progressFill.style.width) || 75;
                        const newWidth = Math.min(currentWidth + Math.random() * 10, 100);
                        progressFill.style.width = `${newWidth}%`;
                        
                        const progressText = item.querySelector('.progress-text');
                        if (progressText) {
                            progressText.textContent = `${Math.round(newWidth)}% complete`;
                        }
                        
                        // Randomly complete some sessions
                        if (newWidth >= 100) {
                            status.classList.remove('in-progress');
                            status.classList.add('completed');
                            status.innerHTML = '<i class="fas fa-check-circle"></i> Completed';
                            
                            // Add results
                            const sessionDetails = item.querySelector('.session-details');
                            if (sessionDetails) {
                                sessionDetails.innerHTML = `
                                    <div class="session-results">
                                        <div class="result-stat">
                                            <span class="stat-count high">${Math.floor(Math.random() * 5) + 1}</span>
                                            <span class="stat-label">Critical</span>
                                        </div>
                                        <div class="result-stat">
                                            <span class="stat-count medium">${Math.floor(Math.random() * 8) + 3}</span>
                                            <span class="stat-label">High</span>
                                        </div>
                                        <div class="result-stat">
                                            <span class="stat-count low">${Math.floor(Math.random() * 10) + 5}</span>
                                            <span class="stat-label">Medium</span>
                                        </div>
                                    </div>
                                    <div class="session-actions">
                                        <button class="btn btn-small">
                                            <i class="fas fa-eye"></i>
                                            View Report
                                        </button>
                                        <button class="btn btn-small btn-outline">
                                            <i class="fas fa-download"></i>
                                            Export
                                        </button>
                                    </div>
                                `;
                            }
                        }
                    }
                }
            });
        },
        
        updatePerformanceMetrics: function() {
            const metrics = document.querySelectorAll('.metric-value');
            if (metrics.length >= 4) {
                // Update parse time (slight random variation)
                let parseTime = parseFloat(metrics[0].textContent);
                parseTime = Math.max(1.5, parseTime + (Math.random() - 0.5) * 0.2);
                metrics[0].textContent = parseTime.toFixed(1) + 's';
                
                // Update accuracy (slight improvement)
                let accuracy = parseFloat(metrics[1].textContent);
                accuracy = Math.min(99, accuracy + (Math.random() * 0.5));
                metrics[1].textContent = Math.round(accuracy) + '%';
                
                // Update active workers (random variation)
                let workers = parseInt(metrics[2].textContent);
                workers = Math.max(10, Math.min(25, workers + Math.floor(Math.random() * 3) - 1));
                metrics[2].textContent = workers;
                
                // Update uptime (stable)
                let uptime = parseFloat(metrics[3].textContent);
                uptime = Math.min(99.9, uptime + (Math.random() * 0.05));
                metrics[3].textContent = uptime.toFixed(1) + '%';
            }
        },
        
        updateSystemStatus: function() {
            // Randomly change system status indicators
            const statusItems = document.querySelectorAll('.status-item');
            statusItems.forEach(item => {
                if (Math.random() > 0.7) { // 30% chance to change
                    const dot = item.querySelector('.status-dot');
                    if (dot) {
                        const isOnline = item.classList.contains('online');
                        const isWarning = item.classList.contains('warning');
                        
                        if (isOnline && Math.random() > 0.8) {
                            item.classList.remove('online');
                            item.classList.add('warning');
                            item.textContent = item.textContent.replace('Online', 'High Load');
                        } else if (isWarning && Math.random() > 0.6) {
                            item.classList.remove('warning');
                            item.classList.add('online');
                            item.textContent = item.textContent.replace('High Load', 'Online');
                        }
                    }
                }
            });
        },
        
        // ==================== Utility Functions ====================
        countLines: function(code) {
            return code.split('\n').length;
        },
        
        countUnsafeBlocks: function(code) {
            // Simple regex to count unsafe blocks
            const unsafeRegex = /\bunsafe\s*\{/g;
            const matches = code.match(unsafeRegex);
            return matches ? matches.length : 0;
        },
        
        showMessage: function(message, type = 'info') {
            // Create message element
            const messageEl = document.createElement('div');
            messageEl.className = `demo-message ${type}`;
            messageEl.innerHTML = `
                <i class="fas fa-${this.getIconForType(type)}"></i>
                <span>${message}</span>
                <button class="close-btn">&times;</button>
            `;
            
            // Style the message
            messageEl.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: ${this.getColorForType(type)};
                color: white;
                padding: 12px 16px;
                border-radius: 6px;
                display: flex;
                align-items: center;
                gap: 10px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                z-index: 1000;
                max-width: 400px;
                animation: slideIn 0.3s ease;
            `;
            
            // Close button
            const closeBtn = messageEl.querySelector('.close-btn');
            closeBtn.style.cssText = `
                background: transparent;
                border: none;
                color: white;
                font-size: 20px;
                cursor: pointer;
                margin-left: auto;
                padding: 0;
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
            `;
            
            closeBtn.addEventListener('click', () => {
                messageEl.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => {
                    if (messageEl.parentNode) {
                        messageEl.parentNode.removeChild(messageEl);
                    }
                }, 500);
            });
            
            // Add CSS for animations if not already present
            if (!document.querySelector('#message-styles')) {
                const styleEl = document.createElement('style');
                styleEl.id = 'message-styles';
                styleEl.textContent = `
                    @keyframes slideIn {
                        from { transform: translateX(100%); opacity: 0; }
                        to { transform: translateX(0); opacity: 1; }
                    }
                    @keyframes slideOut {
                        from { transform: translateX(0); opacity: 1; }
                        to { transform: translateX(100%); opacity: 0; }
                    }
                `;
                document.head.appendChild(styleEl);
            }
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                if (messageEl.parentNode) {
                    closeBtn.click();
                }
            }, 5000);
            
            document.body.appendChild(messageEl);
        },
        
        getIconForType: function(type) {
            const icons = {
                'success': 'check-circle',
                'warning': 'exclamation-triangle',
                'info': 'info-circle',
                'error': 'times-circle'
            };
            return icons[type] || 'info-circle';
        },
        
        getColorForType: function(type) {
            const colors = {
                'success': '#38a169',
                'warning': '#d69e2e',
                'info': '#3182ce',
                'error': '#e53e3e'
            };
            return colors[type] || '#3182ce';
        }
    };
    
    // Initialize the application when DOM is ready
    document.addEventListener('DOMContentLoaded', () => RustGreenApp.init());
    
    // Expose to global scope only if needed for debugging
    window.RustGreenApp = RustGreenApp;
    
    console.log('rust-green mock-up JavaScript loaded successfully');
})();
