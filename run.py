import mimetypes # <--- 1. Importar esto
from app import create_app

# --- 2. Añadir configuración de Windows AQUÍ ---
# Esto evita que el navegador bloquee tus estilos CSS o scripts JS
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')
# -----------------------------------------------
#commit
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)