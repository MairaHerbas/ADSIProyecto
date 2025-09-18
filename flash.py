import tkinter as tk
from tkinter import ttk
import flash

# Crear la ventana principal
root = tk.Tk()
root.title("Ejemplo de Tinker y Flash")
root.geometry("400x300")

# Crear una etiqueta para mostrar el mensaje
message_label = ttk.Label(root, text="Esta es una etiqueta de Tinker.", font=("Helvetica", 16))
message_label.pack(pady=20)


# Definir una función para cambiar el mensaje y usar un widget de Flash
def change_message():
    message_label.config(text="¡El mensaje ha sido cambiado!")

    # Ejemplo de uso de un widget de Flash (nota: Flash es una librería separada y su uso puede variar)
    # Por lo general, Flash se usa para efectos visuales o animaciones
    # y no es una librería de GUI completa como Tinker.

    # En este caso, asumimos que 'flash' tiene una clase Label similar.
    try:
        flash_widget = flash.Label(root, text="Este es un widget de Flash.", bg="lightblue")
        flash_widget.pack()
    except AttributeError:
        # En caso de que la librería 'flash' no tenga una clase Label,
        # puedes usar un mensaje de depuración.
        print("La librería 'flash' no tiene una clase 'Label' para este ejemplo.")


# Crear un botón que llame a la función 'change_message'
change_button = ttk.Button(root, text="Cambiar Mensaje", command=change_message)
change_button.pack()

# Iniciar el bucle principal de la aplicación
root.mainloop()