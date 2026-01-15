import sqlite3
# Asegúrate de que config.py esté en la raíz del proyecto
from config import Config

class Connection:

    def __init__(self):
        self.connection = sqlite3.connect(
            Config.DB_PATH,
            check_same_thread=False
        )
        self.connection.row_factory = sqlite3.Row


    def select(self, sentence, parameters=None):
        cursor = self.connection.cursor()
        if parameters:
            cursor.execute(sentence, parameters)
        else:
            cursor.execute(sentence)
        rows = cursor.fetchall()
        cursor.close()
        return rows


    def insert(self, sentence, parameters=None):
        cursor = self.connection.cursor()
        if parameters:
            cursor.execute(sentence, parameters)
        else:
            cursor.execute(sentence)
        self.connection.commit()
        # Capturamos el ID del último insertado (necesario para los diagramas)
        last_id = cursor.lastrowid
        cursor.close()
        return last_id


    def update(self, sentence, parameters=None):
        cursor = self.connection.cursor()
        if parameters:
            cursor.execute(sentence, parameters)
        else:
            cursor.execute(sentence)
        self.connection.commit()
        cursor.close()


    def delete(self, sentence, parameters=None):
        cursor = self.connection.cursor()
        if parameters:
            cursor.execute(sentence, parameters)
        else:
            cursor.execute(sentence)
        self.connection.commit()
        cursor.close()

# Instancia global para usar en la app
db = Connection()