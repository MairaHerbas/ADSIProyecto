(async function() {
    console.log("Módulo BL: Cargando lista...");

    const userRole = 'user'; 
    const listContainer = document.getElementById('bl-team-list');
    const wrapper = document.querySelector('.bl-list-wrapper');
    const btnAdd = document.querySelector('.bl-action-btn'); 
    let scrollTimeout;

    // Gestión de Vistas
    const viewUser = document.getElementById('bl-view-user');
    const viewAdmin = document.getElementById('bl-view-admin');
    if(viewUser) viewUser.style.display = (userRole === 'user') ? 'flex' : 'none';
    if(viewAdmin) viewAdmin.style.display = (userRole === 'admin') ? 'flex' : 'none';

    if (userRole !== 'user') return;

    // --- FUNCIÓN DE ACTUALIZACIÓN ---
    async function renderTeamList() {
        if (!listContainer) return;
        
        try {
            const response = await fetch('/api/user-info');
            const data = await response.json();

            listContainer.innerHTML = '';

            if (data.teams && data.teams.length > 0) {
                data.teams.forEach(team => {
                    const li = document.createElement('li');
                    li.className = 'team-item';
                    
                    let iconsHtml = '';
                    for(let i=0; i < team.pokemon_count; i++) {
                        iconsHtml += `<div class="poke-icon"></div>`;
                    }

                    li.innerHTML = `
                        <span class="team-name">${team.name}</span>
                        <div class="team-mons">${iconsHtml}</div>
                    `;

                    li.addEventListener('click', () => {
                        if (window.ModalSystem) {
                            window.ModalSystem.open('team', team);
                        }
                    });

                    listContainer.appendChild(li);
                });
                
                updateScrollShadows();
            } else {
                listContainer.innerHTML = '<li style="padding:20px; text-align:center; color:#888;">No tienes equipos</li>';
            }

        } catch (e) {
            console.error("Error cargando equipos", e);
        }
    }

    // --- NUEVO: EVENTO BOTÓN AGREGAR (ESTO FALTABA) ---
    if (btnAdd) {
        btnAdd.addEventListener('click', () => {
            if (window.ModalSystem) {
                window.ModalSystem.open('team-new');
            } else {
                console.warn("El sistema modal aún no está listo.");
            }
        });
    }

    // Inicialización
    await renderTeamList();
    window.addEventListener('app-data-refresh', renderTeamList);

    // Lógica Scroll
    if (listContainer) {
        listContainer.addEventListener('scroll', () => {
            updateScrollShadows();
            listContainer.classList.add('scrolling');
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                listContainer.classList.remove('scrolling');
            }, 3000);
        });
    }

    function updateScrollShadows() {
        if (!wrapper || !listContainer) return;
        const scrollTop = listContainer.scrollTop;
        const scrollHeight = listContainer.scrollHeight;
        const clientHeight = listContainer.clientHeight;

        if (scrollTop > 5) wrapper.classList.add('can-scroll-up');
        else wrapper.classList.remove('can-scroll-up');

        if (scrollTop + clientHeight < scrollHeight - 1) wrapper.classList.add('can-scroll-down');
        else wrapper.classList.remove('can-scroll-down');
    }
})();