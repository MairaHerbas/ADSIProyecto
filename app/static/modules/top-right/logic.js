(function() {
    const btnOpen = document.getElementById('btn-test-pokedex') || document.getElementById('btn-open-pokedex');
    let pokemonsCache = [];

    const TIPOS = ["normal","fire","water","electric","grass","ice","fighting","poison","ground","flying","psychic","bug","rock","ghost","dragon","steel","dark","fairy"];
    const GENS = ["Gen 1","Gen 2","Gen 3","Gen 4","Gen 5","Gen 6","Gen 7","Gen 8","Gen 9"];

    if(btnOpen) btnOpen.addEventListener('click', abrirVentanaFlotante);

    function abrirVentanaFlotante() {
        if(document.getElementById('fake-modal-pokedex')) return;

        const overlay = document.createElement('div');
        overlay.id = 'fake-modal-pokedex';
        overlay.style.cssText = "position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,0.9); z-index:99999; display:flex; justify-content:center; align-items:center;";

        const box = document.createElement('div');
        box.className = 'modal-body';
        box.style.cssText = "width:95%; max-width:1100px; height:85%; background:#2b2b2b; border-radius:10px; overflow:hidden; position:relative; border: 1px solid #444; display:flex; flex-direction:column;";

        const closeBtn = document.createElement('div');
        closeBtn.innerText = "×";
        closeBtn.style.cssText = "position:absolute; top:10px; right:20px; color:#aaa; font-size:40px; font-weight:bold; cursor:pointer; z-index:100000; line-height:0.8;";
        closeBtn.onclick = (e) => { e.stopPropagation(); document.body.removeChild(overlay); };

        overlay.appendChild(box);
        overlay.appendChild(closeBtn);
        document.body.appendChild(overlay);

        iniciarInterfaz(box);
    }

    function iniciarInterfaz(container) {
        const opsT = TIPOS.map(t=>`<option value="${t}">${t.toUpperCase()}</option>`).join('');
        const opsG = GENS.map(g=>`<option value="${g}">${g}</option>`).join('');

        container.innerHTML = `
            <div class="dex-container">
                <div class="dex-sidebar">
                    <div class="dex-title">POKÉDEX</div>
                    <input type="text" id="dex-search" class="dex-input" placeholder="Nombre..." autocomplete="off">
                    <div class="filter-group">
                        <select id="dex-gen" class="dex-select"><option value="">GEN</option>${opsG}</select>
                        <select id="dex-type" class="dex-select"><option value="">TIPO</option>${opsT}</select>
                    </div>
                    <div id="dex-list" class="dex-list"><div style="text-align:center; padding:20px; color:#666;">Cargando...</div></div>
                </div>
                <div class="dex-main" id="dex-detail">
                    <div style="display:flex; justify-content:center; align-items:center; height:100%; color:#555;">SELECCIONA UN POKÉMON</div>
                </div>
            </div>
        `;
        ['dex-search','dex-gen','dex-type'].forEach(id => document.getElementById(id).addEventListener('input', filtrar));
        cargarDatos();
    }

    async function cargarDatos() {
        try {
            const res = await fetch('/api/pokedex');
            const data = await res.json();
            pokemonsCache = data;
            renderLista(data);
        } catch(e) { console.error(e); }
    }

    function renderLista(lista) {
        const div = document.getElementById('dex-list');
        div.innerHTML = '';
        lista.slice(0, 50).forEach(p => {
            const item = document.createElement('div');
            item.className = 'dex-item';
            item.id = `list-item-${p.id}`;
            item.innerHTML = `
                <div><strong style="color:${p.owned?'#81c784':'#ccc'}">${p.name}</strong> <small style="color:#666">${p.generation}</small></div>
                <div class="fake-toggle ${p.owned?'owned':''}"></div>
            `;
            item.onclick = () => {
                document.querySelectorAll('.dex-item').forEach(e=>e.classList.remove('active'));
                item.classList.add('active');
                mostrarDetalle(p);
            };
            div.appendChild(item);
        });
    }

    function filtrar() {
        const txt = document.getElementById('dex-search').value.toLowerCase();
        const gen = document.getElementById('dex-gen').value;
        const typ = document.getElementById('dex-type').value;
        const res = pokemonsCache.filter(p =>
            p.name.toLowerCase().includes(txt) &&
            (gen==="" || p.generation===gen) &&
            (typ==="" || p.types.includes(typ))
        );
        renderLista(res);
    }

    function mostrarDetalle(p) {
        const box = document.getElementById('dex-detail');
        const colors = {fire:'#F08030',water:'#6890F0',grass:'#78C850',electric:'#F8D030',default:'#aaa'};
        const color = colors[p.types[0]] || '#aaa';

        // --- RECUPERADO: Procesar Habilidades ---
        const abilitiesHtml = p.habilidades ? p.habilidades.split(',').map(h =>
            `<span class="tag">${h}</span>`
        ).join('') : '<span style="color:#666">Desconocidas</span>';

        box.innerHTML = `
            <div class="detail-header">
                <h1 style="color:${color}; text-transform:uppercase; margin:0;">${p.name}</h1>
                <div>${p.types.map(t=>`<span class="tag" style="background:${color}; color:white;">${t}</span>`).join('')}</div>
                <img src="${p.sprite}" class="detail-img-lg">
            </div>

            <div class="info-grid">
                <div class="info-card">
                    <strong style="display:block; border-bottom:1px solid #444; margin-bottom:10px; padding-bottom:5px; color:#888;">ESTADÍSTICAS</strong>
                    ${Object.entries(p.stats).map(([k,v])=>`
                        <div class="stat-row">
                            <span style="width:40px; color:#aaa;">${k.toUpperCase().slice(0,3)}</span>
                            <div class="stat-track"><div class="stat-fill" style="width:${Math.min(v/2,100)}%; background:${color}"></div></div>
                            <span>${v}</span>
                        </div>
                    `).join('')}
                </div>

                <div class="info-card">
                    <strong style="display:block; border-bottom:1px solid #444; margin-bottom:10px; padding-bottom:5px; color:#888;">DATOS TÉCNICOS</strong>
                    <div style="margin-bottom:15px;">
                        <span style="color:#aaa; display:block; font-size:0.75rem;">Generación</span>
                        <span style="font-size:1.1rem;">${p.generation}</span>
                    </div>
                    <strong style="display:block; border-bottom:1px solid #444; margin-bottom:10px; padding-bottom:5px; color:#888; margin-top:15px;">HABILIDADES</strong>
                    <div style="line-height:1.6;">${abilitiesHtml}</div>
                </div>

                <div class="info-card" style="grid-column:span 2;">
                    <strong style="display:block; border-bottom:1px solid #444; margin-bottom:10px; padding-bottom:5px; color:#888;">MOVIMIENTOS</strong>
                    <div id="moves-box" style="display:flex; flex-wrap:wrap; gap:5px;"></div>
                </div>

                <div class="capture-container">
                    <span class="capture-label" id="cap-lbl" style="color:${p.owned?'#4caf50':'#aaa'}">${p.owned?'CAPTURADO':'NO CAPTURADO'}</span>
                    <label class="switch">
                        <input type="checkbox" id="btn-cap" ${p.owned?'checked':''}>
                        <span class="slider"></span>
                    </label>
                </div>
            </div>
        `;

        // LÓGICA DE MOVIMIENTOS
        const moves = p.movimientos ? p.movimientos.split(',') : [];
        const renderM = (all) => {
            const list = all ? moves : moves.slice(0, 15);
            let html = list.map(m=>`<span class="tag">${m}</span>`).join('');
            if(!all && moves.length > 15) html += `<span id="more-moves" class="tag" style="cursor:pointer; background:#666; color:white;">+${moves.length-15} MÁS</span>`;
            else if(all) html += `<span id="less-moves" class="tag" style="cursor:pointer; background:#444; color:#aaa;">VER MENOS</span>`;
            document.getElementById('moves-box').innerHTML = html;
            if(document.getElementById('more-moves')) document.getElementById('more-moves').onclick = () => renderM(true);
            if(document.getElementById('less-moves')) document.getElementById('less-moves').onclick = () => renderM(false);
        };
        renderM(false);

        // LÓGICA DE CAPTURA
        document.getElementById('btn-cap').addEventListener('change', async function() {
            const lbl = document.getElementById('cap-lbl');
            lbl.innerText = "GUARDANDO...";
            try {
                const res = await fetch('/api/pokedex/capture', {
                    method: 'POST',
                    headers: {'Content-Type':'application/json'},
                    body: JSON.stringify({pokemon_id: p.id})
                });
                const ret = await res.json();
                if(ret.success) {
                    p.owned = ret.captured;
                    lbl.innerText = ret.captured ? "CAPTURADO" : "NO CAPTURADO";
                    lbl.style.color = ret.captured ? "#4caf50" : "#aaa";

                    const listItem = document.getElementById(`list-item-${p.id}`);
                    if(listItem) {
                        const toggle = listItem.querySelector('.fake-toggle');
                        const name = listItem.querySelector('strong');
                        if(ret.captured) { toggle.classList.add('owned'); name.style.color = '#81c784'; }
                        else { toggle.classList.remove('owned'); name.style.color = '#ccc'; }
                    }
                }
            } catch(e) { console.error(e); this.checked = !this.checked; }
        });
    }
})();