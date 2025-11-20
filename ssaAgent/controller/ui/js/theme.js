// Theme management
function changeTheme(theme) {
    const root = document.documentElement;
    
    switch(theme) {
        case 'purple':
            root.style.setProperty('--primary', '#a855f7');
            root.style.setProperty('--primary-dark', '#9333ea');
            break;
        case 'green':
            root.style.setProperty('--primary', '#10b981');
            root.style.setProperty('--primary-dark', '#059669');
            break;
        case 'orange':
            root.style.setProperty('--primary', '#f97316');
            root.style.setProperty('--primary-dark', '#ea580c');
            break;
        default: // Blue theme
            root.style.setProperty('--primary', '#38bdf8');
            root.style.setProperty('--primary-dark', '#0ea5e9');
    }
}