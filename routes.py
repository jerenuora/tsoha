from app import app
from flask import redirect, render_template, request, session
from db import db
from sqlalchemy.sql import text

from werkzeug.security import check_password_hash, generate_password_hash

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

@app.route("/loginpage")
def loginpage():
    return render_template("loginpage.html")


@app.route("/login",methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    #TODO: implement username and password check

    session["username"] = username
    return redirect("/")
 
 
@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")


@app.route("/signuppage")
def signuppage():
    return render_template("signuppage.html")

@app.route("/signup",methods=["POST"])
def signup():
    username = request.form["username"]
    password = request.form["password"]
    hash_value = generate_password_hash(password)
    sql = "INSERT INTO users (username, password) VALUES (:username, :password)"
    db.session.execute(text(sql), {"username":username, "password":hash_value})
    db.session.commit()

    session["username"] = username
    return redirect("/")
