export function loadTeamContent(team, contentArea, startEditing = false) {
    const container = document.createElement('div');
    container.className = 'team-view-container';

    // Header Badge
    const badge = document.createElement('div');
    badge.className = 'team-header-badge';
    badge.textContent = startEditing ? "CREAR EQUIPO" : "CONSULTAR EQUIPO"; 
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

    // Configuración inicial de botones
    if (startEditing) {
        btnMain.textContent = "CREAR";
        btnSec.textContent = "CANCELAR";
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
        renderTeamNameHeader(leftPanel, team);
        enterEditMode(team, leftPanel, rightContentPanel, btnMain, btnSec, badge);
    } else {
        renderTeamNameHeader(leftPanel, team); 
        renderPokemonList(leftPanel, team.members || [], rightContentPanel, false);

        // 1. EDITAR
        btnMain.onclick = () => {
            enterEditMode(team, leftPanel, rightContentPanel, btnMain, btnSec, badge);
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

// --- MODO EDICIÓN ---
async function enterEditMode(team, leftPanel, rightPanel, btnMain, btnSec, badge) {
    const isNew = (team.id === null);

    // 1. UI Updates
    badge.textContent = isNew ? "NUEVO EQUIPO" : "EDITANDO EQUIPO";
    badge.style.color = "var(--dp-success)";
    
    btnMain.textContent = isNew ? "CREAR" : "GUARDAR CAMBIOS";
    btnMain.classList.add('saving');
    
    // Override Cancelar para evitar borrado
    btnSec.onclick = null; 
    btnSec.textContent = "CANCELAR";
    btnSec.classList.remove('confirm-state');
    btnSec.onclick = () => {
        if(isNew) window.ModalSystem.close(); 
        else window.ModalSystem.open('team', team); 
    };

    // 2. Input Nombre
    const nameWrapper = leftPanel.querySelector('.team-name-wrapper');
    if(nameWrapper) nameWrapper.remove(); // Eliminamos el wrapper antiguo
    
    const nameInput = document.createElement('input');
    nameInput.type = 'text';
    nameInput.className = 'edit-input';
    nameInput.placeholder = "NOMBRE DEL EQUIPO...";
    nameInput.value = team.name;
    nameInput.style.fontSize = "1.5cqw";
    nameInput.style.marginBottom = "10px";
    
    leftPanel.prepend(nameInput);

    // 3. Fetch Disponible
    try {
        const res = await fetch('/api/team-edit-available', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({id: team.id})
        });
        const data = await res.json();

        // 4. Render Izquierda
        const oldList = leftPanel.querySelector('.poke-list-container');
        if(oldList) oldList.remove();
        
        // Simplemente añadimos al final del panel (ya no hay botones dentro)
        renderPokemonList(leftPanel, team.members, null, true);

        // 5. Render Derecha
        rightPanel.innerHTML = '';
        renderPokemonList(rightPanel, data.available, null, true);

        // 6. Drag & Drop
        setupDragAndDrop(leftPanel, rightPanel);

        // 7. Acción Guardar
        btnMain.onclick = () => handleSaveAction(team, leftPanel, btnMain, nameInput.value, isNew);
        nameInput.addEventListener('input', (e) => team.name = e.target.value);

    } catch (e) {
        console.error(e);
        rightPanel.innerHTML = '<div style="color:red; text-align:center">Error cargando caja</div>';
    }
}

// --- GUARDAR ---
async function handleSaveAction(team, leftPanel, saveBtn, currentNameInputVal, isNew) {
    const currentList = getPokemonDataFromDOM(leftPanel);
    const finalName = currentNameInputVal || team.name;

    if (!finalName || !finalName.trim()) {
        triggerErrorShake(saveBtn);
        const t = saveBtn.textContent;
        saveBtn.textContent = "¡FALTA NOMBRE!";
        setTimeout(() => saveBtn.textContent = t, 1500);
        return;
    }

    if (currentList.length === 0) {
        triggerErrorShake(saveBtn);
        const t = saveBtn.textContent;
        saveBtn.textContent = "¡EQUIPO VACÍO!";
        setTimeout(() => saveBtn.textContent = t, 1500);
        return;
    }

    const originalText = saveBtn.textContent;
    saveBtn.textContent = isNew ? "CREANDO..." : "GUARDANDO...";
    saveBtn.disabled = true;

    const endpoint = isNew ? '/api/team-create' : '/api/team-update';

    try {
        const res = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                id: team.id,
                name: finalName,
                members: currentList
            })
        });

        const result = await res.json();

        if (result.success) {
            Object.assign(team, result.team || {}); 
            if(!isNew) {
                team.name = result.newName;
                team.members = result.members;
            }

            saveBtn.textContent = "¡ÉXITO!";
            saveBtn.style.backgroundColor = "var(--dp-success)";
            
            setTimeout(() => {
                if(isNew) window.ModalSystem.close();
                else window.ModalSystem.open('team', team);
            }, 800);
        } else {
            throw new Error(result.error);
        }

    } catch (e) {
        console.error(e);
        triggerErrorShake(saveBtn);
        saveBtn.textContent = "ERROR";
        setTimeout(() => {
            saveBtn.textContent = originalText;
            saveBtn.disabled = false;
        }, 1500);
    }
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

function renderPokemonList(container, pokemonList, detailViewContainer, isEditable) {
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
    pokemonList.forEach(pk => createDraggableRow(pk, listWrapper, detailViewContainer, isEditable, container.id));
}

function createDraggableRow(pk, parent, detailViewContainer, isEditable, containerId) {
    const row = document.createElement('div');
    row.className = 'poke-item-row';
    row.innerHTML = `<div class="pk-info-left"><span class="pk-name">${pk.name}</span><span class="pk-type">${pk.type||'Normal'}</span></div><div class="pk-info-right"><span class="pk-lvl">Nv. ${pk.lvl||'??'}</span><div class="pk-icon-ph"></div></div>`;
    if (isEditable) {
        row.classList.add('draggable-item'); row.draggable = true; row.dataset.pokemon = JSON.stringify(pk);
        row.addEventListener('dragstart', (e) => { row.classList.add('dragging'); e.dataTransfer.setData('application/json', JSON.stringify(pk)); e.dataTransfer.setData('source-id', containerId); e.dataTransfer.effectAllowed = 'move'; });
        row.addEventListener('dragend', () => { row.classList.remove('dragging'); document.querySelectorAll('.drop-active').forEach(e=>e.classList.remove('drop-active')); document.querySelectorAll('.drop-error').forEach(e=>e.classList.remove('drop-error')); });
    } else if (detailViewContainer) {
        row.onclick = () => { parent.querySelectorAll('.poke-item-row').forEach(r=>r.classList.remove('selected')); row.classList.add('selected'); renderPokemonDetails(pk, detailViewContainer); };
    }
    parent.appendChild(row);
}

function setupDragAndDrop(leftPanel, rightPanel) {
    leftPanel.dataset.dropMsg = "AÑADIR"; leftPanel.dataset.errorMsg = "¡LLENO!"; rightPanel.dataset.dropMsg = "QUITAR";
    [leftPanel, rightPanel].forEach(panel => {
        panel.addEventListener('dragover', (e) => { e.preventDefault(); if(panel.classList.contains('drop-error')) return; panel.classList.add('drop-active'); });
        panel.addEventListener('dragleave', (e) => { if(e.relatedTarget && panel.contains(e.relatedTarget)) return; panel.classList.remove('drop-active'); panel.classList.remove('drop-error'); });
        panel.addEventListener('drop', (e) => {
            e.preventDefault(); panel.classList.remove('drop-active');
            const str = e.dataTransfer.getData('application/json'); const src = e.dataTransfer.getData('source-id');
            if(!str || src === panel.id) return;
            const pk = JSON.parse(str);
            if(panel.id === 'panel-team-members') {
                if(getPokemonDataFromDOM(leftPanel).length >= 6) { triggerErrorShake(panel); return; }
            }
            let dest = panel.querySelector('.poke-list-container');
            createDraggableRow(pk, dest, null, true, panel.id);
            const old = document.querySelector('.draggable-item.dragging'); if(old) old.remove();
        });
    });
}

function getPokemonDataFromDOM(p) { const l=[]; p.querySelectorAll('.poke-item-row').forEach(r=>{if(r.dataset.pokemon)l.push(JSON.parse(r.dataset.pokemon))}); return l; }
function triggerErrorShake(e) { if(e.id==='panel-team-members'){e.classList.add('drop-error','error-shake');setTimeout(()=>{e.classList.remove('drop-error','error-shake')},600);}else{e.classList.add('btn-error');setTimeout(()=>e.classList.remove('btn-error'),500);} }
function renderPokemonDetails(pk, c) { c.innerHTML=''; const d=document.createElement('div'); d.className='pk-detail-view'; d.innerHTML=`<div class="pk-detail-header"><div class="pk-detail-circle-big"></div><div class="pk-detail-name">${pk.name}</div></div><ul class="pk-stats-list"><li class="pk-stat-row"><span class="pk-label">Nivel</span><span class="pk-val">${pk.lvl}</span></li><li class="pk-stat-row"><span class="pk-label">Tipo</span><span class="pk-val">${pk.type}</span></li></ul>`; c.appendChild(d); setTimeout(()=>d.style.opacity='1',0); }
function renderTeamNameHeader(c, t) { const w=document.createElement('div'); w.className='team-name-wrapper'; w.innerHTML=`<div class="name-row"><span class="team-name-text">${t.name}</span></div>`; c.appendChild(w); }