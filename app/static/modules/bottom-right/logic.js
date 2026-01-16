import { setupToggles } from './js/toggles.js';
import { loadFriendsData } from './js/friends.js';
import { loadAvailableUsers } from './js/add-friend.js';
import { setupNotificationLogic, loadNotifications } from './js/notifications.js';
import { loadAdminData } from './js/admin.js';

console.log("Módulo BR (ES6 Modules) cargado.");

export function setupScrollLogic(element) {
    if(!element) return;
    const wrapper = element.parentElement;
    let t;
    const check = () => {
        if(element.scrollTop > 5) wrapper.classList.add('can-scroll-up');
        else wrapper.classList.remove('can-scroll-up');
        if(element.scrollTop + element.clientHeight < element.scrollHeight - 1)
            wrapper.classList.add('can-scroll-down');
        else wrapper.classList.remove('can-scroll-down');
    };
    element.addEventListener('scroll', () => {
        check(); element.classList.add('scrolling');
        clearTimeout(t); t = setTimeout(()=>element.classList.remove('scrolling'), 1000);
    });
    setTimeout(check, 100);
}

(async function init() {

    // 1. Verificar Rol Admin
    let isAdmin = false;
    try {
        const res = await fetch('/api/user-info');
        const data = await res.json();
        isAdmin = data.is_admin; // Asegúrate de que tu API devuelve 'is_admin'
    } catch(e) { console.error("Error check admin", e); }

    // 2. Configurar Botón Admin
    if (isAdmin) {
        const btnAdmin = document.getElementById('btn-tab-admin');
        const mainToggleGroup = document.getElementById('br-main-toggle-group');
        // Mostrar botón y ajustar estilos
        if(btnAdmin && mainToggleGroup) {
            btnAdmin.style.display = 'block';
            mainToggleGroup.classList.add('has-admin');
        }
        // Carga inicial silenciosa para tener datos listos
        loadAdminData();
    }

    // 3. Iniciar Toggles
    setupToggles({
        onMainToggle: (target) => {
            try {
                if(target === 'notifications') loadNotifications();
                // Al hacer clic en la pestaña ADMIN, recargamos los datos visualmente
                if(target === 'admin' && isAdmin) {
                    // Pequeño timeout para asegurar que el display:flex ya aplicó
                    setTimeout(() => loadAdminData(), 50);
                }
            } catch(e) { console.error("Error en toggle", e); }
        },
        onSubToggle: (page) => {
            const ul = page.querySelector('ul');
            if(ul) setupScrollLogic(ul);
        }
    });

    // 4. Cargas Iniciales
    try { setupNotificationLogic(); } catch(e) {}
    try { await loadFriendsData(); } catch(e) {}
    try { await loadAvailableUsers(); } catch(e) {}

})();