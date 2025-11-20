// Shared utility functions
function getStatusIcon(status) {
    const statusIcons = {
        'ONLINE': '🟢',
        'OFFLINE': '🔴',
        'RUNNING': '⏳',
        'ACTIVE': '✅',
        'ERROR': '❌',
        'IDLE': '⚪'
    };
    return statusIcons[status] || '⚪';
}

function getStatusClass(status) {
    const statusClasses = {
        'ONLINE': 'status-online',
        'OFFLINE': 'status-offline',
        'RUNNING': 'status-running',
        'ACTIVE': 'status-active',
        'ERROR': 'status-offline'
    };
    return statusClasses[status] || '';
}

function formatDate(dateString) {
    if (!dateString) return 'Never';
    try {
        const date = new Date(dateString);
        return date.toLocaleString();
    } catch (e) {
        return 'Invalid Date';
    }
}