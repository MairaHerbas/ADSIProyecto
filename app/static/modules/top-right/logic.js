(function() {
    const btnOpen = document.getElementById('btn-open-pokedex');
    let pokemonsCache = [];

    // Listas fijas para rellenar los selects
    const TIPOS = ["normal","fire","water","electric","grass","ice","fighting","poison","ground","flying","psychic","bug","rock","ghost","dragon","steel","dark","fairy"];
    const GENS = ["Gen 1","Gen 2","Gen 3","Gen 4","Gen 5","Gen 6","Gen 7","Gen 8","Gen 9"];

    if(btnOpen) {
        btnOpen.addEventListener('click', abrirVentanaFlotante);
    } else {
        console.error("Botón Pokedex no encontrado.");
    }

    function abrirVentanaFlotante() {
        if(document.getElementById('fake-modal-pokedex')) return;

        // 1. Crear Overlay
        const overlay = document.createElement('div');
        overlay.id = 'fake-modal-pokedex';
        overlay.style.cssText = "position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,0.9); z-index:99999; display:flex; justify-content:center; align-items:center;";

        // 2. Crear Caja Principal
        const box = document.createElement('div');
        box.className = 'modal-body';
        box.style.cssText = "width:95%; max-width:1100px; height:85%; background:#2b2b2b; border-radius:10px; overflow:hidden; position:relative; box-shadow:0 0 50px rgba(0,0,0,1); border: 1px solid #444; display:flex; flex-direction:column;";

        // 3. FIX BOTÓN CERRAR: Creado independientemente y añadido al final
        const closeBtn = document.createElement('div');
        closeBtn.innerText = "×";
        closeBtn.style.cssText = "position:absolute; top:10px; right:20px; color:#aaa; font-size:40px; font-weight:bold; cursor:pointer; z-index:100000; line-height:0.8; height:40px; width:40px; text-align:center;";
        closeBtn.onmouseover = () => closeBtn.style.color = "white";
        closeBtn.onmouseout = () => closeBtn.style.color = "#aaa";

        // Evento directo al botón
        closeBtn.onclick = function(e) {
            e.stopPropagation(); // Evita que el clic traspase
            document.body.removeChild(overlay);
        };

        // Montamos el DOM
        overlay.appendChild(box);
        overlay.appendChild(closeBtn); // La X está fuera de la caja para asegurar clic, o dentro pero con z-index alto
        document.body.appendChild(overlay);

        iniciarInterfaz(box);
    }

    function iniciarInterfaz(container) {
        // Generar opciones de los selects
        const opsTipos = TIPOS.map(t => `<option value="${t}">${t.toUpperCase()}</option>`).join('');
        const opsGens = GENS.map(g => `<option value="${g}">${g}</option>`).join('');

        container.innerHTML = `
            <div class="dex-container">
                <div class="dex-sidebar">
                    <div class="dex-title">POKÉDEX NACIONAL</div>

                    <input type="text" id="dex-filter-name" class="dex-input" placeholder="Buscar Nombre..." autocomplete="off">

                    <div class="filter-group">
                        <select id="dex-filter-gen" class="dex-select">
                            <option value="">TODAS GEN</option>
                            ${opsGens}
                        </select>
                        <select id="dex-filter-type" class="dex-select">
                            <option value="">TODOS TIPOS</option>
                            ${opsTipos}
                        </select>
                    </div>

                    <div id="dex-list" class="dex-list">
                        <div style="padding:20px; text-align:center; color:#666;">Cargando...</div>
                    </div>
                </div>

                <div class="dex-main" id="dex-detail">
                    <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; color:#555;">
                        <img src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/poke-ball.png" style="width:100px; opacity:0.1; filter:grayscale(1);">
                        <p style="margin-top:20px; font-size:1.2rem;">SELECCIONA UN POKÉMON</p>
                    </div>
                </div>
            </div>
        `;

        // Asignar eventos de filtrado a los 3 inputs
        const inputs = ['dex-filter-name', 'dex-filter-gen', 'dex-filter-type'];
        inputs.forEach(id => {
            document.getElementById(id).addEventListener('input', aplicarFiltros);
        });

        cargarDatos();
    }

    async function cargarDatos() {
        try {
            const res = await fetch('/api/pokedex');
            if(!res.ok) throw new Error("Error API");
            const data = await res.json();

            pokemonsCache = data;
            renderizarLista(data);
        } catch (e) {
            console.error(e);
            document.getElementById('dex-list').innerHTML = "<div style='color:red; text-align:center'>Error de conexión</div>";
        }
    }

    function renderizarLista(lista) {
        const listContainer = document.getElementById('dex-list');
        listContainer.innerHTML = '';

        if(lista.length === 0) {
            listContainer.innerHTML = "<div style='text-align:center; padding:20px; color:#666'>Sin resultados</div>";
            return;
        }

        // Renderizado limitado a 50 para máxima velocidad al escribir
        const visibleList = lista.slice(0, 50);

        visibleList.forEach(poke => {
            const item = document.createElement('div');
            item.className = 'dex-item';

            // Icono de tipo pequeño
            const tipoPrincipal = poke.types[0];

            item.innerHTML = `
                <div style="display:flex; align-items:center; gap:10px;">
                    <img src="${poke.sprite}" style="width:30px; height:30px;">
                    <div>
                        <div style="font-weight:bold; color:${poke.owned ? '#81c784' : '#ccc'}">${poke.name}</div>
                        <div style="font-size:0.7rem; color:#666;">#${poke.id} • ${poke.generation}</div>
                    </div>
                </div>
                <div class="fake-toggle ${poke.owned ? 'owned' : ''}"></div>
            `;

            item.onclick = () => {
                document.querySelectorAll('.dex-item').forEach(el => el.classList.remove('active'));
                item.classList.add('active');
                mostrarDetalleCompleto(poke);
            };

            listContainer.appendChild(item);
        });
    }

    function aplicarFiltros() {
        const txtName = document.getElementById('dex-filter-name').value.toLowerCase();
        const txtGen = document.getElementById('dex-filter-gen').value;
        const txtType = document.getElementById('dex-filter-type').value;

        const filtrados = pokemonsCache.filter(p => {
            const matchName = p.name.toLowerCase().includes(txtName);
            const matchGen = txtGen === "" || p.generation === txtGen;
            const matchType = txtType === "" || p.types.includes(txtType);
            return matchName && matchGen && matchType;
        });

        renderizarLista(filtrados);
    }

    // --- NUEVA VISTA DETALLADA COMPLETA ---
    function mostrarDetalleCompleto(poke) {
        const container = document.getElementById('dex-detail');

        // Mapa de colores
        const typeColors = {
            fire: '#F08030', water: '#6890F0', grass: '#78C850', electric: '#F8D030',
            ice: '#98D8D8', fighting: '#C03028', poison: '#A040A0', ground: '#E0C068',
            flying: '#A890F0', psychic: '#F85888', bug: '#A8B820', rock: '#B8A038',
            ghost: '#705898', dragon: '#7038F8', steel: '#B8B8D0', fairy: '#EE99AC',
            normal: '#A8A878', dark: '#705848'
        };
        const mainColor = typeColors[poke.types[0]] || '#aaa';

        // Preparamos habilidades (vienen separadas por comas)
        const abilitiesHtml = poke.habilidades ? poke.habilidades.split(',').map(h =>
            `<span class="tag">${h}</span>`
        ).join('') : '<span style="color:#666">Desconocidas</span>';

        // Preparamos movimientos (mostramos los primeros 10)
        const movesList = poke.movimientos ? poke.movimientos.split(',') : [];
        const movesHtml = movesList.length > 0 ? movesList.slice(0, 12).map(m =>
            `<span class="tag" style="border-color:#444; background:#222;">${m}</span>`
        ).join('') + (movesList.length > 12 ? `<span class="tag" style="color:#888">+${movesList.length - 12} más</span>` : '')
        : 'Sin datos';

        container.innerHTML = `
            <div class="detail-header">
                <h1 style="color:${mainColor}; text-transform:uppercase; letter-spacing:4px; margin:0; font-size:2.5rem; text-shadow:0 2px 10px rgba(0,0,0,0.5);">${poke.name}</h1>
                <div style="margin-top:10px;">
                    ${poke.types.map(t => `<span class="tag" style="background:${typeColors[t]}; color:white; border:none; padding:5px 15px; font-weight:bold; text-transform:uppercase;">${t}</span>`).join('')}
                </div>

                <img src="${poke.sprite}" class="detail-img-lg">
            </div>

            <div class="info-grid">
                <div class="info-card">
                    <div class="info-title">Estadísticas Base</div>
                    ${crearBarra('HP', poke.stats.hp, '#FF5959')}
                    ${crearBarra('ATK', poke.stats.atk, '#F5AC78')}
                    ${crearBarra('DEF', poke.stats.def, '#FAE078')}
                    ${crearBarra('SPA', poke.stats.sp_atk, '#9DB7F5')}
                    ${crearBarra('SPD', poke.stats.sp_def, '#A7DB8D')}
                    ${crearBarra('SPE', poke.stats.spd, '#FA92B2')}
                    <div style="margin-top:10px; font-size:0.7rem; color:#666; text-align:center;">TOTAL: ${Object.values(poke.stats).reduce((a,b)=>a+b, 0)}</div>
                </div>

                <div class="info-card">
                    <div class="info-title">Datos Técnicos</div>
                    <div style="margin-bottom:15px;">
                        <span style="color:#aaa; display:block; font-size:0.75rem;">Generación</span>
                        <span style="font-size:1.1rem;">${poke.generation}</span>
                    </div>

                    <div class="info-title" style="margin-top:10px;">Habilidades</div>
                    <div style="line-height:1.5;">${abilitiesHtml}</div>
                </div>

                <div class="info-card" style="grid-column: span 2;">
                    <div class="info-title">Movimientos Principales</div>
                    <div style="display:flex; flex-wrap:wrap; gap:5px;">
                        ${movesHtml}
                    </div>
                </div>
            </div>
        `;
    }

    function crearBarra(lbl, val, col) {
        const pct = Math.min((val/200)*100, 100);
        return `
            <div class="stat-row">
                <span class="stat-lbl">${lbl}</span>
                <div class="stat-track"><div class="stat-fill" style="width:${pct}%; background:${col}; box-shadow:0 0 5px ${col};"></div></div>
                <span class="stat-num">${val}</span>
            </div>
        `;
    }

})();