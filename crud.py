import sqlite3

DB_NAME = "music_repertoire.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def get_or_create_artist(artist_name):
    if not artist_name:
        return None
    artist_name = artist_name.strip()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM artists WHERE LOWER(name) = LOWER(?)", (artist_name,))
    row = cursor.fetchone()
    if row:
        artist_id = row[0]
    else:
        cursor.execute("INSERT INTO artists (name) VALUES (?)", (artist_name,))
        conn.commit()
        artist_id = cursor.lastrowid
    conn.close()
    return artist_id

def create_user(username, password, role, chair=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password, role, chair) VALUES (?, ?, ?, ?)", 
                       (username, password, role, chair))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    finally:
        conn.close()
    return success

def get_user_by_username(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role, chair FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "username": row[1], "role": row[2], "chair": row[3]}
    return None

def verify_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def get_all_students():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, chair FROM users WHERE role = 'alumno'")
    students = cursor.fetchall()
    conn.close()
    return students

def get_all_teachers():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE role = 'profesor' ORDER BY id ASC")
    teachers = cursor.fetchall()
    conn.close()
    return teachers

def delete_teacher(teacher_id):
    conn = get_connection()
    cursor = conn.cursor()
    # Evitar borrar al profesor ID 1 (el superusuario principal)
    if int(teacher_id) != 1:
        cursor.execute("DELETE FROM users WHERE id = ? AND role = 'profesor'", (teacher_id,))
        conn.commit()
    conn.close()

def add_song(title, artist_name, instrument, key_signature, tempo, link, file_path, status, user_id):
    artist_id = get_or_create_artist(artist_name)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO songs (title, artist_id, instrument, key_signature, tempo, tab_or_score_link, file_path, status, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (title, artist_id, instrument, key_signature, tempo, link, file_path, status, user_id))
    conn.commit()
    conn.close()

def list_songs_by_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.id, s.title, COALESCE(a.name, 'Sin Artista'), COALESCE(s.instrument, 'Sin Instrumento'), 
               s.key_signature, s.tempo, s.status, s.tab_or_score_link, s.file_path
        FROM songs s
        LEFT JOIN artists a ON s.artist_id = a.id
        WHERE s.user_id = ?
    """, (user_id,))
    songs = cursor.fetchall()
    conn.close()
    return songs

def add_assignment(teacher_id, student_id, title, artist, instrument, notes, link, file_path):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO assignments (teacher_id, student_id, title, artist, instrument, notes, link, file_path, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pendiente')
    """, (teacher_id, student_id, title, artist, instrument, notes, link, file_path))
    conn.commit()
    conn.close()

def get_student_assignments(student_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id, a.title, a.artist, a.instrument, a.notes, a.status, u.username, a.link, a.file_path
        FROM assignments a
        JOIN users u ON a.teacher_id = u.id
        WHERE a.student_id = ?
    """, (student_id,))
    assignments = cursor.fetchall()
    conn.close()
    return assignments