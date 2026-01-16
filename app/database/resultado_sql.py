class ResultadoSQL:
    def __init__(self, filas):
        self.filas = filas
        self.indice = -1

    def next(self):
        """Mueve el cursor a la siguiente fila. Devuelve True si hay datos."""
        self.indice += 1
        return self.indice < len(self.filas)

    def getString(self, columna):
        """Obtiene el valor de una columna de la fila actual."""
        if 0 <= self.indice < len(self.filas):
            fila_actual = self.filas[self.indice]
            # Soportamos acceso por nombre (Row) o índice si fuera necesario
            return str(fila_actual[columna])
        return None