import { loadProfileContent } from './js/profile.js';
import { loadTeamContent } from './js/team.js';
import { loadPokedexContent } from './js/pokedex.js'; // <--- IMPORTANTE

(function() {
    console.log("Módulo Modal (Orquestador) cargado.");

    const overlay = document.getElementById('modal-overlay');
    const contentArea = document.getElementById('modal-content');
    const closeBtn = document.getElementById('modal-close-btn');

    window.ModalSystem = {
        open: function(type, data) {
            overlay.classList.remove('hidden');
            contentArea.innerHTML = ''; 
            
            if (type === 'profile') {
                loadProfileContent(contentArea);
            } 
            else if (type === 'team') {
                loadTeamContent(data, contentArea, false);
            }
            else if (type === 'team-new') {
                const newTeam = { id: null, name: "", members: [], pokemon_count: 0 };
                loadTeamContent(newTeam, contentArea, true);
            }
            else if (type === 'pokedex') { 
                // --- NUEVO CASO ---
                loadPokedexContent(contentArea);
            }
        },
        close: closeModal
    };

    function closeModal() {
        overlay.classList.add('hidden');
        contentArea.innerHTML = '';
        window.dispatchEvent(new CustomEvent('app-data-refresh'));
    }

    overlay.addEventListener('click', (e) => { if(e.target === overlay) closeModal(); });
    closeBtn.addEventListener('click', closeModal);
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });
})();