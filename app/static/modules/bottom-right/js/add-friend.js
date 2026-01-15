import { setupScrollLogic } from '../logic.js';

const ulAdd = document.getElementById('list-add-ul');
const searchInput = document.getElementById('user-search-input');
let availableUsers = [];
const sentRequests = new Set(); // Memoria local

export async function loadAvailableUsers() {
    try {
        const res = await fetch('/api/users/available');
        availableUsers = await res.json();
        filterAndRenderAddList("");
        
        // Listener
        if(searchInput) {
            // Clonamos el nodo para eliminar listeners viejos si recargamos modulo
            const newInput = searchInput.cloneNode(true);
            searchInput.parentNode.replaceChild(newInput, searchInput);
            newInput.addEventListener('input', (e) => filterAndRenderAddList(e.target.value));
            // Foco automatico si lo tenia
            if(document.activeElement === searchInput) newInput.focus();
        }
    } catch (e) { console.error(e); }
}

function filterAndRenderAddList(query) {
    // Referencia al elemento fresco (por si se reemplazó)
    const ul = document.getElementById('list-add-ul'); 
    ul.innerHTML = '';
    const q = query.toLowerCase();
    
    let filtered = availableUsers.filter(user => user.toLowerCase().includes(q));
    
    // Ordenar: Enviados primero
    filtered.sort((a, b) => {
        const isSentA = sentRequests.has(a);
        const isSentB = sentRequests.has(b);
        if (isSentA && !isSentB) return -1;
        if (!isSentA && isSentB) return 1;
        return a.localeCompare(b);
    });

    if (filtered.length === 0) {
        ul.innerHTML = '<li class="friend-item"><span class="item-name" style="opacity:0.5">Sin resultados</span></li>';
        return;
    }

    filtered.forEach(name => {
        const li = document.createElement('li');
        li.className = 'friend-item';
        
        const isSent = sentRequests.has(name);
        const btnClass = isSent ? 'btn-request sent' : 'btn-request';
        const btnText = isSent ? 'ENVIADO' : 'SOLICITAR';

        li.innerHTML = `
            <span class="item-name">${name}</span>
            <button class="${btnClass}">
                <span>${btnText}</span>
            </button>
        `;
        
        li.querySelector('button').addEventListener('click', (e) => handleRequest(e.currentTarget, name));
        ul.appendChild(li);
    });
    setupScrollLogic(ul);
}

async function handleRequest(btn, name) {
    const textSpan = btn.querySelector('span');
    
    // CANCELAR
    if (btn.classList.contains('sent')) {
        btn.disabled = true;
        try {
            await fetch('/api/friends/cancel', {
                method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name })
            });
            btn.classList.remove('sent');
            textSpan.textContent = "SOLICITAR";
            sentRequests.delete(name);
        } catch (e) { console.error(e); }
        btn.disabled = false;
        return;
    }

    // SOLICITAR
    btn.disabled = true; textSpan.textContent = "...";
    try {
        const res = await fetch('/api/friends/request', {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name })
        });
        const data = await res.json();
        if(data.status === 'success') {
            btn.classList.add('sent');
            textSpan.textContent = "ENVIADO";
            sentRequests.add(name);
        }
    } catch (e) { textSpan.textContent = "ERROR"; }
    btn.disabled = false;
}