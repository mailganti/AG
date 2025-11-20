// Register Agent module
async function registerAgent() {
    const agentName = document.getElementById('agentName').value;
    const agentType = document.getElementById('agentType').value;
    const agentEndpoint = document.getElementById('agentEndpoint').value;
    
    if (!agentName || !agentType || !agentEndpoint) {
        alert('Please fill in all required fields');
        return;
    }
    
    try {
        const agentData = {
            name: agentName,
            type: agentType,
            endpoint: agentEndpoint,
            description: document.getElementById('agentDescription').value
        };
        
        await apiClient.registerAgent(agentData);
        alert(`Agent "${agentName}" registered successfully!`);
        
        // Clear form and redirect to agents view
        clearForm();
        showView('agents');
        
    } catch (error) {
        alert('Error registering agent: ' + error.message);
    }
}

function clearForm() {
    document.getElementById('agentName').value = '';
    document.getElementById('agentType').value = '';
    document.getElementById('agentEndpoint').value = '';
    document.getElementById('agentDescription').value = '';
}