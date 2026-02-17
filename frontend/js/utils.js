/**
 * rust-green Utility Functions Module
 */
const RustGreenUtils = {
    /**
     * Count lines in code
     * @param {string} code - Source code
     * @returns {number} Line count
     */
    countLines: function(code) {
        return code.split('\n').length;
    },
    
    /**
     * Count unsafe blocks in Rust code
     * @param {string} code - Rust source code
     * @returns {number} Unsafe block count
     */
    countUnsafeBlocks: function(code) {
        const unsafeRegex = /\bunsafe\s*\{/g;
        const matches = code.match(unsafeRegex);
        return matches ? matches.length : 0;
    },
    
    /**
     * Escape HTML to prevent XSS
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    escapeHtml: function(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
    
    /**
     * Show a message notification
     * @param {string} message - Message to show
     * @param {string} type - Message type (success, warning, info, error)
     */
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
    
    /**
     * Get icon name for message type
     * @param {string} type - Message type
     * @returns {string} Font Awesome icon name
     */
    getIconForType: function(type) {
        const icons = {
            'success': 'check-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle',
            'error': 'times-circle'
        };
        return icons[type] || 'info-circle';
    },
    
    /**
     * Get color for message type
     * @param {string} type - Message type
     * @returns {string} CSS color
     */
    getColorForType: function(type) {
        const colors = {
            'success': '#38a169',
            'warning': '#d69e2e',
            'info': '#3182ce',
            'error': '#e53e3e'
        };
        return colors[type] || '#3182ce';
    },
    
    /**
     * Format code block type for display
     * @param {string} codeBlockType - Code block type
     * @returns {string} Formatted display text
     */
    formatCodeBlockType: function(codeBlockType) {
        const formatMap = {
            'replaceable': 'Replaceable',
            'non_replaceable': 'Non-Replaceable',
            'conditionally_replaceable': 'Conditionally Replaceable'
        };
        return formatMap[codeBlockType] || codeBlockType;
    },
    
    /**
     * Get finding title for code block type
     * @param {string} codeBlockType - Code block type
     * @returns {string} Finding title
     */
    getFindingTitle: function(codeBlockType) {
        const titleMap = {
            'replaceable': 'Replaceable Safety Issue',
            'non_replaceable': 'Non-Replaceable Pattern',
            'conditionally_replaceable': 'Conditionally Replaceable'
        };
        return titleMap[codeBlockType] || 'Code Analysis Finding';
    },
    
    /**
     * Get confidence text for analysis
     * @param {Object} analysis - Analysis object
     * @returns {string} Confidence text
     */
    getConfidenceText: function(analysis) {
        if (analysis.confidence_score) {
            return `${Math.round(analysis.confidence_score * 100)}% confidence`;
        }
        return "High confidence";
    }
};

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.RustGreenUtils = RustGreenUtils;
}