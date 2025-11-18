// src/utils/api.js
const API_BASE_URL = 'http://localhost:8000/api';

export async function submitTryOn(formData) {
    try {
        // Submit the job
        const response = await fetch(`${API_BASE_URL}/tryon/link`, {
            method: 'POST',
            body: formData,
            // Remove timeout limitations
            signal: AbortSignal.timeout(600000) // 10 minutes
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        // If using job system
        if (data.job_id) {
            return await pollJobStatus(data.job_id);
        }
        
        return data;
    } catch (error) {
        console.error('Error:', error);
        throw error;
    }
}

async function pollJobStatus(jobId) {
    const maxAttempts = 120; // 10 minutes with 5-second intervals
    let attempts = 0;

    while (attempts < maxAttempts) {
        const response = await fetch(`${API_BASE_URL}/job/${jobId}`);
        const status = await response.json();

        if (status.status === 'completed') {
            return status.result;
        }
        if (status.status === 'failed') {
            throw new Error(status.error || 'Processing failed');
        }

        // Wait 5 seconds before next poll
        await new Promise(resolve => setTimeout(resolve, 5000));
        attempts++;
    }

    throw new Error('Operation timed out');
}