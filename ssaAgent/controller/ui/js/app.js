// Main application controller
class App {
    constructor() {
        this.currentView = 'dashboard';
        this.modules = new Map();
        this.init();
    }

    init() {
        // Load dashboard by default
        this.showView('dashboard');
        
        // Set up event listeners
        document.addEventListener('DOMContentLoaded', () => {
            this.setupTheme();
        });
    }

    async showView(viewId) {
        // Hide all views
        document.querySelectorAll('.view').forEach(view => {
            view.classList.remove('active');
        });
        
        // Update active tab
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.remove('active');
        });
        
        // Activate current tab
        const activeTab = [...document.querySelectorAll('.tab')].find(tab => 
            tab.getAttribute('onclick').includes(viewId)
        );
        if (activeTab) {
            activeTab.classList.add('active');
        }

        // Load and show the view
        await this.loadView(viewId);
        document.getElementById(viewId).classList.add('active');
        this.currentView = viewId;
    }

    async loadView(viewId) {
        const viewElement = document.getElementById(viewId);
        if (!viewElement) return;

        try {
            // Load HTML content
            const response = await fetch(`${viewId}/${viewId}.html`);
            if (!response.ok) throw new Error('Failed to load view');
            
            const html = await response.text();
            viewElement.innerHTML = html;

            // Load and execute JS module if it exists
            await this.loadModule(viewId);

        } catch (error) {
            console.error(`Error loading view ${viewId}:`, error);
            viewElement.innerHTML = `
                <div style="padding: 20px; text-align: center;">
                    <h2>⚠️ Error Loading ${viewId.replace('_', ' ').toUpperCase()}</h2>
                    <p>${error.message}</p>
                    <button onclick="app.showView('${viewId}')">Retry</button>
                </div>
            `;
        }
    }

    async loadModule(moduleName) {
        if (this.modules.has(moduleName)) return;

        try {
            const modulePath = `${moduleName}/${moduleName}.js`;
            const response = await fetch(modulePath);
            
            if (response.ok) {
                const moduleScript = await response.text();
                // Execute module script
                const executeModule = new Function(moduleScript);
                executeModule();
                this.modules.set(moduleName, true);
            }
        } catch (error) {
            console.warn(`No module found for ${moduleName} or failed to load:`, error);
        }
    }

    setupTheme() {
        const themePicker = document.getElementById('themePicker');
        if (themePicker) {
            themePicker.value = 'blue'; // Default theme
        }
    }
}

// Initialize app
const app = new App();

// Global functions for HTML onclick handlers
function showView(viewId) {
    app.showView(viewId);
}

function changeTheme(theme) {
    window.changeTheme(theme);
}
