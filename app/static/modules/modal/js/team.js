// app/static/modules/modal/js/team.js

export function loadTeamContent(team, contentArea, startEditing = false) {
    // --- LÓGICA PUNTO 4: SI ES UN EQUIPO NUEVO (NO TIENE ID), CREARLO PRIMERO ---
    if (startEditing && !team.id) {
        createEmptyTeamAndRedirect(contentArea);
        return; // Detenemos aquí, la función se volverá a llamar cuando tengamos ID
    }

    const container = document.createElement('div');
    container.className = 'team-view-container';

    // Header Badge
    const badge = document.createElement('div');
    badge.className = 'team-header-badge';
    badge.textContent = startEditing ? "EDITANDO EQUIPO" : "CONSULTAR EQUIPO";
    container.appendChild(badge);

    // Grid Wrapper
    const grid = document.createElement('div');
    grid.className = 'team-grid-wrapper';

    // --- IZQUIERDA (Wrapper) ---
    const leftWrapper = document.createElement('div');
    leftWrapper.className = 'left-column-wrapper';

    const leftPanel = document.createElement('div');
    leftPanel.className = 'team-panel-left';
    leftPanel.id = 'panel-team-members';

    const actionsRow = document.createElement('div');
    actionsRow.className = 'team-actions-row';

    const btnMain = document.createElement('button');
    btnMain.className = 'btn-main-action';

    const btnSec = document.createElement('button');
    btnSec.className = 'btn-sec-action';

    if (startEditing) {
        btnMain.textContent = "TERMINAR"; // Ya no es "Guardar", porque se guarda solo
        btnSec.style.display = 'none';    // No hay cancelar
    } else {
        btnMain.textContent = "EDITAR EQUIPO";
        btnSec.textContent = "ELIMINAR";
    }

    actionsRow.appendChild(btnMain);
    actionsRow.appendChild(btnSec);
    leftWrapper.appendChild(leftPanel);
    leftWrapper.appendChild(actionsRow);

    // --- DERECHA ---
    const rightCol = document.createElement('div');
    rightCol.className = 'team-col-right';

    const rightContentPanel = document.createElement('div');
    rightContentPanel.className = 'team-panel-tr';
    rightContentPanel.id = 'panel-available';

    if (startEditing) {
        rightContentPanel.innerHTML = '<div style="padding:20px; text-align:center;">Cargando caja...</div>';
    } else {
        rightContentPanel.innerHTML = '<div class="pk-empty-state">Selecciona un Pokémon de la lista para ver sus características</div>';
    }

    rightCol.appendChild(rightContentPanel);

    // --- ENSAMBLAJE DOM ---
    grid.appendChild(leftWrapper);
    grid.appendChild(rightCol);
    container.appendChild(grid);
    contentArea.innerHTML = '';
    contentArea.appendChild(container);

    // --- LÓGICA DE FLUJO ---
    if (startEditing) {
        // En modo edición pasamos el OBJETO team completo
        renderTeamNameInput(leftPanel, team);
        enterEditMode(team, leftPanel, rightContentPanel, btnMain, btnSec, badge);
    } else {
        renderTeamNameHeader(leftPanel, team);
        renderPokemonList(leftPanel, team.members || [], rightContentPanel, false);
        // 1. IR A EDITAR
        btnMain.onclick = () => {
            // CORRECCIÓN: No usamos window.ModalSystem.open porque eso fuerza el modo lectura (false).
            // En su lugar, limpiamos el área y cargamos 'loadTeamContent' directamente con TRUE.

            contentArea.innerHTML = '';
            loadTeamContent(team, contentArea, true);
        };

        // 2. ELIMINAR (Confirmación UI sin alert)
        let confirmState = false;
        let timeout;

        btnSec.onclick = () => {
            if (!confirmState) {
                confirmState = true;
                btnSec.textContent = "¿CONFIRMAR?";
                btnSec.classList.add('confirm-state');
                timeout = setTimeout(() => {
                    confirmState = false;
                    btnSec.textContent = "ELIMINAR";
                    btnSec.classList.remove('confirm-state');
                }, 3000);
            } else {
                clearTimeout(timeout);
                deleteTeam(team);
            }
        };
    }
}

// --- FUNCIÓN AUXILIAR: CREAR EQUIPO VACÍO (PUNTO 4) ---
async function createEmptyTeamAndRedirect(contentArea) {
    contentArea.innerHTML = '<div style="display:flex;justify-content:center;align-items:center;height:100%;font-size:1.2em;">Creando equipo en base de datos...</div>';
    try {
        const res = await fetch('/api/team/init', {method: 'POST'});
        const data = await res.json();
        if(data.success) {
            // El backend nos devuelve el ID nuevo.
            const newTeam = { id: data.id, name: data.name, members: [] };
            // Volvemos a cargar la vista, pero ahora ya tenemos ID, así que entrará en la lógica normal de edición
            loadTeamContent(newTeam, contentArea, true);
        } else {
            contentArea.innerHTML = '<div style="color:red">Error al inicializar equipo.</div>';
        }
    } catch(e) {
        console.error(e);
        contentArea.innerHTML = '<div style="color:red">Error de conexión.</div>';
    }
}

// --- MODO EDICIÓN ---
async function enterEditMode(team, leftPanel, rightPanel, btnMain, btnSec, badge) {
    // 1. UI Updates
    badge.textContent = "EDITANDO EQUIPO";
    badge.style.color = "var(--dp-success)";

    // Botón "TERMINAR" simplemente cierra el modal
    btnMain.onclick = () => window.ModalSystem.close();

    // 2. Fetch Disponible (Caja)
    try {
        const res = await fetch('/api/team-edit-available', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({id: team.id})
        });
        const data = await res.json();

        // 3. Render Izquierda (Miembros actuales del equipo)
        const oldList = leftPanel.querySelector('.poke-list-container');
        if(oldList) oldList.remove();
        renderPokemonList(leftPanel, team.members, null, true);

        // 4. Render Derecha (Caja disponible)
        rightPanel.innerHTML = '';

        // [MODIFICADO] Pasamos una función callback para el click
        renderPokemonList(rightPanel, data.available, null, true, (pk) => {
            addMemberToTeamLogic(team, pk, leftPanel);
        });

        // 5. Drag & Drop INSTANTÁNEO
        setupDragAndDropInstantaneo(leftPanel, rightPanel, team);

    } catch (e) {
        console.error(e);
        rightPanel.innerHTML = '<div style="color:red; text-align:center">Error cargando caja</div>';
    }
}

// [NUEVO] Lógica centralizada para añadir miembro (usada por Click y Drag&Drop)
async function addMemberToTeamLogic(team, pk, leftPanel) {
    // Validar límite de 6
    if ((team.members || []).length >= 6) {
        triggerErrorShake(leftPanel);
        return;
    }

    try {
        const res = await fetch('/api/team/add-member', {
            method: 'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({ team_id: team.id, pokemon_id: pk.pokemon_id })
        });
        const result = await res.json();

        if(result.success) {
            // Actualizar local
            if(!team.members) team.members = [];
            team.members.push(pk);
            // Repintar izquierda
            renderPokemonList(leftPanel, team.members, null, true);
        } else {
            alert("Error: " + result.error);
        }
    } catch(err) { console.error(err); }
}

// --- DRAG & DROP CON ACTUALIZACIÓN INMEDIATA ---
function setupDragAndDropInstantaneo(leftPanel, rightPanel, team) {
    leftPanel.dataset.dropMsg = "AÑADIR";
    leftPanel.dataset.errorMsg = "¡LLENO!";
    rightPanel.dataset.dropMsg = "QUITAR";

    [leftPanel, rightPanel].forEach(panel => {
        panel.addEventListener('dragover', (e) => {
            e.preventDefault();
            if(panel.classList.contains('drop-error')) return;
            panel.classList.add('drop-active');
        });
        panel.addEventListener('dragleave', (e) => {
            if(e.relatedTarget && panel.contains(e.relatedTarget)) return;
            panel.classList.remove('drop-active');
            panel.classList.remove('drop-error');
        });
    });

    // DROP EN IZQUIERDA: AÑADIR AL EQUIPO
    leftPanel.addEventListener('drop', async (e) => {
        e.preventDefault();
        leftPanel.classList.remove('drop-active');
        const str = e.dataTransfer.getData('application/json');
        if(!str) return;

        const pk = JSON.parse(str);
        // [MODIFICADO] Usamos la lógica centralizada
        addMemberToTeamLogic(team, pk, leftPanel);
    });

    // DROP EN DERECHA: QUITAR DEL EQUIPO (BORRAR)
    rightPanel.addEventListener('drop', async (e) => {
        e.preventDefault();
        rightPanel.classList.remove('drop-active');

        const sourceId = e.dataTransfer.getData('source-id');
        const str = e.dataTransfer.getData('application/json');

        // Solo borramos si viene del panel izquierdo ('panel-team-members')
        if (sourceId === 'panel-team-members' && str) {
            const pk = JSON.parse(str);
            try {
                const res = await fetch('/api/team/remove-member', {
                    method: 'POST', headers:{'Content-Type':'application/json'},
                    body: JSON.stringify({ team_id: team.id, pokemon_id: pk.pokemon_id })
                });
                const result = await res.json();

                if(result.success) {
                    // Actualizar local: Filtramos el que coincida
                    team.members = team.members.filter(m => m.pokemon_id !== pk.pokemon_id);
                    renderPokemonList(leftPanel, team.members, null, true);
                }
            } catch(err) { console.error(err); }
        }
    });
}

// --- UI HELPERS ---
function renderTeamNameInput(container, team) {
    const nameWrapper = container.querySelector('.team-name-wrapper');
    if(nameWrapper) nameWrapper.remove();

    const nameInput = document.createElement('input');
    nameInput.type = 'text';
    nameInput.className = 'edit-input';
    nameInput.placeholder = "NOMBRE DEL EQUIPO...";
    nameInput.value = team.name;
    nameInput.style.fontSize = "1.5cqw";
    nameInput.style.marginBottom = "10px";

    // GUARDADO AUTOMÁTICO DE NOMBRE
    nameInput.addEventListener('blur', async () => {
        if(nameInput.value !== team.name) {
            await fetch('/api/team/set-name', {
                method: 'POST', headers:{'Content-Type':'application/json'},
                body: JSON.stringify({id: team.id, name: nameInput.value})
            });
            team.name = nameInput.value;
        }
    });

    container.prepend(nameInput);
}

function renderTeamNameHeader(c, t) {
    const w=document.createElement('div');
    w.className='team-name-wrapper';
    w.innerHTML=`<div class="name-row"><span class="team-name-text">${t.name}</span></div>`;
    c.appendChild(w);
}

async function deleteTeam(team) {
    try {
        const res = await fetch('/api/team-delete', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({id: team.id})
        });
        if (res.ok) window.ModalSystem.close();
        else alert("Error al eliminar");
    } catch(e) { console.error(e); }
}

// [MODIFICADO] Añadido parámetro onClickCallback
function renderPokemonList(container, pokemonList, detailViewContainer, isEditable, onClickCallback = null) {
    let listWrapper = container.querySelector('.poke-list-container');
    if (!listWrapper) {
        listWrapper = document.createElement('div');
        listWrapper.className = 'poke-list-container';
        if(isEditable) listWrapper.classList.add('edit-mode');
        container.appendChild(listWrapper);
    } else {
        listWrapper.innerHTML = '';
    }
    if (!pokemonList) return;
    pokemonList.forEach(pk => createDraggableRow(pk, listWrapper, detailViewContainer, isEditable, container.id, onClickCallback));
}

// [MODIFICADO] Añadido parámetro onClickCallback y evento click
function createDraggableRow(pk, parent, detailViewContainer, isEditable, containerId, onClickCallback) {
    const row = document.createElement('div');
    row.className = 'poke-item-row';
    row.innerHTML = `<div class="pk-info-left"><span class="pk-name">${pk.name}</span><span class="pk-type">${pk.type||'Normal'}</span></div><div class="pk-info-right"><span class="pk-lvl">Nv. ${pk.lvl||'??'}</span><div class="pk-icon-ph"></div></div>`;

    if (isEditable) {
        row.classList.add('draggable-item');
        row.draggable = true;
        row.dataset.pokemon = JSON.stringify(pk);

        // Si hay callback de click (para la caja derecha), lo usamos
        if (onClickCallback) {
            row.style.cursor = "pointer";
            row.title = "Clic para añadir al equipo";
            row.onclick = () => onClickCallback(pk);
        }

        row.addEventListener('dragstart', (e) => {
            row.classList.add('dragging');
            e.dataTransfer.setData('application/json', JSON.stringify(pk));
            e.dataTransfer.setData('source-id', containerId);
            e.dataTransfer.effectAllowed = 'move';
        });
        row.addEventListener('dragend', () => {
            row.classList.remove('dragging');
            document.querySelectorAll('.drop-active').forEach(e=>e.classList.remove('drop-active'));
            document.querySelectorAll('.drop-error').forEach(e=>e.classList.remove('drop-error'));
        });
    } else if (detailViewContainer) {
        row.onclick = () => {
            parent.querySelectorAll('.poke-item-row').forEach(r=>r.classList.remove('selected'));
            row.classList.add('selected');
            renderPokemonDetails(pk, detailViewContainer);
        };
    }
    parent.appendChild(row);
}

function triggerErrorShake(e) {
    if(e.id==='panel-team-members'){
        e.classList.add('drop-error','error-shake');
        setTimeout(()=>{e.classList.remove('drop-error','error-shake')},600);
    } else {
        e.classList.add('btn-error');
        setTimeout(()=>e.classList.remove('btn-error'),500);
    }
}

function renderPokemonDetails(pk, c) {
    c.innerHTML='';
    const d=document.createElement('div');
    d.className='pk-detail-view';
    d.innerHTML=`<div class="pk-detail-header"><div class="pk-detail-circle-big"></div><div class="pk-detail-name">${pk.name}</div></div><ul class="pk-stats-list"><li class="pk-stat-row"><span class="pk-label">Nivel</span><span class="pk-val">${pk.lvl}</span></li><li class="pk-stat-row"><span class="pk-label">Tipo</span><span class="pk-val">${pk.type}</span></li></ul>`;
    c.appendChild(d);
    setTimeout(()=>d.style.opacity='1',0);
}