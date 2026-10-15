import sqlite3

DB_NAME = "music_repertoire.db"

SUPER_CEDULAS = ["31021593", "19061394"]


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
  cursor.execute(
      "SELECT id FROM artists WHERE LOWER(name) = LOWER(?)", (artist_name,)
  )
  row = cursor.fetchone()
  if row:
    artist_id = row[0]
  else:
    cursor.execute("INSERT INTO artists (name) VALUES (?)", (artist_name,))
    conn.commit()
    artist_id = cursor.lastrowid
  conn.close()
  return artist_id


def create_user(
    cedula,
    username,
    password,
    role,
    chair=None,
    security_question=None,
    security_answer=None,
):
  conn = get_connection()
  cursor = conn.cursor()
  status = (
      "aprobado"
      if role == "profesor" or cedula in SUPER_CEDULAS
      else "pendiente"
  )

  try:
    cursor.execute(
        """
            INSERT INTO users (cedula, username, password, role, chair, status, security_question, security_answer) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cedula,
            username,
            password,
            role,
            chair,
            status,
            security_question,
            security_answer,
        ),
    )
    conn.commit()
    success = True
  except sqlite3.IntegrityError:
    success = False
  finally:
    conn.close()
  return success


def get_user_by_cedula(cedula):
  conn = get_connection()
  cursor = conn.cursor()
  cursor.execute(
      "SELECT id, cedula, username, password, role, chair, status,"
      " security_question, security_answer FROM users WHERE cedula = ?",
      (cedula,),
  )
  row = cursor.fetchone()
  conn.close()
  if row:
    return {
        "id": row[0],
        "cedula": row[1],
        "username": row[2],
        "password": row[3],
        "role": row[4],
        "chair": row[5],
        "status": row[6],
        "security_question": row[7],
        "security_answer": row[8],
    }
  return None


def get_pending_students():
  conn = get_connection()
  cursor = conn.cursor()
  cursor.execute(
      "SELECT id, cedula, username, chair FROM users WHERE role = 'alumno' AND"
      " status = 'pendiente'"
  )
  students = cursor.fetchall()
  conn.close()
  return students


def approve_student(student_id):
  conn = get_connection()
  cursor = conn.cursor()
  cursor.execute(
      "UPDATE users SET status = 'aprobado' WHERE id = ? AND role = 'alumno'",
      (student_id,),
  )
  conn.commit()
  conn.close()


def get_all_approved_students():
  conn = get_connection()
  cursor = conn.cursor()
  cursor.execute(
      "SELECT id, cedula, username, chair FROM users WHERE role = 'alumno' AND"
      " status = 'aprobado'"
  )
  students = cursor.fetchall()
  conn.close()
  return students


def get_students_by_chair():
  students = get_all_approved_students()
  chairs = {}
  for s in students:
    chair_name = s[3] if s[3] else "Sin Cátedra"
    if chair_name not in chairs:
      chairs[chair_name] = []
    chairs[chair_name].append(s)
  return chairs


def get_all_teachers():
  conn = get_connection()
  cursor = conn.cursor()
  cursor.execute(
      "SELECT id, cedula, username FROM users WHERE role = 'profesor' ORDER BY id"
      " ASC"
  )
  teachers = cursor.fetchall()
  conn.close()
  return teachers


def delete_teacher(teacher_id):
  conn = get_connection()
  cursor = conn.cursor()
  cursor.execute("SELECT cedula FROM users WHERE id = ?", (teacher_id,))
  row = cursor.fetchone()
  if row and row[0] not in SUPER_CEDULAS:
    cursor.execute(
        "DELETE FROM users WHERE id = ? AND role = 'profesor'", (teacher_id,)
    )
    conn.commit()
  conn.close()


def update_password(cedula, new_password):
  conn = get_connection()
  cursor = conn.cursor()
  cursor.execute(
      "UPDATE users SET password = ? WHERE cedula = ?", (new_password, cedula)
  )
  conn.commit()
  conn.close()


def add_song(
    user_id,
    title,
    artist_name,
    instrument,
    key_signature,
    tempo,
    status,
    link,
    file_path,
):
  artist_id = get_or_create_artist(artist_name)
  conn = get_connection()
  cursor = conn.cursor()
  cursor.execute(
      """
        INSERT INTO songs (title, artist_id, instrument, key_signature, tempo, tab_or_score_link, file_path, status, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
      (
          title,
          artist_id,
          instrument,
          key_signature,
          tempo,
          link,
          file_path,
          status,
          user_id,
      ),
  )
  conn.commit()
  conn.close()


def list_songs_by_user(user_id):
  conn = get_connection()
  cursor = conn.cursor()
  cursor.execute(
      """
        SELECT s.id, s.title, COALESCE(a.name, 'Sin Artista'), COALESCE(s.instrument, 'Sin Instrumento'), 
               s.key_signature, s.tempo, s.status, s.tab_or_score_link, s.file_path
        FROM songs s
        LEFT JOIN artists a ON s.artist_id = a.id
        WHERE s.user_id = ?
    """,
      (user_id,),
  )
  songs = cursor.fetchall()
  conn.close()
  return songs


def add_assignment(
    teacher_id, student_id, title, artist, instrument, notes, link, file_path
):
  conn = get_connection()
  cursor = conn.cursor()
  cursor.execute(
      """
        INSERT INTO assignments (teacher_id, student_id, title, artist, instrument, notes, link, file_path, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pendiente')
    """,
      (
          teacher_id,
          student_id,
          title,
          artist,
          instrument,
          notes,
          link,
          file_path,
      ),
  )
  conn.commit()
  conn.close()


def get_student_assignments(student_id):
  conn = get_connection()
  cursor = conn.cursor()
  cursor.execute(
      """
        SELECT a.id, a.title, a.artist, a.instrument, a.notes, a.status, u.username, a.link, a.file_path
        FROM assignments a
        JOIN users u ON a.teacher_id = u.id
        WHERE a.student_id = ?
        ORDER BY a.id DESC
    """,
      (student_id,),
  )
  assignments = cursor.fetchall()
  conn.close()
  return assignments


def delete_student(student_id):
  conn = get_connection()
  cursor = conn.cursor()
  cursor.execute(
      "DELETE FROM users WHERE id = ? AND role = 'alumno'", (student_id,)
  )
  conn.commit()
  conn.close()


def delete_assignment(assignment_id):
  conn = get_connection()
  cursor = conn.cursor()
  cursor.execute("DELETE FROM assignments WHERE id = ?", (assignment_id,))
  conn.commit()
  conn.close()


def get_all_assignments():
  conn = get_connection()
  cursor = conn.cursor()
  cursor.execute("""
        SELECT a.id, a.title, a.artist, a.instrument, a.notes, a.status, u_teacher.username, u_student.username, a.link, a.file_path
        FROM assignments a
        JOIN users u_teacher ON a.teacher_id = u_teacher.id
        JOIN users u_student ON a.student_id = u_student.id
        ORDER BY a.id DESC
    """)
  assignments = cursor.fetchall()
  conn.close()
  return assignments