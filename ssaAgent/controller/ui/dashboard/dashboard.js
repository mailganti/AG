// Dashboard module
async function refreshDashboard() {
    try {
        const [workflows, agents] = await Promise.all([
            apiClient.getWorkflows(),
            apiClient.getAgents()
        ]);

        updateDashboardKPIs(workflows.data, agents.data);
        updateRecentActivity(workflows.data, agents.data);
    } catch (error) {
        console.error('Error refreshing dashboard:', error);
    }
}

function updateDashboardKPIs(workflows, agents) {
    const activeWorkflows = workflows.filter(w => w.status === 'ACTIVE').length;
    const runningAgents = agents.filter(a => a.status === 'ONLINE').length;
    
    document.getElementById('activeWorkflowsCount').textContent = activeWorkflows;
    document.getElementById('runningAgentsCount').textContent = runningAgents;
    document.getElementById('tasksCompletedCount').textContent = '1,245'; // Mock data
    document.getElementById('successRate').textContent = '98.2%'; // Mock data
}

function updateRecentActivity(workflows, agents) {
    const activityList = document.getElementById('activityList');
    const activities = [
        ...workflows.slice(0, 3).map(wf => 
            `Workflow "${wf.name}" is ${wf.status.toLowerCase()}`
        ),
        ...agents.slice(0, 2).map(agent => 
            `Agent "${agent.name}" is ${agent.status.toLowerCase()}`
        )
    ];
    
    activityList.innerHTML = activities
        .map(activity => `<div class="activity-item">${activity}</div>`)
        .join('');
}

// Initialize dashboard when loaded
refreshDashboard();