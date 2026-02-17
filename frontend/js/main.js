/**
 * rust-green Main Application Module
 * Handles analysis flow and app initialization
 */
const RustGreenApp = {
    // Current session state
    currentSessionId: null,
    currentMode: 'paste',
    pollingInterval: null,
    pollingStartTime: null,
    timeElapsedInterval: null,
    
    /**
     * Initialize the application
     */
    init: function() {
        console.log('rust-green frontend loaded with backend integration');
        
        // Initialize all components
        this.initInputOptions();
        this.initCodeInput();
        this.initActionButtons();
        this.initResponsiveBehavior();
        
        // Initialize Git handlers
        RustGreenGitHandlers.init();
        
        // Set up example interactions
        this.setupExampleInteractions();
        
        // Update live data (simulated)
        this.updateLiveData();
        
        // Set up periodic updates
        setInterval(() => this.updateLiveData(), RustGreenConfig.LIVE_DATA_INTERVAL);
    },
    
    // ==================== Input Options ====================
    
    initInputOptions: function() {
        const optionButtons = document.querySelectorAll('.option-btn');
        const codeInput = document.getElementById('rust-code');
        const gitSection = document.getElementById('git-input-section');
        const codeContainer = document.getElementById('code-input-container');
        
        optionButtons.forEach(button => {
            button.addEventListener('click', () => {
                optionButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                
                const mode = button.getAttribute('data-mode');
                this.switchInputMode(mode, codeInput, gitSection, codeContainer);
            });
        });
    },
    
    switchInputMode: function(mode, codeInput, gitSection, codeContainer) {
        if (mode === 'git') {
            gitSection.style.display = 'block';
            codeContainer.style.display = 'none';
            this.currentMode = 'git';
        } else {
            gitSection.style.display = 'none';
            codeContainer.style.display = 'block';
            this.currentMode = mode;
            
            const placeholders = {
                'paste': 'Paste your Rust code here...',
                'upload': 'File will be uploaded and displayed here...'
            };
            codeInput.placeholder = placeholders[mode] || placeholders.paste;
        }
    },
    
    // ==================== Code Input ====================
    
    initCodeInput: function() {
        const codeInput = document.getElementById('rust-code');
        if (!codeInput) return;
        
        codeInput.addEventListener('input', () => {
            this.updateCodeStats(codeInput.value);
        });
        
        this.updateCodeStats(codeInput.value);
    },
    
    updateCodeStats: function(code) {
        const inputInfo = document.querySelector('.input-info');
        if (!inputInfo) return;
        
        const lines = RustGreenUtils.countLines(code);
        const unsafeBlocks = RustGreenUtils.countUnsafeBlocks(code);
        
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
    
    // ==================== Analysis Flow ====================
    
    startAnalysis: async function() {
        const analyzeBtn = document.getElementById('analyze-btn');
        
        // Check current mode
        if (this.currentMode === 'git') {
            return await this.startGitAnalysis();
        }
        
        // Code paste mode
        const codeInput = document.getElementById('rust-code');
        const code = codeInput.value.trim();
        if (!code) {
            RustGreenUtils.showMessage('Please enter some Rust code to analyze.', 'warning');
            return;
        }
        
        // Show loading state
        const originalText = analyzeBtn.innerHTML;
        analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
        analyzeBtn.disabled = true;
        
        this.disableButtons(true);
        
        try {
            const session = await RustGreenAPI.createSession(code);
            this.currentSessionId = session.id;
            
            RustGreenUtils.showMessage(`Analysis started! Session ID: ${session.id.substring(0, 8)}...`, 'success');
            this.startPolling(session.id);
            
        } catch (error) {
            RustGreenUtils.showMessage(`Failed to start analysis: ${error.message}`, 'error');
            analyzeBtn.innerHTML = originalText;
            analyzeBtn.disabled = false;
            this.disableButtons(false);
        }
    },
    
    startGitAnalysis: async function() {
        const analyzeBtn = document.getElementById('analyze-btn');
        
        // Validate Git state
        if (!RustGreenGitHandlers.state.url) {
            RustGreenUtils.showMessage('Please enter a Git repository URL.', 'warning');
            return;
        }
        
        if (!RustGreenGitHandlers.state.selectedRef) {
            RustGreenUtils.showMessage('Please select a branch or tag.', 'warning');
            return;
        }
        
        const selectedFiles = RustGreenGitHandlers.getSelectedFiles();
        if (selectedFiles.length === 0) {
            RustGreenUtils.showMessage('Please select at least one file to analyze.', 'warning');
            return;
        }
        
        // Show loading state
        const originalText = analyzeBtn.innerHTML;
        analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Cloning & Analyzing...';
        analyzeBtn.disabled = true;
        
        try {
            const response = await RustGreenAPI.createGitSession(
                RustGreenGitHandlers.state.url,
                RustGreenGitHandlers.state.selectedRef,
                selectedFiles
            );
            
            this.currentSessionId = response.id;
            RustGreenUtils.showMessage(`Git analysis started! Session ID: ${response.id.substring(0, 8)}...`, 'success');
            this.startPolling(response.id);
            
        } catch (error) {
            RustGreenUtils.showMessage(`Failed to start Git analysis: ${error.message}`, 'error');
            analyzeBtn.innerHTML = originalText;
            analyzeBtn.disabled = false;
        }
    },
    
    // ==================== Polling ====================
    
    startPolling: function(sessionId) {
        this.stopPolling();
        
        this.currentSessionId = sessionId;
        this.pollingStartTime = Date.now();
        
        this.showProgressDisplay(sessionId);
        this.pollSessionStatus();
        
        this.pollingInterval = setInterval(() => {
            this.pollSessionStatus();
        }, RustGreenConfig.POLLING_INTERVAL);
        
        this.startTimeElapsedCounter();
    },
    
    showProgressDisplay: function(sessionId) {
        const progressDisplay = document.getElementById('progress-display');
        if (progressDisplay) {
            progressDisplay.style.display = 'block';
            
            const sessionIdElement = document.getElementById('session-id');
            if (sessionIdElement) {
                sessionIdElement.textContent = sessionId.substring(0, 8) + '...';
            }
            
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
        
        this.hideProgressDisplay();
        this.stopTimeElapsedCounter();
    },
    
    pollSessionStatus: async function() {
        if (!this.currentSessionId) return;
        
        if (Date.now() - this.pollingStartTime > RustGreenConfig.MAX_POLLING_TIME) {
            RustGreenUtils.showMessage('Analysis timed out after 10 minutes. Please try again.', 'error');
            this.stopPolling();
            this.restoreAnalysisButtons();
            return;
        }
        
        try {
            const status = await RustGreenAPI.getSessionStatus(this.currentSessionId);
            this.updateProgress(status.progress, status.status);
            
            if (status.status === 'completed') {
                const sessionId = this.currentSessionId;
                this.stopPolling();
                this.fetchAndDisplayResults(sessionId);
            } else if (status.status === 'failed') {
                this.stopPolling();
                RustGreenUtils.showMessage('Analysis failed. Please try again.', 'error');
                this.restoreAnalysisButtons();
            }
            
        } catch (error) {
            console.error('Polling error:', error);
        }
    },
    
    updateProgress: function(progress, status) {
        const progressBar = document.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
            progressBar.textContent = `${progress}%`;
        }
        
        const statusElement = document.querySelector('.analysis-status');
        if (statusElement) {
            statusElement.textContent = `Status: ${status} (${progress}%)`;
        }
        
        const analyzeBtn = document.getElementById('analyze-btn');
        if (analyzeBtn && status !== 'COMPLETED' && status !== 'FAILED') {
            analyzeBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${status} (${progress}%)`;
        }
    },
    
    fetchAndDisplayResults: async function(sessionId) {
        if (!sessionId) {
            RustGreenUtils.showMessage('Cannot fetch results: invalid session ID', 'error');
            this.restoreAnalysisButtons();
            return;
        }
        
        try {
            const session = await RustGreenAPI.getSession(sessionId);
            
            RustGreenFindings.updateSummary(session.analyses);
            RustGreenFindings.display(session.analyses, sessionId);
            
            RustGreenUtils.showMessage(
                `Analysis complete! Found ${session.analyses.length} safety issue${session.analyses.length !== 1 ? 's' : ''}.`,
                'success'
            );
            
            this.restoreAnalysisButtons();
            
        } catch (error) {
            RustGreenUtils.showMessage(`Failed to fetch results: ${error.message}`, 'error');
            this.restoreAnalysisButtons();
        }
    },
    
    // ==================== Utility Methods ====================
    
    disableButtons: function(disabled) {
        const quickScanBtn = document.getElementById('quick-scan');
        const clearBtn = document.getElementById('clear-btn');
        if (quickScanBtn) quickScanBtn.disabled = disabled;
        if (clearBtn) clearBtn.disabled = disabled;
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
            RustGreenUtils.showMessage('Please enter some code to scan.', 'warning');
            return;
        }
        
        const quickScanBtn = document.getElementById('quick-scan');
        const originalText = quickScanBtn.innerHTML;
        quickScanBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scanning...';
        quickScanBtn.disabled = true;
        
        setTimeout(() => {
            const lines = RustGreenUtils.countLines(code);
            const unsafeBlocks = RustGreenUtils.countUnsafeBlocks(code);
            
            RustGreenUtils.showMessage(
                `Quick scan complete: ${lines} lines, ${unsafeBlocks} unsafe block${unsafeBlocks !== 1 ? 's' : ''} detected.`,
                'info'
            );
            
            quickScanBtn.innerHTML = originalText;
            quickScanBtn.disabled = false;
        }, 1000);
    },
    
    clearCodeInput: function() {
        const codeInput = document.getElementById('rust-code');
        codeInput.value = '';
        this.updateCodeStats('');
        RustGreenUtils.showMessage('Code input cleared.', 'info');
    },
    
    // ==================== Responsive Behavior ====================
    
    initResponsiveBehavior: function() {
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
        setInterval(() => this.updateSessionStatuses(), RustGreenConfig.SESSION_STATUS_INTERVAL);
        
        document.querySelectorAll('.session-item').forEach(item => {
            item.addEventListener('click', () => {
                const sessionName = item.querySelector('.session-name').textContent;
                const status = item.querySelector('.session-status').textContent;
                RustGreenUtils.showMessage(`Session: ${sessionName} (${status}). Click "View All Sessions" for details.`, 'info');
            });
        });
        
        const viewAllBtn = document.querySelector('.view-all-btn');
        if (viewAllBtn) {
            viewAllBtn.addEventListener('click', () => {
                RustGreenUtils.showMessage('This would navigate to the full sessions page.', 'info');
            });
        }
    },
    
    updateSessionStatuses: function() {
        document.querySelectorAll('.session-status').forEach(statusEl => {
            if (Math.random() > 0.7) {
                const currentStatus = statusEl.textContent;
                const statusClasses = ['completed', 'in-progress', 'queued'];
                const statusTexts = ['Completed', 'In Progress', 'Queued'];
                
                const currentIndex = statusTexts.findIndex(text => currentStatus.includes(text));
                if (currentIndex !== -1) {
                    const newIndex = (currentIndex + 1) % statusClasses.length;
                    
                    statusClasses.forEach(cls => statusEl.classList.remove(cls));
                    statusEl.classList.add(statusClasses[newIndex]);
                    statusEl.textContent = statusTexts[newIndex];
                }
            }
        });
    },
    
    // ==================== Live Data Updates ====================
    
    updateLiveData: function() {
        this.updateActiveSessions();
        this.updatePerformanceMetrics();
        this.updateSystemStatus();
    },
    
    updateActiveSessions: function() {
        const sessionItems = document.querySelectorAll('.session-item');
        sessionItems.forEach(item => {
            const status = item.querySelector('.session-status');
            if (status.classList.contains('in-progress')) {
                const progressFill = item.querySelector('.progress-fill');
                if (progressFill) {
                    const currentWidth = parseInt(progressFill.style.width) || 75;
                    const newWidth = Math.min(currentWidth + Math.random() * 10, 100);
                    progressFill.style.width = `${newWidth}%`;
                    
                    const progressText = item.querySelector('.progress-text');
                    if (progressText) {
                        progressText.textContent = `${Math.round(newWidth)}% complete`;
                    }
                    
                    if (newWidth >= 100) {
                        status.classList.remove('in-progress');
                        status.classList.add('completed');
                        status.innerHTML = '<i class="fas fa-check-circle"></i> Completed';
                    }
                }
            }
        });
    },
    
    updatePerformanceMetrics: function() {
        const metrics = document.querySelectorAll('.metric-value');
        if (metrics.length >= 4) {
            let parseTime = parseFloat(metrics[0].textContent);
            parseTime = Math.max(1.5, parseTime + (Math.random() - 0.5) * 0.2);
            metrics[0].textContent = parseTime.toFixed(1) + 's';
            
            let accuracy = parseFloat(metrics[1].textContent);
            accuracy = Math.min(99, accuracy + (Math.random() * 0.5));
            metrics[1].textContent = Math.round(accuracy) + '%';
            
            let workers = parseInt(metrics[2].textContent);
            workers = Math.max(10, Math.min(25, workers + Math.floor(Math.random() * 3) - 1));
            metrics[2].textContent = workers;
            
            let uptime = parseFloat(metrics[3].textContent);
            uptime = Math.min(99.9, uptime + (Math.random() * 0.05));
            metrics[3].textContent = uptime.toFixed(1) + '%';
        }
    },
    
    updateSystemStatus: function() {
        const statusItems = document.querySelectorAll('.status-item');
        statusItems.forEach(item => {
            if (Math.random() > 0.7) {
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
    }
};

// Initialize the application when DOM is ready
document.addEventListener('DOMContentLoaded', () => RustGreenApp.init());

// Expose to global scope for debugging
if (typeof window !== 'undefined') {
    window.RustGreenApp = RustGreenApp;
}

console.log('rust-green modular JavaScript loaded successfully');