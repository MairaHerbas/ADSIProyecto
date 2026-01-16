(async function() {
    console.log("Cargando Top-Left...");

    try {
        // 1. Obtener datos del usuario
        const res = await fetch('/api/user-info');
        if (!res.ok) return; // Si falla (no logueado), no hacemos nada

        const user = await res.json();

        // 2. Rellenar HTML (Avatar, Nombre, Nivel, XP)
        const nameEl = document.getElementById('tl-username');
        const lvlEl = document.getElementById('tl-lvl-val');
        const xpEl = document.getElementById('tl-xp-fill');
        const avatarEl = document.getElementById('tl-avatar-img');

        if(nameEl) nameEl.textContent = user.username;
        if(lvlEl) lvlEl.textContent = user.level;

        if(xpEl) {
            const xpPercent = (user.xp / user.xp_next) * 100;
            xpEl.style.width = `${xpPercent}%`;
        }

        // Cargar avatar personalizado si existe
        if(avatarEl && user.avatar) {
             // Si tienes sistema de avatares, aquí iría la URL correcta
             // avatarEl.src = user.avatar;
        }

        // --- 3. EVENTOS DE CLIC (ABRIR PERFIL) ---
        // Esto es lo que te faltaba:
        const avatarBtn = document.getElementById('tl-avatar-btn');

        // Función para abrir perfil
        const openProfile = () => {
            console.log("Abriendo perfil...");
            if(window.ModalSystem) {
                window.ModalSystem.open('profile');
            } else {
                console.error("El sistema modal no está listo.");
            }
        };

        // Añadimos el evento a la foto y al nombre
        if (avatarBtn) avatarBtn.addEventListener('click', openProfile);
        if (nameEl) nameEl.addEventListener('click', openProfile);


        // --- 4. LÓGICA DE LOGOUT (BOTÓN APAGAR) ---
        const btnLogout = document.getElementById('btn-logout');
        if (btnLogout) {
            btnLogout.addEventListener('click', async (e) => {
                e.stopPropagation(); // Evita que el click se propague
                if(confirm("¿Cerrar sesión y salir?")) {
                    await fetch('/api/logout', { method: 'POST' });
                    window.location.reload();
                }
            });
        }

    } catch (e) { console.error("Error en Top-Left:", e); }
})();