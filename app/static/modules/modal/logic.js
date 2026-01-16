// Imports dinámicos
let loadProfile, loadTeam, loadPokedex;
(async () => {
    try { loadProfile = (await import('./js/profile.js')).loadProfileContent; } catch(e){}
    try { loadTeam = (await import('./js/team.js')).loadTeamContent; } catch(e){}
    try { loadPokedex = (await import('./js/pokedex.js')).loadPokedexContent; } catch(e){}
})();

(function() {
    console.log("🟢 Modal System v4.0 (Centered)");

    const overlay = document.getElementById('modal-overlay');
    const contentArea = document.getElementById('modal-content');

    let isLocked = false;

    window.ModalSystem = {
        open: function(type, data) {
            if (!overlay) return;

            overlay.classList.remove('hidden');
            contentArea.innerHTML = '';

            if (type === 'auth') {
                isLocked = true;
                // Login usa su propia clase (definida en el HTML template)
                loadAuthFromTemplate(contentArea);
            }
            else {
                isLocked = false;
                // Apps usan el marco de ventana centrada
                createWindowFrame(contentArea, type, data);
            }
        },
        close: closeModal
    };

    function createWindowFrame(container, type, data) {
        // Marco de la ventana
        const frame = document.createElement('div');
        frame.className = 'modal-window-frame'; // Clase CSS que define el tamaño 85%

        // Botón cerrar
        const closeBtn = document.createElement('button');
        closeBtn.className = 'window-close-btn';
        closeBtn.innerHTML = '×';
        closeBtn.onclick = closeModal;
        frame.appendChild(closeBtn);

        // Contenido interno
        const innerContent = document.createElement('div');
        innerContent.className = 'window-inner-content';
        frame.appendChild(innerContent);

        container.appendChild(frame);

        // Cargar módulos
        if (type === 'profile' && loadProfile) loadProfile(innerContent);
        else if (type === 'team' && loadTeam) loadTeam(data, innerContent, false);
        else if (type === 'team-new' && loadTeam) loadTeam({ id: null, name: "", members: [], pokemon_count: 0 }, innerContent, true);
        else if (type === 'pokedex' && loadPokedex) loadPokedex(innerContent);
    }

    function closeModal() {
        if (isLocked) return;
        overlay.classList.add('hidden');
        contentArea.innerHTML = '';
        window.dispatchEvent(new CustomEvent('app-data-refresh'));
    }

    if(overlay) overlay.addEventListener('click', (e) => {
        // Cierra si clicas fuera de la ventana (.modal-window-frame)
        if(e.target === overlay || e.target === contentArea) closeModal();
    });

    function loadAuthFromTemplate(container) {
        const template = document.getElementById('auth-template');
        if (!template) return;
        const clone = template.content.cloneNode(true);
        container.appendChild(clone);

        // Lógica de Login
        const viewLogin = container.querySelector('#login-section');
        const viewRegister = container.querySelector('#register-section');

        container.querySelector('#btn-go-register').onclick = (e) => { e.preventDefault(); viewLogin.style.display='none'; viewRegister.style.display='block'; };
        container.querySelector('#btn-go-login').onclick = (e) => { e.preventDefault(); viewRegister.style.display='none'; viewLogin.style.display='block'; };

        container.querySelector('#form-login').onsubmit = async (e) => {
            e.preventDefault();
            const email = container.querySelector('#login-email').value;
            const password = container.querySelector('#login-password').value;
            try {
                const res = await fetch('/api/login', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({email, password}) });
                const d = await res.json();
                if(d.success) window.location.reload();
                else alert(d.error);
            } catch(err) { alert("Error"); }
        };

        container.querySelector('#form-register').onsubmit = async (e) => {
            e.preventDefault();
             const payload = {
                name: container.querySelector('#reg-name').value,
                username: container.querySelector('#reg-username').value,
                email: container.querySelector('#reg-email').value,
                password: container.querySelector('#reg-password').value
            };
            try {
                const res = await fetch('/api/register', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload) });
                const d = await res.json();
                if(d.success) { alert("Creado"); viewRegister.style.display='none'; viewLogin.style.display='block'; }
                else alert(d.error);
            } catch(err){}
        };
    }
})();