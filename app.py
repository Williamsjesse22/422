import os
from flask import Flask, render_template, request, redirect, send_from_directory, abort, session, url_for, flash
from functools import wraps
import pymysql
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "static/uploads"

# Session / auth settings
SECRET_KEY = os.getenv("SECRET_KEY", "change-this")
APP_USER = os.getenv("APP_USER")
APP_PASSWORD = os.getenv("APP_PASSWORD")
app.secret_key = SECRET_KEY

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = int(os.getenv("DB_PORT", "3306"))

def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        cursorclass=pymysql.cursors.DictCursor
    )

def ensure_table():
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS photos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            filename VARCHAR(255) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        if APP_USER and APP_PASSWORD and username == APP_USER and password == APP_PASSWORD:
            session['logged_in'] = True
            next_url = request.args.get('next') or url_for('index')
            return redirect(next_url)
        flash('Invalid username or password')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))


@app.route("/")
@login_required
def index():
    ensure_table()
    q = request.args.get("q", "").strip()
    conn = get_connection()
    with conn.cursor() as cursor:
        if q:
            like = f"%{q}%"
            cursor.execute(
                "SELECT filename, description FROM photos WHERE filename LIKE %s OR description LIKE %s ORDER BY id DESC",
                (like, like),
            )
        else:
            cursor.execute("SELECT filename, description FROM photos ORDER BY id DESC")
        photos = cursor.fetchall()
    conn.close()
    return render_template("index.html", photos=photos, q=q)


@app.route('/download/<path:filename>')
@login_required
def download(filename):
    # Only allow downloading files that exist in the DB to avoid exposing arbitrary files
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM photos WHERE filename = %s", (filename,))
            found = cursor.fetchone()
    finally:
        conn.close()

    if not found:
        abort(404)

    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)

@app.route("/upload", methods=["POST"])
@login_required
def upload():
    ensure_table()

    file = request.files.get("photo")
    description = request.form.get("description", "")

    if not file or file.filename == "":
        return redirect("/")

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO photos (filename, description) VALUES (%s, %s)",
            (file.filename, description)
        )
    conn.commit()
    conn.close()

    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
