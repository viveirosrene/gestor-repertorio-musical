import os
import psycopg2
import sqlite3

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        conn = sqlite3.connect("music_repertoire.db")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    if DATABASE_URL:
        # 1. Crear tablas si no existen en PostgreSQL (Supabase)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS artists (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
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

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS songs (
            id SERIAL PRIMARY KEY,
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

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id SERIAL PRIMARY KEY,
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

        # 2. Migración automática de columnas por si la tabla ya existía
        migrations = [
            "ALTER TABLE assignments ADD COLUMN IF NOT EXISTS link TEXT;",
            "ALTER TABLE assignments ADD COLUMN IF NOT EXISTS file_path TEXT;",
            "ALTER TABLE assignments ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Pendiente';",
            "ALTER TABLE songs ADD COLUMN IF NOT EXISTS artist_id INTEGER;",
            "ALTER TABLE songs ADD COLUMN IF NOT EXISTS instrument TEXT;",
            "ALTER TABLE songs ADD COLUMN IF NOT EXISTS key_signature TEXT;",
            "ALTER TABLE songs ADD COLUMN IF NOT EXISTS tempo INTEGER;",
            "ALTER TABLE songs ADD COLUMN IF NOT EXISTS tab_or_score_link TEXT;",
            "ALTER TABLE songs ADD COLUMN IF NOT EXISTS file_path TEXT;",
            "ALTER TABLE songs ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Por aprender';",
            "ALTER TABLE songs ADD COLUMN IF NOT EXISTS user_id INTEGER;"
        ]
        for mig in migrations:
            try:
                cursor.execute(mig)
            except Exception:
                conn.rollback() # Ignorar si ya existe y continuar
    else:
        # Configuración SQLite local
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS artists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
        """)
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
    cursor.close()
    conn.close()
    print("¡Base de datos inicializada, migrada y conectada de forma automática!")

if __name__ == "__main__":
    init_db()