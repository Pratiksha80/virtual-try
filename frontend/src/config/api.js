// Frontend API configuration
export const API_CONFIG = {
    // Use environment variable or default to localhost
    BACKEND_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    // API endpoints
    ENDPOINTS: {
        TRYON: '/api/tryon',
        POSE_DETECT: '/api/pose-detect',
        PROGRESS: '/api/progress',
        WARP_CLOTHES: '/api/warp-clothes'
    },
    // Timeout in milliseconds
    TIMEOUT: 30000,
};

// Retry configuration
export const RETRY_CONFIG = {
    maxRetries: 3,
    retryDelay: 1000,
};