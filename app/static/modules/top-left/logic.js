(async function() {
    console.log("Cargando Top-Left (Modo Simple)...");

    try {
        const res = await fetch('/api/user-info');
        if (!res.ok) return;

        const user = await res.json();

        // 1. Rellenar Textos (Nombre Real y Nick)
        const realNameEl = document.getElementById('tl-realname');
        const userNameEl = document.getElementById('tl-username');
        const avatarEl = document.getElementById('tl-avatar-img');

        // Usamos los datos que vienen del backend
        // Nota: Asegúrate de que /api/user-info devuelve 'name' también.
        // Si no, mostrará el username en ambos sitios temporalmente.
        if(realNameEl) realNameEl.textContent = user.name || user.username;
        if(userNameEl) userNameEl.textContent = "@" + user.username;

        // 2. Evento Abrir Perfil
        const avatarBtn = document.getElementById('tl-avatar-btn');
        const openProfile = () => {
            if(window.ModalSystem) window.ModalSystem.open('profile');
        };

        if (avatarBtn) avatarBtn.addEventListener('click', openProfile);
        if (realNameEl) realNameEl.addEventListener('click', openProfile);

        // 3. Evento Logout
        const btnLogout = document.getElementById('btn-logout');
        if (btnLogout) {
            btnLogout.addEventListener('click', async (e) => {
                e.stopPropagation();
                if(confirm("¿Cerrar sesión?")) {
                    await fetch('/api/logout', { method: 'POST' });
                    window.location.reload();
                }
            });
        }

    } catch (e) { console.error("Error Top-Left:", e); }
})();