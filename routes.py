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

@app.route("/forum/<int:id>")
def thread_view(id):
    sql = "SELECT id, title, forum_id FROM threads WHERE forum_id=:id"
    result = db.session.execute(text(sql), {"id":id})
    threads = result.fetchall()
    print(threads)
    return render_template("threads.html", threads=threads)

@app.route("/forum/thread/<int:id>")
def messages_view(id):
    sql = """SELECT id, title, writer, message,  date, thread_id
    FROM messages WHERE thread_id=:id"""
    result = db.session.execute(text(sql), {"id":id})
    messages = result.fetchall()
    print(messages)
    return render_template("messages.html", messages=messages)
