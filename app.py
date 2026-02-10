import os
from flask import Flask, render_template, request, redirect
import pymysql
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "static/uploads"

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

@app.route("/")
def index():
    ensure_table()
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT filename, description FROM photos ORDER BY id DESC")
        photos = cursor.fetchall()
    conn.close()
    return render_template("index.html", photos=photos)

@app.route("/upload", methods=["POST"])
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
