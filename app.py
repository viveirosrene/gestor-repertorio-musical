import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import crud
import database
import crud
app = Flask(__name__)
app.secret_key = "clave_secreta_gestor_musica"

UPLOAD_FOLDER = os.path.join("static", "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
except OSError:
    pass

database.init_db()

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
        assignments = crud.get_all_assignments()
        return render_template(
            "teacher_dashboard.html",
            username=username,
            chairs=chairs,
            teachers=teachers,
            pending_students=pending_students,
            is_superuser=is_superuser,
            SUPER_CEDULAS=crud.SUPER_CEDULAS,
            assignments=assignments,
        )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        cedula = request.form.get("cedula", "").strip()
        user = crud.get_user_by_cedula(cedula)

        if user:
            if user["status"] == 'pendiente':  # <-- Cambiado de user[4] a user["status"]
                flash("Tu cuenta de estudiante está pendiente por aprobación del profesor.", "error")
                return redirect(url_for("login"))

            session["user_id"] = user["id"]         # <-- user["id"]
            session["cedula"] = user["cedula"]       # <-- user["cedula"]
            session["username"] = user["username"]   # <-- user["username"]
            session["role"] = user["role"]           # <-- user["role"]

            flash(f"¡Bienvenido, {user['username']}!", "success")
            return redirect(url_for("index"))
        else:
            flash("Cédula no registrada. Por favor regístrate primero.", "error")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        cedula = request.form.get("cedula", "").strip()
        username = request.form.get("username", "").strip()
        role = request.form.get("role")
        chair = request.form.get("chair", "").strip()

        if crud.get_user_by_cedula(cedula):
            flash("Esta cédula ya se encuentra registrada.", "error")
            return redirect(url_for("register"))

        if role == "alumno":
            approved = 0
            msg = "Registro exitoso. Tu cuenta debe ser aprobada por un profesor para poder ingresar."
        else:
            approved = 1
            msg = "Profesor registrado exitosamente. Ya puedes iniciar sesión."

        crud.create_user(cedula, username, role, approved, chair)
        flash(msg, "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/recover", methods=["GET", "POST"])
def recover():
    if request.method == "POST":
        cedula = request.form.get("cedula", "").strip()
        new_username = request.form.get("new_username", "").strip()

        user = crud.get_user_by_cedula(cedula)
        if user:
            crud.update_username_by_cedula(cedula, new_username)
            flash("Nombre actualizado correctamente. Ya puedes ingresar.", "success")
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
    filename = None
    if score_file and score_file.filename != "":
        filename = secure_filename(score_file.filename)
        score_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    crud.add_song(
        session["user_id"],
        title,
        artist,
        instrument,
        key_sig,
        tempo,
        status,
        link,
        filename,
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
    filename = None
    if score_file and score_file.filename != "":
        filename = secure_filename(score_file.filename)
        score_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    # CAMBIO AQUÍ: add_assignment en lugar de create_assignment
    crud.add_assignment(
        session["user_id"],
        student_id,
        title,
        artist,
        instrument,
        notes,
        link,
        filename,
    )
    flash("Tarea asignada con éxito al alumno.", "success")
    return redirect(url_for("index"))


@app.route("/delete_assignment/<int:assignment_id>", methods=["POST"])
def delete_assignment(assignment_id):
    if "user_id" not in session or session.get("role") != "profesor":
        flash(
            "Acceso denegado. Solo los profesores pueden eliminar asignaciones.",
            "error",
        )
        return redirect(url_for("index"))

    crud.delete_assignment(assignment_id)
    flash("Asignación eliminada correctamente.", "success")
    return redirect(url_for("index"))


@app.route("/approve_student/<int:user_id>", methods=["POST"])
def approve_student(user_id):
    if (
        "user_id" not in session
        or session.get("cedula") not in crud.SUPER_CEDULAS
    ):
        flash("Acceso denegado.", "error")
        return redirect(url_for("index"))

    crud.approve_user(user_id)
    flash("Estudiante aprobado correctamente.", "success")
    return redirect(url_for("index"))


@app.route("/delete_student/<int:user_id>", methods=["POST"])
def delete_student(user_id):
    if (
        "user_id" not in session
        or session.get("cedula") not in crud.SUPER_CEDULAS
    ):
        flash("Acceso denegado.", "error")
        return redirect(url_for("index"))

    crud.delete_user(user_id)
    flash("Estudiante eliminado correctamente.", "success")
    return redirect(url_for("index"))


@app.route("/delete_teacher/<int:user_id>", methods=["POST"])
def delete_teacher(user_id):
    if (
        "user_id" not in session
        or session.get("cedula") not in crud.SUPER_CEDULAS
    ):
        flash("Acceso denegado.", "error")
        return redirect(url_for("index"))

    crud.delete_user(user_id)
    flash("Profesor eliminado correctamente.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)