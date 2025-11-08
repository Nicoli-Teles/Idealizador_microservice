import sqlite3

def criar_tabelas():
    conexao = sqlite3.connect("banco.db")
    cursor = conexao.cursor()

    # Tabela de idealizadores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS idealizadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            github TEXT DEFAULT NULL,
            linkedin TEXT DEFAULT NULL,
            funcao TEXT DEFAULT Null,
            pais TEXT DEFAULT NULL,
            cidade TEXT DEFAULT NULL,
            sobre_mim TEXT DEFAULT NULL
        )
    ''')

    # Tabela de habilidades
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS habilidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            idealizador_id INTEGER,
            nome TEXT NOT NULL,
            FOREIGN KEY(idealizador_id) REFERENCES idealizadores(id)
        )
    ''')

    conexao.commit()
    conexao.close()
