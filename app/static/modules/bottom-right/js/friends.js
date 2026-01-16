import { setupScrollLogic } from '../logic.js';

const ulFriends = document.getElementById('list-friends-ul');
const ulPending = document.getElementById('list-pending-ul');

// Cache para búsquedas locales
let friendsCache = [];
let pendingCache = [];

export async function loadFriendsData() {
    try {
        const res = await fetch('/api/friends/data');
        const data = await res.json();
        
        // 1. Guardar datos (Ahora son Arrays de Objetos)
        friendsCache = data.friends || [];
        pendingCache = data.pending || [];

        // 2. Renderizar inicial
        renderFriendsList(friendsCache);
        renderPendingList(pendingCache);

        // 3. Conectar Buscadores (Adaptados a objetos)
        setupSearch('friends-search-input', friendsCache, renderFriendsList);
        setupSearch('pending-search-input', pendingCache, renderPendingList);

    } catch (e) { console.error(e); }
}

// --- FUNCIÓN DE BÚSQUEDA ADAPTADA A OBJETOS ---
function setupSearch(inputId, dataArray, renderFunc) {
    const input = document.getElementById(inputId);
    if (!input) return;

    const newInput = input.cloneNode(true);
    input.parentNode.replaceChild(newInput, input);
    newInput.value = '';

    newInput.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();
        // FILTRO: Buscamos dentro de la propiedad .name
        const filtered = dataArray.filter(u => u.name.toLowerCase().includes(term));
        renderFunc(filtered);
    });
}

// --- RENDERIZAR AMIGOS ---
function renderFriendsList(list) {
    ulFriends.innerHTML = '';
    if (list.length === 0) {
        ulFriends.innerHTML = '<li class="friend-item" style="justify-content:center"><span class="item-name" style="opacity:0.5">Sin amigos aún</span></li>';
        return;
    }

    list.forEach(u => { // 'u' es el objeto {name: "Ash", status: "online"}
        const li = document.createElement('li');
        li.className = 'friend-item';

        li.innerHTML = `
            <span class="item-name">${u.name}</span> <div class="actions-wrapper">
                <button class="btn-remove-friend" title="Eliminar amigo">
                    <div class="btn-icon-mask"></div>
                </button>
            </div>
        `;

        // Evento Eliminar Amigo
        li.querySelector('.btn-remove-friend').addEventListener('click', () => {
             if(confirm(`¿Eliminar a ${u.name} de tus amigos?`)) {
                 removeFriend(u.name, li);
             }
        });

        ulFriends.appendChild(li);
    });
    setupScrollLogic(ulFriends);
}

// --- RENDERIZAR PENDIENTES ---
function renderPendingList(list) {
    ulPending.innerHTML = '';
    if (list.length === 0) {
        ulPending.innerHTML = '<li class="friend-item" style="justify-content:center"><span class="item-name" style="opacity:0.5">Sin solicitudes</span></li>';
        return;
    }

    list.forEach(u => { // 'u' es el objeto {name: "Gary"}
        const li = document.createElement('li');
        li.className = 'friend-item';

        li.innerHTML = `
            <span class="item-name">${u.name}</span> <div class="actions-wrapper">
                <div class="action-sq-btn btn-accept" title="Aceptar"><div class="btn-icon-mask"></div></div>
                <div class="action-sq-btn btn-reject" title="Rechazar"><div class="btn-icon-mask"></div></div>
            </div>
        `;

        // Pasamos u.name a las funciones de acción
        li.querySelector('.btn-accept').addEventListener('click', (e) => handleFriendAction(e.currentTarget, u.name, 'accept'));
        li.querySelector('.btn-reject').addEventListener('click', (e) => handleFriendAction(e.currentTarget, u.name, 'reject'));

        ulPending.appendChild(li);
    });
    setupScrollLogic(ulPending);
}

// --- LÓGICA DE ACCIONES (Actualizar Caché de Objetos) ---

async function removeFriend(name, li) {
    // Animación visual inmediata (UI Optimista)
    li.style.opacity = '0.5';

    try {
        // Llamada al servidor real
        const res = await fetch('/api/friends/remove', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ name: name })
        });

        const data = await res.json();

        if (data.status === 'success') {
            // Si el servidor confirma, borramos del todo
            li.style.maxHeight = '0';
            li.style.opacity = '0';
            li.style.margin = '0';

            // Borramos de la memoria caché local
            const idx = friendsCache.findIndex(u => u.name === name);
            if(idx > -1) friendsCache.splice(idx, 1);

            setTimeout(() => li.remove(), 300);
        } else {
            // Si falla, revertimos
            li.style.opacity = '1';
            alert("Error al eliminar: " + (data.message || "Desconocido"));
        }
    } catch(e) {
        console.error(e);
        li.style.opacity = '1';
        alert("Error de conexión");
    }
}

async function handleFriendAction(btn, name, action) {
    if(btn.dataset.processing) return;
    btn.dataset.processing = "true";
    const li = btn.closest('.friend-item');

    try {
        const endpoint = action === 'accept' ? '/api/friends/accept' : '/api/friends/reject';
        const res = await fetch(endpoint, {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({name}) // Enviamos el nombre al backend
        });

        const data = await res.json();

        if(data.status === 'success') {
            // Animación de salida
            li.style.opacity = '0';
            setTimeout(() => {
                li.remove();
                // Actualizar caché buscando por nombre
                const idx = pendingCache.findIndex(u => u.name === name);
                if(idx > -1) pendingCache.splice(idx, 1);

                // Si aceptamos, recargar todo para que salga en la lista de amigos
                if(action === 'accept') loadFriendsData();
            }, 300);
        }
    } catch(e) { console.error(e); }
}