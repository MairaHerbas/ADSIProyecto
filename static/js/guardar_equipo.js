// 1. Esperamos a que toodo el contenido de la página (HTML) esté cargado.
document.addEventListener("DOMContentLoaded", function() {

    // 2. Buscamos el botón amarillo por su ID
    const confirmButton = document.getElementById("confirmButton");

    // 3. Añadimos un "escuchador de eventos" para el clic
    confirmButton.addEventListener("click", function() {

        // 4. Mostramos el mensaje pop-up (alert)
        alert("se han guardado los cambios correctamente :)");

    });

});