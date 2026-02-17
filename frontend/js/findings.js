/**
 * rust-green Findings Module
 * Handles displaying analysis findings
 */
const RustGreenFindings = {
    /**
     * Display findings in the container
     * @param {Object[]} analyses - Analysis results
     * @param {string} sessionId - Current session ID
     */
    display: function(analyses, sessionId) {
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
            const findingCard = this.createCard(analysis, sessionId);
            findingsContainer.prepend(findingCard);
        });
    },
    
    /**
     * Create a finding card element
     * @param {Object} analysis - Analysis data
     * @param {string} sessionId - Session ID
     * @returns {HTMLElement} Finding card element
     */
    createCard: function(analysis, sessionId) {
        const codeBlockType = analysis.code_block_type;
        const typeClass = codeBlockType.replace('_', '-');
        const typeDisplayText = RustGreenUtils.formatCodeBlockType(codeBlockType);
        
        // Extract code snippets
        const unsafeCode = analysis.code_block?.raw_code || 'No code available';
        const safeCode = analysis.suggested_replacement?.raw_code || null;
        const diffCode = analysis.diff || null;
        
        // Extract security metadata
        const cweId = analysis.cwe_id;
        const owaspCategory = analysis.owasp_category;
        const riskLevel = analysis.risk_level;
        const confidenceScore = analysis.confidence_score;
        const vulnerabilityDescription = analysis.vulnerability_description;
        const exploitationScenario = analysis.exploitation_scenario;
        const remediationExplanation = analysis.remediation_explanation;
        
        const card = document.createElement('div');
        card.className = `finding-card ${typeClass}`;
        card.innerHTML = `
            <div class="finding-header">
                <span class="finding-badge ${typeClass}">${typeDisplayText}</span>
                <span class="finding-title">${RustGreenUtils.getFindingTitle(codeBlockType)}</span>
                <span class="finding-confidence">${RustGreenUtils.getConfidenceText(analysis)}</span>
            </div>
            
            <!-- Security Metadata -->
            <div class="security-metadata">
                ${cweId ? `<span class="security-badge cwe"><i class="fas fa-bug"></i> ${cweId}</span>` : ''}
                ${owaspCategory ? `<span class="security-badge owasp"><i class="fas fa-shield-alt"></i> ${owaspCategory}</span>` : ''}
                ${riskLevel ? `<span class="security-badge risk-${riskLevel.toLowerCase()}"><i class="fas fa-exclamation-triangle"></i> ${riskLevel.toUpperCase()}</span>` : ''}
                ${confidenceScore ? `<span class="security-badge confidence"><i class="fas fa-chart-line"></i> ${Math.round(confidenceScore * 100)}% confidence</span>` : ''}
            </div>
            
            <div class="finding-content">
                ${vulnerabilityDescription ? `
                <div class="description-section">
                    <div class="section-label"><i class="fas fa-info-circle"></i> Vulnerability Description</div>
                    <div class="section-content">${RustGreenUtils.escapeHtml(vulnerabilityDescription)}</div>
                </div>
                ` : ''}
                
                ${exploitationScenario ? `
                <div class="description-section">
                    <div class="section-label"><i class="fas fa-bolt"></i> Exploitation Scenario</div>
                    <div class="section-content">${RustGreenUtils.escapeHtml(exploitationScenario)}</div>
                </div>
                ` : ''}
                
                ${diffCode ? `
                <div class="code-block diff">
                    <div class="code-label"><i class="fas fa-exchange-alt"></i> Diff (Changes)</div>
                    <pre><code>${RustGreenUtils.escapeHtml(diffCode)}</code></pre>
                </div>
                ` : ''}
                
                <div class="code-block">
                    <div class="code-label"><i class="fas fa-code"></i> Unsafe Code (Lines ${analysis.code_block?.line_start || 1}-${analysis.code_block?.line_end || 1})</div>
                    <pre><code>${RustGreenUtils.escapeHtml(unsafeCode)}</code></pre>
                </div>
                
                ${safeCode ? `
                <div class="code-block safe">
                    <div class="code-label"><i class="fas fa-check-circle"></i> Safe Alternative</div>
                    <pre><code>${RustGreenUtils.escapeHtml(safeCode)}</code></pre>
                </div>
                ` : ''}
                
                ${remediationExplanation ? `
                <div class="description-section">
                    <div class="section-label"><i class="fas fa-wrench"></i> Remediation Explanation</div>
                    <div class="section-content">${RustGreenUtils.escapeHtml(remediationExplanation)}</div>
                </div>
                ` : ''}
            </div>

            <div class="finding-actions">
                ${safeCode ? `
                <button class="action-btn download-fixed" data-session-id="${sessionId}">
                    <i class="fas fa-file-archive"></i> Download Fixed Code
                </button>
                <button class="action-btn download-patches" data-session-id="${sessionId}">
                    <i class="fas fa-file-code"></i> Download Patches
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
        this.addCardEventListeners(card, analysis, sessionId);
        
        return card;
    },
    
    /**
     * Add event listeners to a finding card
     * @param {HTMLElement} card - Card element
     * @param {Object} analysis - Analysis data
     * @param {string} sessionId - Session ID
     */
    addCardEventListeners: function(card, analysis, sessionId) {
        // Download buttons
        const downloadFixedBtn = card.querySelector('.action-btn.download-fixed');
        if (downloadFixedBtn) {
            downloadFixedBtn.addEventListener('click', () => this.downloadFixed(sessionId));
        }
        
        const downloadPatchesBtn = card.querySelector('.action-btn.download-patches');
        if (downloadPatchesBtn) {
            downloadPatchesBtn.addEventListener('click', () => this.downloadPatches(sessionId));
        }
        
        // False positive button
        const falsePositiveBtn = card.querySelector('.action-btn.false-positive');
        if (falsePositiveBtn) {
            falsePositiveBtn.addEventListener('click', () => this.markAsFalsePositive(analysis.id));
        }
        
        // Note button
        const noteBtn = card.querySelector('.action-btn.note');
        if (noteBtn) {
            noteBtn.addEventListener('click', () => this.addNote(analysis.id));
        }
        
        // Details button
        const detailsBtn = card.querySelector('.action-btn.details');
        if (detailsBtn) {
            detailsBtn.addEventListener('click', () => this.showDetails(analysis));
        }
    },
    
    /**
     * Download fixed files
     * @param {string} sessionId - Session ID
     */
    downloadFixed: function(sessionId) {
        if (!sessionId) {
            RustGreenUtils.showMessage('No session ID available for download', 'error');
            return;
        }
        window.open(RustGreenAPI.getDownloadFixedUrl(sessionId), '_blank');
        RustGreenUtils.showMessage('Downloading fixed code ZIP...', 'info');
    },
    
    /**
     * Download patches
     * @param {string} sessionId - Session ID
     */
    downloadPatches: function(sessionId) {
        if (!sessionId) {
            RustGreenUtils.showMessage('No session ID available for download', 'error');
            return;
        }
        window.open(RustGreenAPI.getDownloadPatchesUrl(sessionId), '_blank');
        RustGreenUtils.showMessage('Downloading patches ZIP...', 'info');
    },
    
    /**
     * Mark analysis as false positive
     * @param {string} analysisId - Analysis ID
     */
    markAsFalsePositive: function(analysisId) {
        RustGreenUtils.showMessage(`Marked analysis ${analysisId.substring(0, 8)} as false positive.`, 'info');
    },
    
    /**
     * Add note to analysis
     * @param {string} analysisId - Analysis ID
     */
    addNote: function(analysisId) {
        const note = prompt(`Add a note for analysis ${analysisId.substring(0, 8)}:\n\nYour note:`, '');
        if (note) {
            RustGreenUtils.showMessage(`Note added to analysis ${analysisId.substring(0, 8)}: "${note}"`, 'success');
        }
    },
    
    /**
     * Show analysis details
     * @param {Object} analysis - Analysis data
     */
    showDetails: function(analysis) {
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
    
    /**
     * Update results summary
     * @param {Object[]} analyses - Analysis results
     */
    updateSummary: function(analyses) {
        const summaryItems = document.querySelectorAll('.summary-item');
        if (summaryItems.length < 4) return;
        
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
        if (totalElement) totalElement.textContent = totalIssues;
        
        // Update replaceable count
        const replaceableElement = summaryItems[1].querySelector('.summary-value');
        if (replaceableElement) {
            replaceableElement.textContent = replaceableCount;
            replaceableElement.parentElement.classList.toggle('has-issues', replaceableCount > 0);
        }
        
        // Update non-replaceable count
        const nonReplaceableElement = summaryItems[2].querySelector('.summary-value');
        if (nonReplaceableElement) nonReplaceableElement.textContent = nonReplaceableCount;
        
        // Update conditionally replaceable count
        const conditionallyReplaceableElement = summaryItems[3].querySelector('.summary-value');
        if (conditionallyReplaceableElement) {
            conditionallyReplaceableElement.textContent = conditionallyReplaceableCount;
        }
    }
};

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.RustGreenFindings = RustGreenFindings;
}