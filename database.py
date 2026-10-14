import sqlite3

def init_db():
    conn = sqlite3.connect("music_repertoire.db")
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Tabla de Artistas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS artists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );
    """)

    # 2. Tabla de Usuarios (con cédula única, rol, estado de aprobación y recuperación)
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

    conn.commit()
    conn.close()
    print("¡Base de datos actualizada con cédula, aprobaciones y recuperación!")

if __name__ == "__main__":
    init_db()