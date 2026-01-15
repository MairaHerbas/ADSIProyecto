export async function loadPokedexContent(contentArea) {
    const container = document.createElement('div');
    container.className = 'team-view-container';

    // Header
    const badge = document.createElement('div');
    badge.className = 'team-header-badge';
    badge.textContent = "POKÉDEX"; // <--- CAMBIO: Nombre simplificado
    badge.style.color = "#dc0a2d";
    container.appendChild(badge);

    // Grid
    const grid = document.createElement('div');
    grid.className = 'team-grid-wrapper';

    // --- IZQUIERDA ---
    const leftPanel = document.createElement('div');
    leftPanel.className = 'team-panel-left';

    // Buscador
    const searchWrapper = document.createElement('div');
    searchWrapper.className = 'pokedex-search-wrapper';
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'dex-search-input';
    input.placeholder = "BUSCAR POKÉMON...";
    searchWrapper.appendChild(input);
    leftPanel.appendChild(searchWrapper);

    // Lista
    const listContainer = document.createElement('div');
    listContainer.className = 'poke-list-container';
    leftPanel.appendChild(listContainer);

    // --- DERECHA ---
    const rightCol = document.createElement('div');
    rightCol.className = 'team-col-right';

    const detailsPanel = document.createElement('div');
    detailsPanel.className = 'team-panel-tr';
    detailsPanel.innerHTML = '<div class="pk-empty-state">Selecciona un Pokémon para analizar datos</div>';

    // BOTÓN DE ACCIÓN (INICIAL)
    const actionBtn = document.createElement('div');
    actionBtn.id = 'pokedex-action-btn'; 
    actionBtn.className = 'team-panel-br dex-action-btn'; 
    actionBtn.textContent = "SELECCIONA UNO";
    actionBtn.style.opacity = "0.5";
    actionBtn.style.cursor = "default";

    rightCol.appendChild(detailsPanel);
    rightCol.appendChild(actionBtn);

    grid.appendChild(leftPanel);
    grid.appendChild(rightCol);
    container.appendChild(grid);
    contentArea.appendChild(container);

    // --- LÓGICA ---
    try {
        listContainer.innerHTML = '<div style="text-align:center; padding:20px; color:#888;">Cargando base de datos...</div>';
        const res = await fetch('/api/pokedex');
        const allSpecies = await res.json();
        
        renderDexList(allSpecies, listContainer, detailsPanel);

        input.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            const filtered = allSpecies.filter(p => p.name.toLowerCase().includes(term));
            renderDexList(filtered, listContainer, detailsPanel);
        });

    } catch (e) {
        console.error(e);
        listContainer.innerHTML = '<div style="color:red; text-align:center; padding:20px;">Error de conexión con el servidor Pokedex.</div>';
    }
}

function renderDexList(list, container, detailsPanel) {
    container.innerHTML = '';
    
    if(list.length === 0) {
        container.innerHTML = '<div style="color:#666; text-align:center; padding:20px;">No hay resultados</div>';
        return;
    }

    list.forEach(pk => {
        const row = document.createElement('div');
        row.className = 'poke-item-row';
        row.id = `dex-row-${pk.name}`; 

        const ownedIcon = pk.owned ? '<div class="owned-icon" title="Capturado"></div>' : '';

        row.innerHTML = `
            <div class="pk-info-left">
                <span class="pk-name" style="color:${pk.owned ? 'var(--dp-success)' : '#ccc'}">${pk.name}</span>
                <span class="pk-type">${pk.type}</span>
            </div>
            <div class="pk-info-right">
                <div class="icon-wrapper">${ownedIcon}</div>
                <div class="pk-icon-ph"></div>
            </div>
        `;

        row.addEventListener('click', () => {
            container.querySelectorAll('.poke-item-row').forEach(r => r.classList.remove('selected'));
            row.classList.add('selected');
            
            renderDexDetails(pk, detailsPanel);
            
            const currentBtn = document.getElementById('pokedex-action-btn');
            if (currentBtn) {
                updateActionButton(pk, currentBtn, detailsPanel, row);
            }
        });

        container.appendChild(row);
    });
}

function updateActionButton(pk, oldBtn, detailsPanel, rowElement) {
    const btn = oldBtn.cloneNode(true);
    btn.id = 'pokedex-action-btn'; 
    oldBtn.parentNode.replaceChild(btn, oldBtn);

    btn.className = 'team-panel-br dex-action-btn'; 
    btn.style.opacity = "1";
    btn.style.cursor = "pointer";
    btn.removeAttribute('style'); 

    if (pk.owned) {
        btn.textContent = "YA LO TIENES";
        btn.classList.add('is-owned'); 
    } else {
        btn.textContent = "AÑADIR A COLECCIÓN";
        btn.classList.add('can-capture'); 
        
        btn.addEventListener('click', async () => {
            await addToCollection(pk, btn, detailsPanel, rowElement);
        });
    }
}

async function addToCollection(pk, btn, detailsPanel, rowElement) {
    btn.textContent = "REGISTRANDO...";
    btn.className = 'team-panel-br dex-action-btn is-loading'; 
    
    try {
        const res = await fetch('/api/pokedex/add', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name: pk.name})
        });
        
        if (res.ok) {
            pk.owned = true; 
            btn.textContent = "¡CAPTURADO!";
            
            setTimeout(() => {
                const freshBtn = document.getElementById('pokedex-action-btn');
                if(freshBtn) updateActionButton(pk, freshBtn, detailsPanel, rowElement);
                renderDexDetails(pk, detailsPanel);

                if (rowElement) {
                    const nameSpan = rowElement.querySelector('.pk-name');
                    if(nameSpan) nameSpan.style.color = 'var(--dp-success)';
                    const iconWrapper = rowElement.querySelector('.icon-wrapper');
                    if(iconWrapper) iconWrapper.innerHTML = '<div class="owned-icon" title="Capturado"></div>';
                }
                window.dispatchEvent(new CustomEvent('app-data-refresh'));
            }, 800);

        } else {
            throw new Error("Error API");
        }
    } catch (e) {
        console.error(e);
        btn.textContent = "ERROR";
        setTimeout(() => {
            pk.owned = false;
            const freshBtn = document.getElementById('pokedex-action-btn');
            if(freshBtn) updateActionButton(pk, freshBtn, detailsPanel, rowElement);
        }, 1500);
    }
}

function renderDexDetails(pk, container) {
    container.innerHTML = '';
    const d = document.createElement('div');
    d.className = 'pk-detail-view';
    d.innerHTML = `
        <div class="pk-detail-header">
            <div class="pk-detail-circle-big" style="background-color: ${pk.owned ? 'var(--dp-success)' : '#888'}; transition: background-color 0.3s;"></div>
            <div class="pk-detail-name">${pk.name}</div>
        </div>
        <ul class="pk-stats-list">
            <li class="pk-stat-row"><span class="pk-label">Tipo</span><span class="pk-val">${pk.type}</span></li>
            <li class="pk-stat-row"><span class="pk-label">Estado</span><span class="pk-val" style="color:${pk.owned ? 'var(--dp-success)' : 'inherit'}">${pk.owned ? 'REGISTRADO' : 'No registrado'}</span></li>
        </ul>
        <div style="margin-top:20px; font-size:0.9cqw; color:#666; font-style: italic;">
            ${pk.owned ? 'Entrada sincronizada con la base de datos nacional.' : 'Selecciona "Añadir" para registrar este avistamiento.'}
        </div>
    `;
    container.appendChild(d);
    d.style.opacity = 0;
    d.style.transition = 'opacity 0.2s ease-out';
    requestAnimationFrame(() => d.style.opacity = 1);
}