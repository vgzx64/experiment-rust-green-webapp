/**
 * rust-green Frontend Configuration
 */
const RustGreenConfig = {
    // API Configuration
    API_BASE_URL: 'http://localhost:8000/api/v1',
    
    // Polling Configuration
    POLLING_INTERVAL: 2000, // 2 seconds
    MAX_POLLING_TIME: 10 * 60 * 1000, // 10 minutes
    
    // UI Update Intervals
    LIVE_DATA_INTERVAL: 30000, // 30 seconds
    SESSION_STATUS_INTERVAL: 5000 // 5 seconds
};

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.RustGreenConfig = RustGreenConfig;
}