import sqlite3

DB_NAME = "music_repertoire.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Tabla de Artistas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS artists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );
    """)

    # 2. Tabla de Usuarios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cedula TEXT NOT NULL UNIQUE,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        role TEXT CHECK(role IN ('profesor', 'alumno')) NOT NULL,
        chair TEXT,
        status TEXT CHECK(status IN ('pendiente', 'aprobado')) DEFAULT 'aprobado',
        security_question TEXT,
        security_answer TEXT
    );
    """)

    # 3. Tabla de Canciones del Repertorio
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS songs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        artist_id INTEGER,
        instrument TEXT,
        key_signature TEXT,
        tempo INTEGER,
        tab_or_score_link TEXT,
        file_path TEXT,
        status TEXT CHECK(status IN ('Por aprender', 'En práctica', 'Dominado')) DEFAULT 'Por aprender',
        user_id INTEGER,
        FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE SET NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # 4. Tabla de Asignaciones
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id INTEGER,
        student_id INTEGER,
        title TEXT NOT NULL,
        artist TEXT,
        instrument TEXT,
        notes TEXT,
        link TEXT,
        file_path TEXT,
        status TEXT DEFAULT 'Pendiente',
        FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # MIGRACIÓN SEGURA: Añadir columnas si la tabla ya existía sin ellas
    try:
        cursor.execute("ALTER TABLE assignments ADD COLUMN link TEXT;")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE assignments ADD COLUMN file_path TEXT;")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()
    print("¡Base de datos inicializada y actualizada con éxito!")

if __name__ == "__main__":
    init_db()