import { setupScrollLogic } from '../logic.js';

let usersCache = [];
let pendingCache = [];

export async function loadAdminData() {
    const usersList = document.getElementById('list-admin-users-ul');
    const pendingList = document.getElementById('list-admin-pending-ul');
    
    if(usersList) setupScrollLogic(usersList);
    if(pendingList) setupScrollLogic(pendingList);

    try {
        const res = await fetch('/api/admin/data');
        const data = await res.json();
        
        if (data.error) return; 

        // 1. Guardar Cache
        usersCache = data.users || [];
        pendingCache = data.pending || [];

        // 2. Renderizar
        if(usersList) renderUsersList(usersCache, usersList);
        if(pendingList) renderPendingList(pendingCache, pendingList);

        // 3. Configurar Buscadores
        setupSearch('admin-user-search-input', usersCache, (filtered) => renderUsersList(filtered, usersList));
        setupSearch('admin-pending-search-input', pendingCache, (filtered) => renderPendingList(filtered, pendingList));

    } catch (e) {
        console.error("Error admin", e);
    }
}

function setupSearch(inputId, dataArray, renderFunc) {
    const input = document.getElementById(inputId);
    if (!input) return;
    const newInput = input.cloneNode(true);
    input.parentNode.replaceChild(newInput, input);
    newInput.value = '';
    newInput.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();
        const filtered = dataArray.filter(u => u.toLowerCase().includes(term));
        renderFunc(filtered);
    });
}

function renderUsersList(users, ul) {
    ul.innerHTML = '';
    if (users.length === 0) {
        ul.innerHTML = '<li class="friend-item" style="justify-content:center"><span class="item-name" style="opacity:0.5">Sin resultados</span></li>';
        return;
    }

    users.forEach(username => {
        const li = document.createElement('li');
        li.className = 'friend-item'; 
        
        // Estructura IDÉNTICA a amigos
        li.innerHTML = `
            <span class="item-name">${username}</span>
            <button class="btn-remove-friend" title="Eliminar Usuario">
                <div class="btn-icon-mask"></div>
            </button>
        `;

        li.addEventListener('click', (e) => {
            if(e.target.closest('.btn-remove-friend')) return;
            if(window.ModalSystem) window.ModalSystem.open('profile', { username: username, stats: "Usuario" });
        });

        li.querySelector('.btn-remove-friend').addEventListener('click', async () => {
            if(confirm(`¿Eliminar definitivamente a ${username}?`)) {
                await fetch('/api/admin/delete-user', {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({name: username})
                });
                const idx = usersCache.indexOf(username);
                if (idx > -1) usersCache.splice(idx, 1);
                li.remove();
                if(ul.children.length === 0) ul.innerHTML = '<li class="friend-item" style="justify-content:center"><span class="item-name" style="opacity:0.5">Sin resultados</span></li>';
            }
        });
        ul.appendChild(li);
    });
}

function renderPendingList(users, ul) {
    ul.innerHTML = '';
    if (users.length === 0) {
        ul.innerHTML = '<li class="friend-item" style="justify-content:center"><span class="item-name" style="opacity:0.5">Sin resultados</span></li>';
        return;
    }

    users.forEach(username => {
        const li = document.createElement('li');
        li.className = 'friend-item';
        
        // Estructura IDÉNTICA a pendientes
        li.innerHTML = `
            <span class="item-name">${username}</span>
            <div class="actions-wrapper">
                <div class="action-sq-btn btn-accept" title="Aprobar"><div class="btn-icon-mask"></div></div>
                <div class="action-sq-btn btn-reject" title="Rechazar"><div class="btn-icon-mask"></div></div>
            </div>
        `;

        li.querySelector('.btn-accept').addEventListener('click', async () => {
            await fetch('/api/admin/approve-user', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name: username})
            });
            const idx = pendingCache.indexOf(username);
            if (idx > -1) pendingCache.splice(idx, 1);
            li.remove();
            loadAdminData(); 
        });

        li.querySelector('.btn-reject').addEventListener('click', async () => {
            if(confirm(`¿Rechazar a ${username}?`)) {
                await fetch('/api/admin/reject-user', {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({name: username})
                });
                const idx = pendingCache.indexOf(username);
                if (idx > -1) pendingCache.splice(idx, 1);
                li.remove();
            }
        });
        ul.appendChild(li);
    });
}