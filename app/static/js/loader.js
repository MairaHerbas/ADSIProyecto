const modules = [
    // CORRECCIÓN: Añadimos '/static/' al inicio de cada ruta
    { id: 'wrapper-tl', path: '/static/modules/top-left' },
    { id: 'wrapper-tr', path: '/static/modules/top-right' },
    { id: 'wrapper-bl', path: '/static/modules/bottom-left' },
    { id: 'wrapper-br', path: '/static/modules/bottom-right' },
    { id: 'wrapper-modal', path: '/static/modules/modal' }
];

async function loadModule(module) {
    const container = document.getElementById(module.id);
    if (!container) return;

    try {
        // 1. Cargar HTML
        const response = await fetch(`${module.path}/view.html`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const html = await response.text();
        container.innerHTML = html;

        // 2. Cargar CSS específico del módulo
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = `${module.path}/style.css`;
        document.head.appendChild(link);

        // 3. Cargar JS específico del módulo
        // Creamos un script dinámico para que se ejecute al insertarse
        const script = document.createElement('script');
        script.src = `${module.path}/logic.js`;
        script.type = 'module';
        // script.defer = true; // No necesario si es type module, pero mal no hace
        document.body.appendChild(script);

    } catch (error) {
        console.error(`Error cargando modulo ${module.id} desde ${module.path}:`, error);
    }
}

// Iniciar carga
modules.forEach(m => loadModule(m));