import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "cambia-esta-clave-por-una-secreta"  # en un proyecto real esto no se sube a github

DATABASE = "datos.db"  # nombre del archivo donde SQLite guarda todo


# ---------- BASE DE DATOS ----------

def get_db():
    """Abre (o reutiliza) la conexión a la base de datos para esta petición."""
    if "db" not in g:  # "g" guarda datos solo durante la petición actual
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row  # permite acceder a los datos como p["columna"]
    return g.db


@app.teardown_appcontext
def close_db(exception):
    # Cierra la conexión automáticamente al terminar cada petición
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Crea las tablas si todavía no existen. Se ejecuta al iniciar la app."""
    db = sqlite3.connect(DATABASE)
    # Tabla de profesores/colegios registrados
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            colegio TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
        """
    )
    # Tabla de proyectos, cada uno ligado a un profesor (usuario_id)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            grupo TEXT NOT NULL,
            titulo TEXT NOT NULL,
            tema TEXT NOT NULL,
            avance TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
        """
    )
    db.commit()
    db.close()


# ---------- IDEAS PARA LA RULETA ----------
# Estas son las ideas de investigación que ofrece la página (paso 1 del "paso a paso")
# Esta lista viaja a index.html y de ahí al script.js de la ruleta
IDEAS_RULETA = [
    "Energías renovables en mi comunidad",
    "Cómo detectar el 'greenwashing' en la publicidad",
    "Huella de carbono de la dieta hiper-cárnica",
    "Lobby y cabildeo de la industria de combustibles fósiles",
    "Eficiencia energética en el colegio",
    "Consumo masivo y su impacto en el CO2",
    "Deforestación y pérdida de glaciares",
    "Mantas geotextiles: protegiendo el hielo",
]


# ---------- DECORADOR PARA PROTEGER RUTAS ----------

def login_requerido(vista):
    # Se pone arriba de una ruta (@login_requerido) para exigir sesión iniciada antes de entrar
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Primero debes iniciar sesión.")
            return redirect(url_for("login"))
        return vista(*args, **kwargs)
    return envoltura


# ---------- RUTAS ----------

@app.route("/")
def inicio():
    # Página principal: le pasa las ideas de la ruleta a index.html
    return render_template("index.html", ideas=IDEAS_RULETA)


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        # Toma los datos que llegan del formulario de registro.html
        nombre = request.form["nombre"].strip()
        colegio = request.form["colegio"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not nombre or not colegio or not email or not password:
            flash("Por favor completa todos los campos.")
            return redirect(url_for("registro"))

        db = get_db()
        # Revisa que no exista ya una cuenta con ese correo
        existe = db.execute("SELECT id FROM usuarios WHERE email = ?", (email,)).fetchone()
        if existe:
            flash("Ya existe una cuenta registrada con ese correo.")
            return redirect(url_for("registro"))

        # Guarda al profesor con la contraseña encriptada (nunca en texto plano)
        db.execute(
            "INSERT INTO usuarios (nombre, colegio, email, password_hash) VALUES (?, ?, ?, ?)",
            (nombre, colegio, email, generate_password_hash(password)),
        )
        db.commit()
        flash("¡Cuenta creada! Ahora puedes iniciar sesión.")
        return redirect(url_for("login"))

    return render_template("registro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        db = get_db()
        usuario = db.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()

        # Compara la contraseña ingresada contra el hash guardado
        if usuario is None or not check_password_hash(usuario["password_hash"], password):
            flash("Correo o contraseña incorrectos.")
            return redirect(url_for("login"))

        # Aquí es donde se guarda la sesión del profesor
        session["usuario_id"] = usuario["id"]
        session["usuario_nombre"] = usuario["nombre"]
        return redirect(url_for("panel"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    # Borra todos los datos de la sesión (cierra sesión)
    session.clear()
    flash("Sesión cerrada.")
    return redirect(url_for("inicio"))


@app.route("/panel")
@login_requerido
def panel():
    # Trae solo los proyectos que pertenecen al profesor con sesión iniciada
    db = get_db()
    proyectos = db.execute(
        "SELECT * FROM proyectos WHERE usuario_id = ? ORDER BY id DESC",
        (session["usuario_id"],),
    ).fetchall()
    return render_template("panel.html", proyectos=proyectos)


@app.route("/panel/agregar", methods=["POST"])
@login_requerido
def agregar_proyecto():
    # Recibe los datos del formulario "Agregar proyecto de un grupo" en panel.html
    grupo = request.form["grupo"].strip()
    titulo = request.form["titulo"].strip()
    tema = request.form["tema"].strip()
    avance = request.form.get("avance", "").strip()

    db = get_db()
    db.execute(
        "INSERT INTO proyectos (usuario_id, grupo, titulo, tema, avance) VALUES (?, ?, ?, ?, ?)",
        (session["usuario_id"], grupo, titulo, tema, avance),
    )
    db.commit()
    flash("Proyecto agregado.")
    return redirect(url_for("panel"))


if __name__ == "__main__":
    init_db()       # crea la base de datos si no existe
    app.run(debug=True)  # levanta el servidor en http://127.0.0.1:5000