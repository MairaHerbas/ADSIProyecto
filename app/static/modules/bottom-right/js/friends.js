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
        
        // 1. Guardar datos
        friendsCache = data.friends || [];
        pendingCache = data.pending || [];

        // 2. Renderizar inicial
        renderFriendsList(friendsCache);
        renderPendingList(pendingCache);

        // 3. Conectar Buscadores
        setupSearch('friends-search-input', friendsCache, renderFriendsList);
        setupSearch('pending-search-input', pendingCache, renderPendingList);

    } catch (e) { console.error(e); }
}

function setupSearch(inputId, dataArray, renderFunc) {
    const input = document.getElementById(inputId);
    if (!input) return;
    
    // Clonar para limpiar eventos previos
    const newInput = input.cloneNode(true);
    input.parentNode.replaceChild(newInput, input);
    newInput.value = '';
    
    newInput.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();
        const filtered = dataArray.filter(name => name.toLowerCase().includes(term));
        renderFunc(filtered);
    });
}

function renderFriendsList(names) {
    ulFriends.innerHTML = '';
    if(!names || names.length === 0) {
        ulFriends.innerHTML = '<li class="friend-item" style="justify-content:center"><span class="item-name" style="opacity:0.5; font-size:1cqw">Sin resultados</span></li>';
        return;
    }

    names.forEach(name => {
        const li = document.createElement('li');
        li.className = 'friend-item';
        li.innerHTML = `
            <span class="item-name">${name}</span>
            <button class="btn-remove-friend" data-name="${name}" title="Eliminar Amigo">
                <div class="btn-icon-mask"></div>
            </button>
        `;
        li.querySelector('.btn-remove-friend').addEventListener('click', (e) => handleRemoveFriend(e.currentTarget));
        ulFriends.appendChild(li);
    });
    setupScrollLogic(ulFriends);
}

function renderPendingList(names) {
    ulPending.innerHTML = '';
    if(!names || names.length === 0) { 
        ulPending.innerHTML = '<li class="friend-item" style="justify-content:center"><span class="item-name" style="opacity:0.5; font-size:1cqw">Sin resultados</span></li>'; 
        return;
    }
    
    names.forEach(name => {
        const li = document.createElement('li');
        li.className = 'friend-item';
        li.innerHTML = `
            <span class="item-name">${name}</span>
            <div class="actions-wrapper">
                <div class="action-sq-btn btn-accept" data-action="accept" data-name="${name}"><div class="btn-icon-mask"></div></div>
                <div class="action-sq-btn btn-reject" data-action="reject" data-name="${name}"><div class="btn-icon-mask"></div></div>
            </div>`;
        
        li.querySelectorAll('.action-sq-btn').forEach(btn => 
            btn.addEventListener('click', () => handleFriendAction(btn, btn.dataset.name, btn.dataset.action))
        );
        ulPending.appendChild(li);
    });
    setupScrollLogic(ulPending);
}

// --- ACCIONES ---

async function handleRemoveFriend(btn) {
    const name = btn.dataset.name;
    const li = btn.closest('.friend-item');
    try {
        const res = await fetch('/api/friends/remove', {
            method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({name})
        });
        const data = await res.json();
        if(data.status === 'success') {
            li.style.maxHeight = '0'; li.style.opacity = '0'; li.style.margin = '0'; li.style.padding = '0';
            const idx = friendsCache.indexOf(name);
            if(idx > -1) friendsCache.splice(idx, 1);
            setTimeout(() => { li.remove(); }, 400);
        }
    } catch(e) { console.error(e); }
}

async function handleFriendAction(btn, name, action) {
    if(btn.dataset.processing) return;
    btn.dataset.processing = "true";
    const li = btn.closest('.friend-item');
    const span = li.querySelector('.item-name');
    span.classList.add(action === 'accept' ? 'text-success' : 'text-error');
    
    try {
        const endpoint = action === 'accept' ? '/api/friends/accept' : '/api/friends/reject';
        await fetch(endpoint, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({name}) });
        
        setTimeout(() => {
            li.style.maxHeight = '0'; li.style.opacity = '0'; li.style.margin = '0'; li.style.padding = '0';
            const idx = pendingCache.indexOf(name);
            if(idx > -1) pendingCache.splice(idx, 1);
            setTimeout(() => { 
                li.remove(); 
                if(action==='accept') loadFriendsData(); 
            }, 400);
        }, 300);
    } catch(e) { console.error(e); }
}