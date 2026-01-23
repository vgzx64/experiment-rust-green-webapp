// Sessions page JavaScript for rust-green
(function() {
    'use strict';
    
    // Configuration
    const API_BASE_URL = 'http://localhost:8000/api/v1';
    const SESSIONS_PER_PAGE = 10;
    
    // Application state
    const SessionsApp = {
        currentPage: 1,
        totalPages: 1,
        totalSessions: 0,
        allSessions: [],
        filteredSessions: [],
        currentFilter: 'all',
        currentSort: 'newest',
        
        // Initialize the application
        init: function() {
            console.log('Sessions page loaded');
            
            // Initialize event listeners
            this.initEventListeners();
            
            // Load sessions
            this.loadSessions();
            
            // Update stats
            this.updateStats();
        },
        
        // Initialize event listeners
        initEventListeners: function() {
            // Filter controls
            const statusFilter = document.getElementById('status-filter');
            const sortBy = document.getElementById('sort-by');
            const refreshBtn = document.getElementById('refresh-btn');
            const prevPageBtn = document.getElementById('prev-page');
            const nextPageBtn = document.getElementById('next-page');
            
            if (statusFilter) {
                statusFilter.addEventListener('change', (e) => {
                    this.currentFilter = e.target.value;
                    this.applyFilters();
                });
            }
            
            if (sortBy) {
                sortBy.addEventListener('change', (e) => {
                    this.currentSort = e.target.value;
                    this.applySorting();
                });
            }
            
            if (refreshBtn) {
                refreshBtn.addEventListener('click', () => {
                    this.loadSessions();
                });
            }
            
            if (prevPageBtn) {
                prevPageBtn.addEventListener('click', () => {
                    if (this.currentPage > 1) {
                        this.currentPage--;
                        this.renderSessions();
                    }
                });
            }
            
            if (nextPageBtn) {
                nextPageBtn.addEventListener('click', () => {
                    if (this.currentPage < this.totalPages) {
                        this.currentPage++;
                        this.renderSessions();
                    }
                });
            }
            
            // Modal close button
            const modalClose = document.getElementById('modal-close');
            const sessionModal = document.getElementById('session-modal');
            
            if (modalClose && sessionModal) {
                modalClose.addEventListener('click', () => {
                    sessionModal.style.display = 'none';
                });
                
                // Close modal when clicking outside
                sessionModal.addEventListener('click', (e) => {
                    if (e.target === sessionModal) {
                        sessionModal.style.display = 'none';
                    }
                });
            }
        },
        
        // Load sessions from API
        loadSessions: function() {
            const loadingMessage = document.querySelector('.loading-message');
            const sessionsList = document.getElementById('sessions-list');
            const noSessionsMessage = document.getElementById('no-sessions-message');
            
            // Show loading state
            if (loadingMessage) {
                loadingMessage.style.display = 'block';
            }
            if (noSessionsMessage) {
                noSessionsMessage.style.display = 'none';
            }
            if (sessionsList) {
                sessionsList.innerHTML = '<div class="loading-message"><i class="fas fa-spinner fa-spin"></i><p>Loading sessions...</p></div>';
            }
            
            // Make API request
            this.apiRequest('/sessions?limit=1000')
                .then(sessions => {
                    this.allSessions = sessions;
                    this.filteredSessions = [...sessions];
                    
                    // Apply initial filters and sorting
                    this.applyFilters();
                    this.applySorting();
                    
                    // Update pagination
                    this.updatePagination();
                    
                    // Render sessions
                    this.renderSessions();
                    
                    // Update stats
                    this.updateStats();
                    
                    // Hide loading message if no sessions
                    if (sessions.length === 0) {
                        if (noSessionsMessage) {
                            noSessionsMessage.style.display = 'block';
                        }
                        if (sessionsList) {
                            sessionsList.innerHTML = '';
                        }
                    }
                })
                .catch(error => {
                    console.error('Failed to load sessions:', error);
                    this.showMessage(`Failed to load sessions: ${error.message}`, 'error');
                    
                    // Show error state
                    if (sessionsList) {
                        sessionsList.innerHTML = `
                            <div class="error-message">
                                <i class="fas fa-exclamation-triangle"></i>
                                <p>Failed to load sessions. Please try again.</p>
                            </div>
                        `;
                    }
                })
                .finally(() => {
                    if (loadingMessage) {
                        loadingMessage.style.display = 'none';
                    }
                });
        },
        
        // Apply filters based on current filter state
        applyFilters: function() {
            if (this.currentFilter === 'all') {
                this.filteredSessions = [...this.allSessions];
            } else {
                this.filteredSessions = this.allSessions.filter(session => 
                    session.status.toLowerCase() === this.currentFilter
                );
            }
            
            // Reset to first page after filtering
            this.currentPage = 1;
            this.applySorting();
        },
        
        // Apply sorting based on current sort state
        applySorting: function() {
            switch (this.currentSort) {
                case 'newest':
                    this.filteredSessions.sort((a, b) => 
                        new Date(b.created_at) - new Date(a.created_at)
                    );
                    break;
                case 'oldest':
                    this.filteredSessions.sort((a, b) => 
                        new Date(a.created_at) - new Date(b.created_at)
                    );
                    break;
                case 'status':
                    this.filteredSessions.sort((a, b) => {
                        const statusOrder = {
                            'processing': 0,
                            'pending': 1,
                            'completed': 2,
                            'failed': 3
                        };
                        return statusOrder[a.status] - statusOrder[b.status];
                    });
                    break;
            }
            
            this.updatePagination();
            this.renderSessions();
        },
        
        // Update pagination controls
        updatePagination: function() {
            this.totalSessions = this.filteredSessions.length;
            this.totalPages = Math.ceil(this.totalSessions / SESSIONS_PER_PAGE) || 1;
            
            // Update page info
            const currentPageEl = document.getElementById('current-page');
            const totalPagesEl = document.getElementById('total-pages');
            const prevPageBtn = document.getElementById('prev-page');
            const nextPageBtn = document.getElementById('next-page');
            
            if (currentPageEl) {
                currentPageEl.textContent = this.currentPage;
            }
            if (totalPagesEl) {
                totalPagesEl.textContent = this.totalPages;
            }
            if (prevPageBtn) {
                prevPageBtn.disabled = this.currentPage <= 1;
            }
            if (nextPageBtn) {
                nextPageBtn.disabled = this.currentPage >= this.totalPages;
            }
        },
        
        // Render sessions for current page
        renderSessions: function() {
            const sessionsList = document.getElementById('sessions-list');
            if (!sessionsList) return;
            
            // Calculate start and end indices for current page
            const startIndex = (this.currentPage - 1) * SESSIONS_PER_PAGE;
            const endIndex = Math.min(startIndex + SESSIONS_PER_PAGE, this.filteredSessions.length);
            const pageSessions = this.filteredSessions.slice(startIndex, endIndex);
            
            if (pageSessions.length === 0) {
                sessionsList.innerHTML = `
                    <div class="no-sessions-message">
                        <i class="fas fa-inbox"></i>
                        <h4>No Sessions Found</h4>
                        <p>No sessions match your current filters.</p>
                    </div>
                `;
                return;
            }
            
            // Create session items
            sessionsList.innerHTML = '';
            pageSessions.forEach(session => {
                const sessionItem = this.createSessionItem(session);
                sessionsList.appendChild(sessionItem);
            });
        },
        
        // Create a session list item
        createSessionItem: function(session) {
            const item = document.createElement('div');
            item.className = 'session-list-item';
            item.dataset.sessionId = session.id;
            
            // Format dates
            const createdDate = new Date(session.created_at);
            const createdStr = createdDate.toLocaleDateString() + ' ' + createdDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            
            const completedStr = session.completed_at 
                ? new Date(session.completed_at).toLocaleDateString() + ' ' + new Date(session.completed_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
                : 'N/A';
            
            // Determine status class and icon
            let statusClass = session.status.toLowerCase();
            let statusIcon = 'fa-clock';
            if (session.status === 'completed') statusIcon = 'fa-check-circle';
            if (session.status === 'failed') statusIcon = 'fa-times-circle';
            if (session.status === 'processing') statusIcon = 'fa-sync-alt fa-spin';
            
            // Truncate session ID for display
            const shortId = session.id.substring(0, 8) + '...';
            
            item.innerHTML = `
                <div class="session-item-content">
                    <div class="session-item-main">
                        <div class="session-item-header">
                            <span class="session-id">
                                <i class="fas fa-fingerprint"></i> ${shortId}
                            </span>
                            <span class="session-status ${statusClass}">
                                <i class="fas ${statusIcon}"></i> ${session.status.charAt(0).toUpperCase() + session.status.slice(1)}
                            </span>
                        </div>
                        
                        <div class="session-item-details">
                            <div class="session-detail">
                                <span class="detail-label"><i class="fas fa-calendar-plus"></i> Created:</span>
                                <span class="detail-value">${createdStr}</span>
                            </div>
                            <div class="session-detail">
                                <span class="detail-label"><i class="fas fa-calendar-check"></i> Completed:</span>
                                <span class="detail-value">${completedStr}</span>
                            </div>
                            <div class="session-detail">
                                <span class="detail-label"><i class="fas fa-chart-bar"></i> Progress:</span>
                                <span class="detail-value">
                                    <span class="progress-bar-small">
                                        <span class="progress-fill" style="width: ${session.progress}%"></span>
                                    </span>
                                    ${session.progress}%
                                </span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="session-item-stats">
                        <div class="session-stat">
                            <span class="stat-value">${session.analysis_count}</span>
                            <span class="stat-label">Analyses</span>
                        </div>
                        ${session.error_message ? `
                        <div class="session-error">
                            <i class="fas fa-exclamation-triangle"></i>
                            <span class="error-text">${this.escapeHtml(session.error_message.substring(0, 50))}${session.error_message.length > 50 ? '...' : ''}</span>
                        </div>
                        ` : ''}
                    </div>
                </div>
                
                <div class="session-item-actions">
                    <button class="action-btn view-details" data-session-id="${session.id}">
                        <i class="fas fa-eye"></i> View Details
                    </button>
                    <button class="action-btn copy-id" data-session-id="${session.id}">
                        <i class="fas fa-copy"></i> Copy ID
                    </button>
                </div>
            `;
            
            // Add event listeners
            const viewDetailsBtn = item.querySelector('.view-details');
            const copyIdBtn = item.querySelector('.copy-id');
            
            if (viewDetailsBtn) {
                viewDetailsBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.viewSessionDetails(session.id);
                });
            }
            
            if (copyIdBtn) {
                copyIdBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.copySessionId(session.id);
                });
            }
            
            // Make the whole item clickable
            item.addEventListener('click', (e) => {
                if (!e.target.closest('.action-btn')) {
                    this.viewSessionDetails(session.id);
                }
            });
            
            return item;
        },
        
        // View session details (navigate to session detail page)
        viewSessionDetails: function(sessionId) {
            // Navigate to session detail page with session ID in URL
            window.location.href = `session-detail.html?id=${sessionId}`;
        },
        
        // Copy session ID to clipboard
        copySessionId: function(sessionId) {
            navigator.clipboard.writeText(sessionId)
                .then(() => {
                    this.showMessage('Session ID copied to clipboard', 'success');
                })
                .catch(err => {
                    console.error('Failed to copy session ID:', err);
                    this.showMessage('Failed to copy session ID', 'error');
                });
        },
        
        // Update statistics summary
        updateStats: function() {
            const totalSessionsEl = document.getElementById('total-sessions');
            const completedSessionsEl = document.getElementById('completed-sessions');
            const processingSessionsEl = document.getElementById('processing-sessions');
            
            if (!totalSessionsEl || !completedSessionsEl || !processingSessionsEl) return;
            
            const completedCount = this.allSessions.filter(s => s.status === 'completed').length;
            const processingCount = this.allSessions.filter(s => s.status === 'processing').length;
            
            totalSessionsEl.textContent = this.allSessions.length;
            completedSessionsEl.textContent = completedCount;
            processingSessionsEl.textContent = processingCount;
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
        
        // Utility functions
        escapeHtml: function(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
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
    document.addEventListener('DOMContentLoaded', () => SessionsApp.init());
    
    // Expose to global scope for debugging
    window.SessionsApp = SessionsApp;
    
    console.log('Sessions page JavaScript loaded successfully');
})();
