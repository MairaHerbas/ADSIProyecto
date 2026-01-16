(function() {
    // --- VARIABLES GLOBALES DEL MÓDULO ---
    const btnOpen = document.getElementById('btn-open-pokedex');
    let pokemonsCache = []; // Caché local para filtrar rápido sin recargar BD

    // --- EVENTO PRINCIPAL: ABRIR EL MODAL ---
    if(btnOpen) {
        btnOpen.addEventListener('click', () => {
            if(window.ModalSystem) {
                // 1. Abrir la ventana modal vacía
                window.ModalSystem.open('pokedex');

                // 2. Inyectar la interfaz y cargar los datos
                // Usamos un pequeño timeout para asegurar que el modal ya existe en el DOM
                setTimeout(iniciarInterfazPokedex, 100);
            } else {
                console.error("Error: El sistema modal no está cargado.");
            }
        });
    }

    // --- FUNCIÓN DE INICIO E INYECCIÓN DE HTML ---
    function iniciarInterfazPokedex() {
        // Buscamos el cuerpo del modal (ajusta '.modal-body' si tu modal usa otra clase)
        const modalContainer = document.querySelector('.modal-body') || document.querySelector('.modal-content');

        if (!modalContainer) return;

        // Inyectamos el HTML de la Pokédex (Buscador + Grid)
        modalContainer.innerHTML = `
            <div class="pokedex-interface">
                <div class="dex-controls">
                    <button id="btn-sync-bd" class="btn btn-warning btn-sm" style="font-size:12px; font-weight:bold;">
                        ↻ Sincronizar (API Ext → BD)
                    </button>
                    <input type="text" id="dex-search" class="dex-search" placeholder="Buscar por nombre...">
                </div>
                <div id="dex-grid" class="dex-grid">
                    <div style="text-align:center; padding:20px; color:grey;">Cargando datos de la Base de Datos...</div>
                </div>
            </div>
        `;

        // Asignamos los eventos a los elementos recién creados
        document.getElementById('btn-sync-bd').addEventListener('click', sincronizarDatosExternos);
        document.getElementById('dex-search').addEventListener('keyup', filtrarPokemons);

        // Cargamos la lista inicial (Diagrama 2)
        cargarDesdeBD();
    }

    // =========================================================
    // IMPLEMENTACIÓN DE LOS DIAGRAMAS DE SECUENCIA
    // =========================================================

    /**
     * DIAGRAMA 1: Carga/Sincronización de datos (Seed)
     * Flujo: Botón -> Backend (Python) -> PokéAPI Externa -> Guardar en BD Local
     */
    async function sincronizarDatosExternos() {
        const btn = document.getElementById('btn-sync-bd');
        const textoOriginal = btn.innerText;

        btn.disabled = true;
        btn.innerText = "Descargando...";

        try {
            // Llamamos a TU backend, no a la API externa directamente
            const response = await fetch('/api/sincronizar');
            const data = await response.json();

            if (data.status === 'success') {
                alert("¡Sincronización completada! Datos guardados en BD local.");
                cargarDesdeBD(); // Refrescamos la vista con los nuevos datos
            } else {
                alert("Error al sincronizar: " + (data.msg || "Desconocido"));
            }
        } catch (error) {
            console.error("Error de red:", error);
            alert("Error de conexión con el servidor.");
        } finally {
            btn.disabled = false;
            btn.innerText = textoOriginal;
        }
    }

    /**
     * DIAGRAMA 2: Mostrar Lista (Carga Inicial)
     * Flujo: Vista -> Backend (Python) -> CONSULTA SQL (SELECT) -> Vista
     */
    async function cargarDesdeBD() {
        const grid = document.getElementById('dex-grid');

        try {
            // Petición al servidor para obtener lo que hay en SQL
            const response = await fetch('/api/pokedex');
            const data = await response.json();

            console.log(`Cargados ${data.length} pokemons desde la BD local.`);

            // Guardamos en memoria para el buscador
            pokemonsCache = data;

            // Dibujamos las tarjetas
            renderizarGrid(data);

        } catch (error) {
            console.error("Error cargando desde BD:", error);
            grid.innerHTML = '<div style="color:red; text-align:center;">Error al conectar con la Base de Datos.</div>';
        }
    }

    /**
     * DIAGRAMA 3: Filtrar Pokémons
     * Flujo: Usuario escribe -> Filtro en memoria -> Actualizar Vista
     */
    function filtrarPokemons(event) {
        const texto = event.target.value.toLowerCase();

        const filtrados = pokemonsCache.filter(poke =>
            poke.name.toLowerCase().includes(texto)
        );

        renderizarGrid(filtrados);
    }

    /**
     * DIAGRAMA 4: Marcar como Capturado
     * Flujo: Checkbox -> Backend (Python) -> INSERT/UPDATE SQL
     */
    async function toggleCaptura(pokemonId, checkbox, cardElement) {
        // Feedback visual inmediato (Optimistic UI)
        if (checkbox.checked) {
            cardElement.classList.add('captured');
            console.log(`Guardando captura de ID ${pokemonId} en BD...`);

            // Llamada real al backend para guardar
            try {
                await fetch('/api/pokedex/add', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ pokemon_id: pokemonId })
                });
            } catch (e) {
                console.error("Error guardando captura", e);
                // Si falla, revertimos visualmente
                checkbox.checked = false;
                cardElement.classList.remove('captured');
                alert("Error al guardar la captura.");
            }
        } else {
            cardElement.classList.remove('captured');
            // Aquí podrías implementar la lógica para "liberar" (borrar de BD) si quieres
        }
    }

    /**
     * DIAGRAMA 5: Ver Detalle
     * Flujo: Clic en carta -> Mostrar info detallada
     */
    function verDetalle(poke) {
        // Aquí podrías abrir otro modal o mostrar una alerta avanzada
        alert(`
            POKÉDEX NACIONAL - DETALLE
            --------------------------
            #${poke.id} - ${poke.name.toUpperCase()}
            Tipo: ${poke.type}
            Estado: ${poke.owned ? "Capturado" : "Salvaje"}

            [Aquí irían tus gráficos de estadísticas]
        `);
    }

    // --- FUNCIÓN AUXILIAR DE RENDERIZADO ---
    function renderizarGrid(lista) {
        const grid = document.getElementById('dex-grid');
        grid.innerHTML = ''; // Limpiamos contenido anterior

        if (lista.length === 0) {
            grid.innerHTML = '<div style="text-align:center; width:100%; padding:20px;">No se encontraron resultados.</div>';
            return;
        }

        lista.forEach(poke => {
            // Creamos la tarjeta
            const card = document.createElement('div');
            card.className = `dex-card ${poke.owned ? 'captured' : ''}`;

            // HTML Interno de la tarjeta
            card.innerHTML = `
                <input type="checkbox" class="capture-btn" title="Marcar como capturado" ${poke.owned ? 'checked' : ''}>
                <img src="${poke.sprite}" alt="${poke.name}" loading="lazy">
                <div style="font-weight:bold; font-size:12px; margin-top:5px; text-transform:capitalize;">${poke.name}</div>
                <div style="font-size:10px; color:grey;">#${poke.id}</div>
            `;

            // Evento Clic en la carta (Detalles)
            card.addEventListener('click', (e) => {
                // Evitamos que el clic en el checkbox abra el detalle
                if (e.target.type !== 'checkbox') {
                    verDetalle(poke);
                }
            });

            // Evento Clic en el Checkbox (Capturar)
            const checkbox = card.querySelector('input');
            checkbox.addEventListener('change', () => toggleCaptura(poke.id, checkbox, card));

            grid.appendChild(card);
        });
    }

})();