// Workflows module
async function loadWorkflows() {
    try {
        const result = await apiClient.getWorkflows();
        displayWorkflows(result.data);
    } catch (error) {
        console.error('Error loading workflows:', error);
        displayError('wfTable', error.message);
    }
}

function displayWorkflows(workflows) {
    const tableBody = document.querySelector('#wfTable tbody');
    
    if (workflows.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center; color: var(--text-muted);">
                    No workflows found
                </td>
            </tr>
        `;
        return;
    }
    
    tableBody.innerHTML = workflows.map(workflow => `
        <tr>
            <td>${workflow.id}</td>
            <td>${workflow.name}</td>
            <td>
                <span class="${getStatusClass(workflow.status)}">
                    ${getStatusIcon(workflow.status)} ${workflow.status}
                </span>
            </td>
            <td>${formatDate(workflow.last_run)}</td>
            <td>
                <button onclick="editWorkflow('${workflow.id}')">Edit</button>
                <button onclick="runWorkflow('${workflow.id}')">Run</button>
                ${workflow.status === 'RUNNING' ? 
                    '<button onclick="stopWorkflow(\'' + workflow.id + '\')">Stop</button>' : ''}
            </td>
        </tr>
    `).join('');
}

async function runWorkflow(workflowId) {
    try {
        await apiClient.runWorkflow(workflowId);
        alert(`Workflow ${workflowId} started successfully`);
        loadWorkflows(); // Refresh
    } catch (error) {
        alert('Error running workflow: ' + error.message);
    }
}

function editWorkflow(workflowId) {
    alert(`Edit workflow: ${workflowId}`);
}

function stopWorkflow(workflowId) {
    alert(`Stop workflow: ${workflowId}`);
}

function displayError(tableId, message) {
    const tableBody = document.querySelector(`#${tableId} tbody`);
    tableBody.innerHTML = `
        <tr>
            <td colspan="5" style="text-align: center; color: var(--text-muted);">
                Error: ${message}
            </td>
        </tr>
    `;
}

// Load workflows when module is loaded
loadWorkflows();
