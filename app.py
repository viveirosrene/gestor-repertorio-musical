import os
import uuid
import requests
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)
from werkzeug.utils import secure_filename
import crud
import database

app = Flask(__name__)
app.secret_key = "clave_secreta_gestor_musica"

# RUTA ABSOLUTA BLINDADA PARA RENDER Y LOCAL
basedir = os.path.abspath(os.path.dirname(__file__))
STATIC_FOLDER = os.path.join(basedir, "static")
UPLOAD_FOLDER = os.path.join(STATIC_FOLDER, "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# CONFIGURACIÓN SUPABASE STORAGE
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
BUCKET_NAME = "partituras"

# Forzar limpieza si 'uploads' existe por error como archivo plano y crear directorio seguro
try:
    if os.path.exists(UPLOAD_FOLDER) and not os.path.isdir(UPLOAD_FOLDER):
        os.remove(UPLOAD_FOLDER)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
except Exception as e:
    print(f"Error creando directorio uploads: {e}")

database.init_db()


def save_score_file(score_file):
    if not score_file or score_file.filename == "":
        return None

    original_filename = secure_filename(score_file.filename)
    ext = os.path.splitext(original_filename)[1]
    unique_filename = f"{uuid.uuid4()}{ext}"

    # 1. Subir a Supabase Storage si las variables existen en el servidor
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            storage_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{unique_filename}"
            headers = {
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "apiKey": SUPABASE_KEY,
                "Content-Type": score_file.mimetype or "application/octet-stream",
            }
            file_bytes = score_file.read()
            response = requests.post(storage_url, headers=headers, data=file_bytes)

            if response.status_code in (200, 201):
                return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{unique_filename}"
        except Exception as e:
            print(f"Error subiendo a Supabase Storage: {e}")

    # 2. Respaldo local si trabajas en entorno de desarrollo local sin variables
    upload_path = app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_path, exist_ok=True)
    score_file.seek(0)
    file_path = os.path.join(upload_path, unique_filename)
    score_file.save(file_path)
    return unique_filename


@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))

    role = session.get("role")
    username = session.get("username")
    cedula = session.get("cedula")
    is_superuser = cedula in crud.SUPER_CEDULAS

    if role == "alumno":
        songs = crud.list_songs_by_user(session["user_id"])
        assignments = crud.get_student_assignments(session["user_id"])
        return render_template(
            "student_dashboard.html",
            username=username,
            songs=songs,
            assignments=assignments,
            SUPER_CEDULAS=crud.SUPER_CEDULAS,
        )

    elif role == "profesor":
        chairs = crud.get_students_by_chair()
        teachers = crud.get_all_teachers() if is_superuser else []
        pending_students = crud.get_pending_students() if is_superuser else []
        raw_assignments = crud.get_all_assignments()

        # Agrupar asignaciones por cátedra del estudiante
        assignments_by_chair = {}
        for a in raw_assignments:
            chair_name = a[10] if a[10] else "Sin Cátedra"
            if chair_name not in assignments_by_chair:
                assignments_by_chair[chair_name] = []
            assignments_by_chair[chair_name].append(a)

        return render_template(
            "teacher_dashboard.html",
            username=username,
            chairs=chairs,
            teachers=teachers,
            pending_students=pending_students,
            is_superuser=is_superuser,
            SUPER_CEDULAS=crud.SUPER_CEDULAS,
            assignments_by_chair=assignments_by_chair,
        )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        cedula = request.form.get("cedula", "").strip()
        password = request.form.get("password", "").strip()
        user = crud.get_user_by_cedula(cedula)

        if user and user["password"] == password:
            if user["status"] == "pendiente":
                flash(
                    "Tu cuenta de estudiante está pendiente por aprobación del profesor.",
                    "error",
                )
                return redirect(url_for("login"))

            session["user_id"] = user["id"]
            session["cedula"] = user["cedula"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            flash(f"¡Bienvenido, {user['username']}!", "success")
            return redirect(url_for("index"))
        else:
            flash("Cédula o contraseña incorrecta.", "error")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        cedula = request.form.get("cedula", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        role = request.form.get("role")
        chair = request.form.get("chair", "").strip()
        sec_q = request.form.get("security_question", "").strip()
        sec_a = request.form.get("security_answer", "").strip()

        if crud.get_user_by_cedula(cedula):
            flash("Esta cédula ya se encuentra registrada.", "error")
            return redirect(url_for("register"))

        success = crud.create_user(
            cedula, username, password, role, chair, sec_q, sec_a
        )
        if success:
            if role == "alumno":
                msg = "Registro exitoso. Tu cuenta debe ser aprobada por un profesor para poder ingresar."
            else:
                msg = "Profesor registrado exitosamente. Ya puedes iniciar sesión. (Pendiente de aprobación si no es superusuario)"
            flash(msg, "success")
            return redirect(url_for("login"))
        else:
            flash("Error al registrar el usuario.", "error")

    return render_template("register.html")


@app.route("/reject_student/<int:student_id>", methods=["POST"])
def reject_student(student_id):
    if (
        "user_id" not in session
        or session.get("cedula") not in crud.SUPER_CEDULAS
        and session.get("role") != "profesor"
    ):
        flash("Acceso denegado.", "error")
        return redirect(url_for("index"))

    crud.delete_student(student_id)
    flash("Solicitud del estudiante rechazada y eliminada.", "info")
    return redirect(url_for("index"))


@app.route("/recover", methods=["GET", "POST"])
def recover():
    if request.method == "POST":
        cedula = request.form.get("cedula", "").strip()
        new_password = request.form.get("new_password", "").strip()

        user = crud.get_user_by_cedula(cedula)
        if user:
            crud.update_password(cedula, new_password)
            flash(
                "Contraseña actualizada correctamente. Ya puedes ingresar.",
                "success",
            )
            return redirect(url_for("login"))
        else:
            flash("Cédula no encontrada en el sistema.", "error")

    return render_template("recover.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Has cerrado sesión.", "success")
    return redirect(url_for("login"))


@app.route("/add_song", methods=["POST"])
def add_song():
    if "user_id" not in session:
        return redirect(url_for("login"))

    title = request.form.get("title")
    artist = request.form.get("artist_name")
    instrument = request.form.get("instrument")
    key_sig = request.form.get("key_signature")
    tempo = request.form.get("tempo")
    status = request.form.get("status")
    link = request.form.get("link")

    score_file = request.files.get("score_file")
    filename_or_url = save_score_file(score_file)

    crud.add_song(
        session["user_id"],
        title,
        artist,
        instrument,
        key_sig,
        tempo,
        status,
        link,
        filename_or_url,
    )
    flash("Canción agregada a tu repertorio.", "success")
    return redirect(url_for("index"))


@app.route("/assign_song", methods=["POST"])
def assign_song():
    if "user_id" not in session or session.get("role") != "profesor":
        flash("Acceso denegado.", "error")
        return redirect(url_for("index"))

    student_id = request.form.get("student_id")
    title = request.form.get("title")
    artist = request.form.get("artist")
    instrument = request.form.get("instrument")
    notes = request.form.get("notes")
    link = request.form.get("link")

    score_file = request.files.get("score_file")
    filename_or_url = save_score_file(score_file)

    crud.add_assignment(
        session["user_id"],
        student_id,
        title,
        artist,
        instrument,
        notes,
        link,
        filename_or_url,
    )
    flash("Tarea asignada con éxito al alumno.", "success")
    return redirect(url_for("index"))


@app.route("/delete_song/<int:song_id>", methods=["POST"])
def delete_song(song_id):
    if "user_id" not in session:
        flash("Acceso denegado.", "error")
        return redirect(url_for("login"))

    crud.delete_song(song_id, session["user_id"])
    flash("Canción eliminada de tu repertorio.", "success")
    return redirect(url_for("index"))


@app.route("/delete_assignment/<int:assignment_id>", methods=["POST"])
def delete_assignment(assignment_id):
    if "user_id" not in session:
        flash("Acceso denegado.", "error")
        return redirect(url_for("index"))

    crud.delete_assignment(assignment_id)
    flash("Asignación eliminada correctamente.", "success")
    return redirect(url_for("index"))


@app.route("/approve_student/<int:student_id>", methods=["POST"])
def approve_student(student_id):
    if (
        "user_id" not in session
        or session.get("cedula") not in crud.SUPER_CEDULAS
        and session.get("role") != "profesor"
    ):
        flash("Acceso denegado.", "error")
        return redirect(url_for("index"))

    crud.approve_student(student_id)
    flash("Estudiante aprobado correctamente.", "success")
    return redirect(url_for("index"))


@app.route("/delete_student/<int:user_id>", methods=["POST"])
def delete_student(user_id):
    if "user_id" not in session or session.get("cedula") not in crud.SUPER_CEDULAS:
        flash("Acceso denegado.", "error")
        return redirect(url_for("index"))

    crud.delete_user(user_id)
    flash("Estudiante eliminado correctamente.", "success")
    return redirect(url_for("index"))


@app.route("/delete_teacher/<int:user_id>", methods=["POST"])
def delete_teacher(user_id):
    if "user_id" not in session or session.get("cedula") not in crud.SUPER_CEDULAS:
        flash("Acceso denegado.", "error")
        return redirect(url_for("index"))

    crud.delete_teacher(user_id)
    flash("Profesor eliminado correctamente.", "success")
    return redirect(url_for("index"))


@app.route("/ping")
def ping():
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)