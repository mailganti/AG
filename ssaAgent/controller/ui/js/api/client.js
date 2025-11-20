// API client for making requests
class ApiClient {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }
            
            return data;
        } catch (error) {
            console.error(`API request failed: ${endpoint}`, error);
            throw error;
        }
    }

    // Workflows API
    async getWorkflows() {
        return this.request('/api/workflows');
    }

    async runWorkflow(id) {
        return this.request(`/api/workflows/${id}/run`, { method: 'POST' });
    }

    // Agents API
    async getAgents() {
        return this.request('/api/agents');
    }

    async registerAgent(agentData) {
        return this.request('/api/agents', {
            method: 'POST',
            body: JSON.stringify(agentData)
        });
    }

    async restartAgent(id) {
        return this.request(`/api/agents/${id}/restart`, { method: 'POST' });
    }
}

// Create global API client instance
const apiClient = new ApiClient();
