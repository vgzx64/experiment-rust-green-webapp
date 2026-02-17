/**
 * rust-green API Service Module
 * Handles all API communication with the backend
 */
const RustGreenAPI = {
    /**
     * Make an API request
     * @param {string} endpoint - API endpoint (without base URL)
     * @param {Object} options - Fetch options
     * @returns {Promise<Object>} Response data
     */
    request: async function(endpoint, options = {}) {
        const url = `${RustGreenConfig.API_BASE_URL}${endpoint}`;
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
    
    // ==================== Session Endpoints ====================
    
    /**
     * Create a new analysis session with code
     * @param {string} code - Rust code to analyze
     * @returns {Promise<Object>} Session data
     */
    createSession: async function(code) {
        return this.request('/sessions', {
            method: 'POST',
            body: JSON.stringify({ code })
        });
    },
    
    /**
     * Create a new Git analysis session
     * @param {string} origLocation - Git repository URL
     * @param {string} gitRef - Branch or tag
     * @param {string[]} selectedFiles - Files to analyze
     * @returns {Promise<Object>} Session data
     */
    createGitSession: async function(origLocation, gitRef, selectedFiles) {
        return this.request('/sessions', {
            method: 'POST',
            body: JSON.stringify({
                orig_location: origLocation,
                git_ref: gitRef,
                selected_files: selectedFiles
            })
        });
    },
    
    /**
     * Get session status
     * @param {string} sessionId - Session ID
     * @returns {Promise<Object>} Status data
     */
    getSessionStatus: async function(sessionId) {
        return this.request(`/sessions/${sessionId}/status`);
    },
    
    /**
     * Get full session data with analyses
     * @param {string} sessionId - Session ID
     * @returns {Promise<Object>} Session data
     */
    getSession: async function(sessionId) {
        return this.request(`/sessions/${sessionId}`);
    },
    
    /**
     * List sessions
     * @param {number} skip - Number to skip
     * @param {number} limit - Max number to return
     * @param {string} statusFilter - Filter by status
     * @returns {Promise<Object[]>} Session list
     */
    listSessions: async function(skip = 0, limit = 100, statusFilter = null) {
        let url = `/sessions?skip=${skip}&limit=${limit}`;
        if (statusFilter) {
            url += `&status_filter=${statusFilter}`;
        }
        return this.request(url);
    },
    
    // ==================== Repository Endpoints ====================
    
    /**
     * Fetch Git refs (branches and tags)
     * @param {string} gitUrl - Git repository URL
     * @returns {Promise<Object>} Refs data
     */
    getGitRefs: async function(gitUrl) {
        return this.request(`/repos/refs?git_url=${encodeURIComponent(gitUrl)}`);
    },
    
    /**
     * Fetch Git tree (file list)
     * @param {string} gitUrl - Git repository URL
     * @param {string} gitRef - Branch or tag
     * @returns {Promise<Object>} Tree data
     */
    getGitTree: async function(gitUrl, gitRef) {
        return this.request(`/repos/tree?git_url=${encodeURIComponent(gitUrl)}&git_ref=${encodeURIComponent(gitRef)}`);
    },
    
    // ==================== Download Endpoints ====================
    
    /**
     * Get download URL for fixed files
     * @param {string} sessionId - Session ID
     * @returns {string} Download URL
     */
    getDownloadFixedUrl: function(sessionId) {
        return `${RustGreenConfig.API_BASE_URL}/sessions/${sessionId}/download/fixed`;
    },
    
    /**
     * Get download URL for patches
     * @param {string} sessionId - Session ID
     * @returns {string} Download URL
     */
    getDownloadPatchesUrl: function(sessionId) {
        return `${RustGreenConfig.API_BASE_URL}/sessions/${sessionId}/download/patches`;
    }
};

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.RustGreenAPI = RustGreenAPI;
}