import { setupScrollLogic } from '../logic.js';

let usersCache = [];
let pendingCache = [];

export async function loadAdminData() {
    const usersList = document.getElementById('list-admin-users-ul');
    const pendingList = document.getElementById('list-admin-pending-ul');
    
    if(usersList) setupScrollLogic(usersList);
    if(pendingList) setupScrollLogic(pendingList);

    try {
        const res = await fetch('/api/admin/dashboard-data');
        const data = await res.json();

        if (data.error) return;

        usersCache = data.directory || [];
        pendingCache = data.pending || [];

        if(usersList) renderUsersList(usersCache, usersList);
        if(pendingList) renderPendingList(pendingCache, pendingList);

        setupSearch('admin-user-search-input', usersCache, (filtered) => renderUsersList(filtered, usersList));
        setupSearch('admin-pending-search-input', pendingCache, (filtered) => renderPendingList(filtered, pendingList));

    } catch (e) { console.error("Error admin", e); }
}

function setupSearch(inputId, dataArray, renderFunc) {
    const input = document.getElementById(inputId);
    if (!input) return;
    const newInput = input.cloneNode(true);
    input.parentNode.replaceChild(newInput, input);

    newInput.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();
        const filtered = dataArray.filter(u =>
            (u.username && u.username.toLowerCase().includes(term)) ||
            (u.name && u.name.toLowerCase().includes(term))
        );
        renderFunc(filtered, document.getElementById(inputId === 'admin-user-search-input' ? 'list-admin-users-ul' : 'list-admin-pending-ul'));
    });
}

// ... (imports y variables cache arriba igual) ...

function renderUsersList(users, ul) {
    ul.innerHTML = '';
    if (users.length === 0) {
        ul.innerHTML = '<li class="friend-item" style="justify-content:center"><span class="item-name" style="opacity:0.5">Sin resultados</span></li>';
        return;
    }

    users.forEach(u => {
        const li = document.createElement('li');
        li.className = 'friend-item';

        // Lógica de visualización
        const isAdmin = u.role === 'admin';
        const adminClass = isAdmin ? 'is-admin' : '';
        const roleBtnClass = isAdmin ? 'btn-demote' : 'btn-promote';
        const roleBtnTitle = isAdmin ? 'Degradar a Usuario' : 'Ascender a Administrador';

        // Evitar botones en el Super Admin (username: admin)
        const isSuperAdmin = u.username === 'admin';
        const roleButtonHTML = isSuperAdmin ? '' :
            `<div class="action-sq-btn ${roleBtnClass}" title="${roleBtnTitle}" data-role-action="true">
                <div class="btn-icon-mask"></div>
            </div>`;

        li.innerHTML = `
            <div style="display:flex; flex-direction:column;">
                <span class="item-name ${adminClass}">${u.username}</span>
                <span style="font-size:0.8em; color:#888">${u.email}</span>
            </div>
            <div class="actions-wrapper">
                ${roleButtonHTML}

                <div class="action-sq-btn btn-trash" title="Eliminar cuenta">
                    <div class="btn-icon-mask"></div>
                </div>
            </div>
        `;

        // EVENTO: CAMBIAR ROL
        const roleBtn = li.querySelector(`.${roleBtnClass}`);
        if(roleBtn) {
            roleBtn.addEventListener('click', async () => {
                const newRole = isAdmin ? 'user' : 'admin';
                const actionText = isAdmin ? 'degradar a Usuario' : 'ascender a Administrador';

                if(confirm(`¿Quieres ${actionText} a ${u.username}?`)) {
                    await changeUserRole(u.id, newRole);
                }
            });
        }

        // EVENTO: ELIMINAR (Igual que antes)
        li.querySelector('.btn-trash').addEventListener('click', async () => {
            if(confirm(`⚠️ ¿Eliminar permanentemente a @${u.username}?`)) {
                await deleteUser(u.id);
            }
        });

        ul.appendChild(li);
    });
}

// Nueva función auxiliar para llamar a la API de rol
async function changeUserRole(id, newRole) {
    try {
        const res = await fetch(`/api/admin/user/${id}/role`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ role: newRole })
        });
        const data = await res.json();

        if (data.error) {
            alert("Error: " + data.error);
        } else {
            // alert(data.msg); // Opcional: mostrar mensaje de éxito
            loadAdminData(); // Recargar lista visualmente
        }
    } catch(e) { console.error(e); }
}



// --- LISTA DE SOLICITUDES PENDIENTES ---
function renderPendingList(users, ul) {
    ul.innerHTML = '';
    if (users.length === 0) {
        ul.innerHTML = '<li class="friend-item" style="justify-content:center"><span class="item-name" style="opacity:0.5">No hay solicitudes</span></li>';
        return;
    }

    users.forEach(u => {
        const li = document.createElement('li');
        li.className = 'friend-item';

        li.innerHTML = `
             <div style="display:flex; flex-direction:column;">
                <span class="item-name">${u.username}</span>
                <span style="font-size:0.8em; color:#888">${u.email}</span>
            </div>
            <div class="actions-wrapper">
                <div class="action-sq-btn btn-accept" title="Aprobar"><div class="btn-icon-mask"></div></div>
                <div class="action-sq-btn btn-trash" title="Rechazar y Eliminar"><div class="btn-icon-mask"></div></div>
            </div>
        `;

        // APROBAR
        li.querySelector('.btn-accept').addEventListener('click', async () => {
            await fetch(`/api/admin/user/${u.id}/status`, {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({status: 'aprobado'})
            });
            loadAdminData();
        });

        // RECHAZAR (ELIMINAR)
        li.querySelector('.btn-trash').addEventListener('click', async () => {
            if(confirm(`¿Rechazar solicitud de ${u.username} y borrar datos?`)) {
                await deleteUser(u.id);
            }
        });
        ul.appendChild(li);
    });
}

// Función auxiliar para llamar a la API de borrado
async function deleteUser(id) {
    try {
        const res = await fetch(`/api/admin/user/${id}/delete`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        const data = await res.json();

        if (data.error) {
            alert("Error: " + data.error);
        } else {
            loadAdminData(); // Recargar lista
        }
    } catch(e) {
        console.error("Error deleting", e);
        alert("Error de conexión");
    }
}