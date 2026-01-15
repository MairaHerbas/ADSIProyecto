const modules = [
    { id: 'wrapper-tl', path: 'modules/top-left' },
    { id: 'wrapper-tr', path: 'modules/top-right' },
    { id: 'wrapper-bl', path: 'modules/bottom-left' },
    { id: 'wrapper-br', path: 'modules/bottom-right' },
    // AÑADE ESTO:
    { id: 'wrapper-modal', path: 'modules/modal' }
];

async function loadModule(module) {
    const container = document.getElementById(module.id);
    if (!container) return;

    try {
        // 1. Cargar HTML
        const response = await fetch(`${module.path}/view.html`);
        const html = await response.text();
        container.innerHTML = html;

        // 2. Cargar CSS específico del módulo
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = `${module.path}/style.css`;
        document.head.appendChild(link);

        // 3. Cargar JS específico del módulo
        const script = document.createElement('script');
        script.src = `${module.path}/logic.js`;
        script.type = 'module';
        script.defer = true;
        document.body.appendChild(script);

    } catch (error) {
        console.error(`Error cargando modulo ${module.id}:`, error);
    }
}

// Iniciar carga
modules.forEach(m => loadModule(m));