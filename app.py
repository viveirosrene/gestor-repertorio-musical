import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import crud
import database

app = Flask(__name__)
app.secret_key = "clave_secreta_super_segura"

UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

database.init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if crud.verify_user(username, password):
            user_data = crud.get_user_by_username(username)
            session["user_id"] = user_data["id"]
            session["username"] = user_data["username"]
            session["role"] = user_data["role"]
            return redirect(url_for("index"))
        else:
            flash("Usuario o contraseña incorrectos", "error")
            
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role")
        chair = request.form.get("chair") if role == "alumno" else None
        
        if crud.create_user(username, password, role, chair):
            flash("¡Registro exitoso! Inicia sesión.", "success")
            return redirect(url_for("login"))
        else:
            flash("El nombre de usuario ya existe.", "error")
            
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
        
    role = session["role"]
    user_id = session["user_id"]
    
    if role == "profesor":
        students = crud.get_all_students()
        teachers = crud.get_all_teachers()
        chairs_dict = {}
        for s in students:
            chair_name = s[2] or "General"
            if chair_name not in chairs_dict:
                chairs_dict[chair_name] = []
            chairs_dict[chair_name].append(s)
            
        # El primer profesor registrado (ID 1) es el superusuario
        is_superuser = (user_id == 1)
        
        return render_template("teacher_dashboard.html", 
                               username=session["username"], 
                               user_id=user_id,
                               chairs=chairs_dict, 
                               teachers=teachers, 
                               is_superuser=is_superuser)
    else:
        songs = crud.list_songs_by_user(user_id)
        assignments = crud.get_student_assignments(user_id)
        return render_template("student_dashboard.html", username=session["username"], songs=songs, assignments=assignments)

@app.route("/delete_teacher/<int:teacher_id>", methods=["POST"])
def delete_teacher(teacher_id):
    if "user_id" not in session or session["user_id"] != 1:
        flash("Acceso denegado. Solo el superusuario principal puede eliminar profesores.", "error")
        return redirect(url_for("index"))
        
    crud.delete_teacher(teacher_id)
    flash("Profesor eliminado correctamente del sistema.", "success")
    return redirect(url_for("index"))

@app.route("/add_song", methods=["POST"])
def add_song():
    if "user_id" not in session or session["role"] != "alumno":
        return redirect(url_for("login"))
        
    title = request.form.get("title")
    artist_name = request.form.get("artist_name")
    instrument = request.form.get("instrument")
    key_signature = request.form.get("key_signature")
    tempo = request.form.get("tempo")
    link = request.form.get("link")
    status = request.form.get("status")

    tempo = int(tempo) if tempo and tempo.isdigit() else None

    file_filename = None
    if 'score_file' in request.files:
        file = request.files['score_file']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            file_filename = filename

    crud.add_song(title, artist_name, instrument, key_signature, tempo, link, file_filename, status, session["user_id"])
    flash("¡Canción guardada exitosamente en tu repertorio!", "success")
    return redirect(url_for("index"))

@app.route("/assign_song", methods=["POST"])
def assign_song():
    if "user_id" not in session or session["role"] != "profesor":
        return redirect(url_for("login"))
        
    student_id = request.form.get("student_id")
    title = request.form.get("title")
    artist = request.form.get("artist")
    instrument = request.form.get("instrument")
    notes = request.form.get("notes")
    link = request.form.get("link")

    file_filename = None
    if 'score_file' in request.files:
        file = request.files['score_file']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            file_filename = filename

    if student_id:
        crud.add_assignment(session["user_id"], int(student_id), title, artist, instrument, notes, link, file_filename)
        flash("¡Asignación realizada y enviada al alumno correctamente!", "success")
    else:
        flash("Por favor selecciona un alumno válido.", "error")
        
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)