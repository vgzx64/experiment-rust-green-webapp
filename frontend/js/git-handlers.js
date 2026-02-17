/**
 * rust-green Git Handlers Module
 * Handles Git repository interactions
 */
const RustGreenGitHandlers = {
    // Git state
    state: {
        url: null,
        refs: null,
        selectedRef: null,
        files: [],
        selectedFiles: []
    },
    
    /**
     * Initialize Git handlers
     */
    init: function() {
        const gitUrlInput = document.getElementById('git-url');
        const fetchRefsBtn = document.getElementById('fetch-refs-btn');
        const gitRefSelect = document.getElementById('git-ref');
        const fetchFilesBtn = document.getElementById('fetch-files-btn');
        
        // Enable fetch button when URL is entered
        if (gitUrlInput) {
            gitUrlInput.addEventListener('input', () => {
                fetchRefsBtn.disabled = !gitUrlInput.value.trim();
            });
        }
        
        // Fetch refs button
        if (fetchRefsBtn) {
            fetchRefsBtn.addEventListener('click', () => this.fetchRefs());
        }
        
        // Ref selection change
        if (gitRefSelect) {
            gitRefSelect.addEventListener('change', () => {
                this.state.selectedRef = gitRefSelect.value;
                fetchFilesBtn.disabled = !gitRefSelect.value;
            });
        }
        
        // Fetch files button
        if (fetchFilesBtn) {
            fetchFilesBtn.addEventListener('click', () => this.fetchFiles());
        }
    },
    
    /**
     * Fetch Git refs (branches and tags)
     */
    fetchRefs: async function() {
        const gitUrlInput = document.getElementById('git-url');
        const gitRefSelect = document.getElementById('git-ref');
        const fetchRefsBtn = document.getElementById('fetch-refs-btn');
        const gitFilesSection = document.getElementById('git-files-section');
        
        const gitUrl = gitUrlInput.value.trim();
        if (!gitUrl) return;
        
        // Show loading state
        fetchRefsBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Fetching...';
        fetchRefsBtn.disabled = true;
        
        try {
            const response = await RustGreenAPI.getGitRefs(gitUrl);
            
            this.state.url = gitUrl;
            this.state.refs = response;
            
            // Populate select
            gitRefSelect.innerHTML = '<option value="">-- Select branch or tag --</option>';
            
            // Add branches
            if (response.branches && response.branches.length > 0) {
                const branchGroup = document.createElement('optgroup');
                branchGroup.label = 'Branches';
                response.branches.forEach(branch => {
                    const option = document.createElement('option');
                    option.value = branch;
                    option.textContent = `🌿 ${branch}`;
                    if (branch === response.default_branch) {
                        option.textContent += ' (default)';
                        option.selected = true;
                    }
                    branchGroup.appendChild(option);
                });
                gitRefSelect.appendChild(branchGroup);
            }
            
            // Add tags
            if (response.tags && response.tags.length > 0) {
                const tagGroup = document.createElement('optgroup');
                tagGroup.label = 'Tags';
                response.tags.forEach(tag => {
                    const option = document.createElement('option');
                    option.value = tag;
                    option.textContent = `🏷️ ${tag}`;
                    tagGroup.appendChild(option);
                });
                gitRefSelect.appendChild(tagGroup);
            }
            
            gitRefSelect.disabled = false;
            gitFilesSection.style.display = 'block';
            
            RustGreenUtils.showMessage(
                `Found ${response.branches.length} branches and ${response.tags.length} tags`,
                'success'
            );
            
        } catch (error) {
            RustGreenUtils.showMessage(`Failed to fetch refs: ${error.message}`, 'error');
        } finally {
            fetchRefsBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Fetch Refs';
            fetchRefsBtn.disabled = false;
        }
    },
    
    /**
     * Fetch Git files for selected ref
     */
    fetchFiles: async function() {
        const gitRefSelect = document.getElementById('git-ref');
        const fetchFilesBtn = document.getElementById('fetch-files-btn');
        const fileList = document.getElementById('git-file-list');
        
        const gitRef = gitRefSelect.value;
        if (!gitRef || !this.state.url) return;
        
        // Show loading state
        fetchFilesBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
        fetchFilesBtn.disabled = true;
        
        try {
            const response = await RustGreenAPI.getGitTree(this.state.url, gitRef);
            
            this.state.files = response.files;
            this.state.selectedRef = gitRef;
            
            // Populate file list
            fileList.innerHTML = '';
            
            if (response.files.length === 0) {
                fileList.innerHTML = '<p class="no-files">No Rust files found in repository</p>';
            } else {
                // Add select all checkbox
                const selectAllLabel = document.createElement('label');
                selectAllLabel.className = 'file-select-all';
                selectAllLabel.innerHTML = `
                    <input type="checkbox" id="select-all-files" checked />
                    <span>Select All (${response.files.length} files)</span>
                `;
                fileList.appendChild(selectAllLabel);
                
                // Add individual file checkboxes
                response.files.forEach(file => {
                    const fileLabel = document.createElement('label');
                    fileLabel.className = 'file-item';
                    fileLabel.innerHTML = `
                        <input type="checkbox" value="${file}" checked />
                        <i class="fas fa-file-code"></i>
                        <span>${file}</span>
                    `;
                    fileList.appendChild(fileLabel);
                });
                
                // Select all handler
                const selectAll = document.getElementById('select-all-files');
                if (selectAll) {
                    selectAll.addEventListener('change', (e) => {
                        fileList.querySelectorAll('.file-item input').forEach(cb => {
                            cb.checked = e.target.checked;
                        });
                    });
                }
            }
            
            RustGreenUtils.showMessage(`Found ${response.files.length} Rust files`, 'success');
            
        } catch (error) {
            RustGreenUtils.showMessage(`Failed to fetch files: ${error.message}`, 'error');
        } finally {
            fetchFilesBtn.innerHTML = '<i class="fas fa-list"></i> List Files';
            fetchFilesBtn.disabled = false;
        }
    },
    
    /**
     * Get selected files from the file list
     * @returns {string[]} Selected file paths
     */
    getSelectedFiles: function() {
        const fileList = document.getElementById('git-file-list');
        const checkboxes = fileList.querySelectorAll('.file-item input:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    },
    
    /**
     * Reset Git state
     */
    reset: function() {
        this.state = {
            url: null,
            refs: null,
            selectedRef: null,
            files: [],
            selectedFiles: []
        };
    }
};

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.RustGreenGitHandlers = RustGreenGitHandlers;
}