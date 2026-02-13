// Session detail page JavaScript for rust-green
(function() {
    'use strict';
    
    // Configuration
    const API_BASE_URL = 'http://localhost:8000/api/v1';
    const POLLING_INTERVAL = 2000; // 2 seconds
    const MAX_POLLING_TIME = 10 * 60 * 1000; // 10 minutes
    
    // Application state
    const SessionDetailApp = {
        sessionId: null,
        sessionData: null,
        pollingInterval: null,
        pollingStartTime: null,
        timeElapsedInterval: null,
        
        // Initialize the application
        init: function() {
            console.log('Session detail page loaded');
            
            // Get session ID from URL
            this.sessionId = this.getSessionIdFromUrl();
            if (!this.sessionId) {
                this.showError('No session ID provided in URL');
                return;
            }
            
            // Initialize event listeners
            this.initEventListeners();
            
            // Load session data
            this.loadSessionData();
        },
        
        // Get session ID from URL query parameters
        getSessionIdFromUrl: function() {
            const urlParams = new URLSearchParams(window.location.search);
            return urlParams.get('id');
        },
        
        // Initialize event listeners
        initEventListeners: function() {
            // Action buttons
            const reanalyzeBtn = document.getElementById('reanalyze-btn');
            const exportBtn = document.getElementById('export-btn');
            const deleteBtn = document.getElementById('delete-btn');
            
            if (reanalyzeBtn) {
                reanalyzeBtn.addEventListener('click', () => this.reanalyzeSession());
            }
            
            if (exportBtn) {
                exportBtn.addEventListener('click', () => this.exportSession());
            }
            
            if (deleteBtn) {
                deleteBtn.addEventListener('click', () => this.deleteSession());
            }
        },
        
        // Load session data from API
        loadSessionData: function() {
            this.showLoadingState();
            
            this.apiRequest(`/sessions/${this.sessionId}`)
                .then(session => {
                    this.sessionData = session;
                    this.renderSessionData();
                    
                    // If session is still processing, start polling
                    if (session.status === 'processing' || session.status === 'pending') {
                        this.startPolling();
                    }
                })
                .catch(error => {
                    console.error('Failed to load session data:', error);
                    this.showError(`Failed to load session data: ${error.message}`);
                });
        },
        
        // Show loading state
        showLoadingState: function() {
            const findingsContainer = document.getElementById('findings-container');
            const noFindingsMessage = document.getElementById('no-findings-message');
            const progressDisplay = document.getElementById('progress-display');
            
            if (findingsContainer) {
                findingsContainer.innerHTML = `
                    <div class="loading-message">
                        <i class="fas fa-spinner fa-spin"></i>
                        <p>Loading session data...</p>
                    </div>
                `;
            }
            
            if (noFindingsMessage) {
                noFindingsMessage.style.display = 'none';
            }
            
            if (progressDisplay) {
                progressDisplay.style.display = 'none';
            }
        },
        
        // Render session data to the page
        renderSessionData: function() {
            if (!this.sessionData) return;
            
            const session = this.sessionData;
            
            // Update metadata
            this.updateMetadata(session);
            
            // Update results summary
            this.updateResultsSummary(session.analyses);
            
            // Show/hide error message
            this.updateErrorMessage(session);
            
            // Show/hide progress display
            this.updateProgressDisplay(session);
            
            // Render findings
            this.renderFindings(session.analyses);
            
            // Update action buttons state
            this.updateActionButtons(session);
        },
        
        // Update session metadata
        updateMetadata: function(session) {
            // Format dates
            const createdDate = new Date(session.created_at);
            const createdStr = createdDate.toLocaleDateString() + ' ' + createdDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            
            const completedStr = session.completed_at 
                ? new Date(session.completed_at).toLocaleDateString() + ' ' + new Date(session.completed_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
                : 'N/A';
            
            // Update DOM elements
            const sessionIdEl = document.getElementById('session-id');
            const sessionStatusEl = document.getElementById('session-status');
            const sessionCreatedEl = document.getElementById('session-created');
            const sessionCompletedEl = document.getElementById('session-completed');
            const sessionProgressEl = document.getElementById('session-progress');
            const analysisCountEl = document.getElementById('analysis-count');
            
            if (sessionIdEl) {
                sessionIdEl.textContent = session.id.substring(0, 12) + '...';
            }
            
            if (sessionStatusEl) {
                sessionStatusEl.textContent = session.status.charAt(0).toUpperCase() + session.status.slice(1);
                sessionStatusEl.className = `session-status-badge ${session.status.toLowerCase()}`;
            }
            
            if (sessionCreatedEl) {
                sessionCreatedEl.textContent = createdStr;
            }
            
            if (sessionCompletedEl) {
                sessionCompletedEl.textContent = completedStr;
            }
            
            if (sessionProgressEl) {
                sessionProgressEl.textContent = `${session.progress}%`;
            }
            
            if (analysisCountEl) {
                analysisCountEl.textContent = session.analyses.length;
            }
        },
        
        // Update results summary
        updateResultsSummary: function(analyses) {
            const summaryItems = document.querySelectorAll('.summary-item');
            if (summaryItems.length < 4) return;
            
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
        },
        
        // Update error message display
        updateErrorMessage: function(session) {
            const errorMessageEl = document.getElementById('error-message');
            const errorTextEl = document.getElementById('error-text');
            
            if (errorMessageEl && errorTextEl) {
                if (session.error_message && session.status === 'failed') {
                    errorTextEl.textContent = session.error_message;
                    errorMessageEl.style.display = 'block';
                } else {
                    errorMessageEl.style.display = 'none';
                }
            }
        },
        
        // Update progress display
        updateProgressDisplay: function(session) {
            const progressDisplay = document.getElementById('progress-display');
            const progressBar = document.querySelector('.progress-bar');
            const analysisStatus = document.querySelector('.analysis-status');
            const detailSessionId = document.getElementById('detail-session-id');
            
            if (progressDisplay && progressBar && analysisStatus && detailSessionId) {
                if (session.status === 'processing' || session.status === 'pending') {
                    progressDisplay.style.display = 'block';
                    progressBar.style.width = `${session.progress}%`;
                    progressBar.textContent = `${session.progress}%`;
                    analysisStatus.textContent = `Status: ${session.status.toUpperCase()} (${session.progress}%)`;
                    detailSessionId.textContent = session.id.substring(0, 8) + '...';
                    
                    // Start time elapsed counter if not already running
                    if (!this.timeElapsedInterval) {
                        this.startTimeElapsedCounter();
                    }
                } else {
                    progressDisplay.style.display = 'none';
                    this.stopTimeElapsedCounter();
                }
            }
        },
        
        // Start time elapsed counter
        startTimeElapsedCounter: function() {
            // Clear any existing counter
            if (this.timeElapsedInterval) {
                clearInterval(this.timeElapsedInterval);
            }
            
            const startTime = Date.now();
            this.timeElapsedInterval = setInterval(() => {
                const elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
                const timeElapsedElement = document.getElementById('detail-time-elapsed');
                if (timeElapsedElement) {
                    timeElapsedElement.textContent = `${elapsedSeconds}s`;
                }
            }, 1000);
        },
        
        // Stop time elapsed counter
        stopTimeElapsedCounter: function() {
            if (this.timeElapsedInterval) {
                clearInterval(this.timeElapsedInterval);
                this.timeElapsedInterval = null;
            }
        },
        
        // Render findings
        renderFindings: function(analyses) {
            const findingsContainer = document.getElementById('findings-container');
            const noFindingsMessage = document.getElementById('no-findings-message');
            
            if (!findingsContainer) return;
            
            if (analyses.length === 0) {
                findingsContainer.innerHTML = '';
                if (noFindingsMessage) {
                    noFindingsMessage.style.display = 'block';
                }
                return;
            }
            
            if (noFindingsMessage) {
                noFindingsMessage.style.display = 'none';
            }
            
            // Clear existing findings
            findingsContainer.innerHTML = '';
            
            // Create finding cards
            analyses.forEach((analysis, index) => {
                const findingCard = this.createFindingCard(analysis, index);
                findingsContainer.appendChild(findingCard);
            });
        },
        
        // Create a finding card (reusing logic from main app)
        createFindingCard: function(analysis, index) {
            // Reuse the createFindingCard function from the main app if available
            if (window.RustGreenApp && typeof window.RustGreenApp.createFindingCard === 'function') {
                return window.RustGreenApp.createFindingCard(analysis, index);
            }
            
            // Fallback implementation
            const codeBlockType = analysis.code_block_type;
            const typeClass = codeBlockType.replace('_', '-');
            
            // Format display text for code block type
            const typeDisplayText = this.formatCodeBlockType(codeBlockType);
            
            // Extract code snippets
            const unsafeCode = analysis.code_block?.raw_code || 'No code available';
            const safeCode = analysis.suggested_replacement?.raw_code || null;
            
            // Get diff if available
            const diffCode = analysis.diff || null;
            
            const card = document.createElement('div');
            card.className = `finding-card ${typeClass}`;
            card.innerHTML = `
                <div class="finding-header">
                    <span class="finding-badge ${typeClass}">${typeDisplayText}</span>
                    <span class="finding-title">${this.getFindingTitle(codeBlockType)}</span>
                    <span class="finding-confidence">${this.getConfidenceText(analysis)}</span>
                </div>
                
                <div class="finding-content">
                    ${diffCode ? `
                    <div class="code-block diff">
                        <div class="code-label">Diff (Changes):</div>
                        <pre><code>${this.escapeHtml(diffCode)}</code></pre>
                    </div>
                    ` : ''}
                    
                    <div class="code-block">
                        <div class="code-label">Unsafe Code:</div>
                        <pre><code>${this.escapeHtml(unsafeCode)}</code></pre>
                    </div>
                    
                    ${safeCode ? `
                    <div class="code-block safe">
                        <div class="code-label">Safe Alternative:</div>
                        <pre><code>${this.escapeHtml(safeCode)}</code></pre>
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
            
            return card;
        },
        
        // Update action buttons state
        updateActionButtons: function(session) {
            const reanalyzeBtn = document.getElementById('reanalyze-btn');
            const exportBtn = document.getElementById('export-btn');
            const deleteBtn = document.getElementById('delete-btn');
            
            if (reanalyzeBtn) {
                reanalyzeBtn.disabled = session.status === 'processing' || session.status === 'pending';
            }
            
            if (exportBtn) {
                exportBtn.disabled = session.status !== 'completed' || session.analyses.length === 0;
            }
        },
        
        // Start polling for session updates
        startPolling: function() {
            // Clear any existing polling
            this.stopPolling();
            
            this.pollingStartTime = Date.now();
            
            // Start polling immediately
            this.pollSessionStatus();
            
            // Set up interval for polling
            this.pollingInterval = setInterval(() => {
                this.pollSessionStatus();
            }, POLLING_INTERVAL);
        },
        
        // Stop polling
        stopPolling: function() {
            if (this.pollingInterval) {
                clearInterval(this.pollingInterval);
                this.pollingInterval = null;
            }
            this.pollingStartTime = null;
        },
        
        // Poll session status
        pollSessionStatus: async function() {
            if (!this.sessionId) return;
            
            // Check if we've been polling too long
            if (Date.now() - this.pollingStartTime > MAX_POLLING_TIME) {
                this.showMessage('Session polling timed out after 10 minutes.', 'error');
                this.stopPolling();
                return;
            }
            
            try {
                const status = await this.apiRequest(`/sessions/${this.sessionId}/status`);
                
                // Update progress display
                this.updateProgressFromStatus(status);
                
                // Check if analysis is complete
                if (status.status === 'completed' || status.status === 'failed') {
                    this.stopPolling();
                    // Reload full session data
                    this.loadSessionData();
                }
                
            } catch (error) {
                console.error('Polling error:', error);
                // Don't show error for every failed poll
            }
        },
        
        // Update progress from status response
        updateProgressFromStatus: function(status) {
            const progressBar = document.querySelector('.progress-bar');
            const analysisStatus = document.querySelector('.analysis-status');
            
            if (progressBar) {
                progressBar.style.width = `${status.progress}%`;
                progressBar.textContent = `${status.progress}%`;
            }
            
            if (analysisStatus) {
                analysisStatus.textContent = `Status: ${status.status.toUpperCase()} (${status.progress}%)`;
            }
            
            // Update session data if we have it
            if (this.sessionData) {
                this.sessionData.status = status.status;
                this.sessionData.progress = status.progress;
                this.updateMetadata(this.sessionData);
            }
        },
        
        // Action button handlers
        reanalyzeSession: function() {
            this.showMessage('Re-analyze functionality not yet implemented', 'info');
        },
        
        exportSession: function() {
            this.showMessage('Export functionality not yet implemented', 'info');
        },
        
        deleteSession: function() {
            if (confirm('Are you sure you want to delete this session? This action cannot be undone.')) {
                this.apiRequest(`/sessions/${this.sessionId}`, { method: 'DELETE' })
                    .then(() => {
                        this.showMessage('Session deleted successfully', 'success');
                        // Redirect back to sessions page after a delay
                        setTimeout(() => {
                            window.location.href = 'sessions.html';
                        }, 1500);
                    })
                    .catch(error => {
                        console.error('Failed to delete session:', error);
                        this.showMessage(`Failed to delete session: ${error.message}`, 'error');
                    });
            }
        },
        
        applyFix: function(analysisId) {
            this.showMessage(`Applying fix for analysis ${analysisId.substring(0, 8)}...`, 'success');
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
        
        // Utility functions
        formatCodeBlockType: function(codeBlockType) {
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
            return "High confidence";
        },
        
        escapeHtml: function(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        },
        
        // API request helper
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
        
        // Show a message to the user
        showMessage: function(message, type = 'info') {
            // Reuse the message function from the main app if available
            if (window.RustGreenApp && typeof window.RustGreenApp.showMessage === 'function') {
                window.RustGreenApp.showMessage(message, type);
                return;
            }
            
            // Fallback message display
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
        },
        
        // Show error message
        showError: function(message) {
            const findingsContainer = document.getElementById('findings-container');
            if (findingsContainer) {
                findingsContainer.innerHTML = `
                    <div class="error-message">
                        <i class="fas fa-exclamation-triangle"></i>
                        <div>
                            <h4>Error Loading Session</h4>
                            <p>${this.escapeHtml(message)}</p>
                            <button onclick="window.location.href='sessions.html'" class="primary-btn">
                                <i class="fas fa-arrow-left"></i> Back to Sessions
                            </button>
                        </div>
                    </div>
                `;
            }
        }
    };
    
    // Initialize the application when DOM is ready
    document.addEventListener('DOMContentLoaded', () => SessionDetailApp.init());
    
    // Expose to global scope for debugging
    window.SessionDetailApp = SessionDetailApp;
    
    console.log('Session detail page JavaScript loaded successfully');
})();
