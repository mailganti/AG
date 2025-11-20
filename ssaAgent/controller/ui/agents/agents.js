// Agents module
async function loadAgents() {
    try {
        const result = await apiClient.getAgents();
        displayAgents(result.data);
    } catch (error) {
        console.error('Error loading agents:', error);
        displayError('agentTable', error.message);
    }
}

function displayAgents(agents) {
    const tableBody = document.querySelector('#agentTable tbody');
    
    if (agents.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; color: var(--text-muted);">
                    No agents found
                </td>
            </tr>
        `;
        return;
    }
    
    tableBody.innerHTML = agents.map(agent => `
        <tr>
            <td>${agent.id}</td>
            <td>${agent.name}</td>
            <td>
                <span class="${getStatusClass(agent.status)}">
                    ${getStatusIcon(agent.status)} ${agent.status}
                </span>
            </td>
            <td>${agent.workflows || 0}</td>
            <td>${formatDate(agent.last_active)}</td>
            <td>
                <button onclick="showAgentDetails('${agent.id}')">Details</button>
                <button onclick="restartAgent('${agent.id}')">Restart</button>
            </td>
        </tr>
    `).join('');
}

async function restartAgent(agentId) {
    try {
        await apiClient.restartAgent(agentId);
        alert(`Agent ${agentId} restarted successfully`);
        loadAgents(); // Refresh
    } catch (error) {
        alert('Error restarting agent: ' + error.message);
    }
}

function showAgentDetails(agentId) {
    alert(`Show details for agent: ${agentId}`);
}

// Load agents when module is loaded
loadAgents();