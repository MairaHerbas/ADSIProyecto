(async function() {
    console.log("Iniciando Módulo Top-Left...");

    const usernameEl = document.getElementById('tl-username');
    const statsEl = document.getElementById('tl-stats');
    const avatarEl = document.getElementById('tl-avatar');
    const avatarContainer = document.querySelector('.tl-avatar-container');
    
    let currentData = null; // Guardamos datos locales para pasarlos al modal

    // --- FUNCIÓN DE ACTUALIZACIÓN ---
    async function updateProfileView() {
        try {
            const response = await fetch('/api/user-info');
            if (!response.ok) throw new Error('Error API');
            
            const data = await response.json();
            currentData = data; // Actualizar cache local

            usernameEl.textContent = data.username;
            statsEl.textContent = data.stats;
            
            if (data.avatar_url) {
                // Truco para forzar recarga de imagen si la URL es la misma pero la imagen cambió
                // (opcional, pero útil si cambias el avatar)
                avatarEl.src = data.avatar_url; 
            }

        } catch (error) {
            console.error("Error Top-Left:", error);
            usernameEl.textContent = "Error";
        }
    }

    // 1. Carga Inicial
    await updateProfileView();

    // 2. Evento Click (Abre Modal)
    const openProfile = () => {
        if (window.ModalSystem) {
            // Pasamos currentData actualizado
            window.ModalSystem.open('profile', currentData);
        }
    };
    if (avatarContainer) avatarContainer.addEventListener('click', openProfile);
    if (usernameEl) usernameEl.addEventListener('click', openProfile);

    // 3. NUEVO: ESCUCHAR ACTUALIZACIÓN GLOBAL
    window.addEventListener('app-data-refresh', () => {
        console.log("Refrescando Perfil...");
        updateProfileView();
    });

})();