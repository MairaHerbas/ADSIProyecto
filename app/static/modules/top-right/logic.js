(function() {
    const btn = document.getElementById('btn-open-pokedex');
    if(btn) {
        btn.addEventListener('click', () => {
            if(window.ModalSystem) {
                window.ModalSystem.open('pokedex');
            } else {
                console.error("El sistema modal no está cargado aún.");
            }
        });
    }
})();