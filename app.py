from flask import Flask, render_template
import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is missing. Add it to your .env file.")
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    return url


def get_student_names() -> list[str]:
    conn = psycopg2.connect(database_url())
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM students ORDER BY name")
            return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()


@app.route("/")
def index():
    names = get_student_names()
    return render_template("index.html", names=names)


if __name__ == "__main__":
    app.run(debug=True)
