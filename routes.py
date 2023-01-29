from app import app
from flask import render_template
from db import db
from sqlalchemy.sql import text

@app.route("/")
def index():
    sql = "SELECT id, name FROM forums"
    result = db.session.execute(text(sql))
    forums = result.fetchall()
    return render_template("index.html", forums=forums)

