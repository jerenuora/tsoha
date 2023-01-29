from app import app
from flask import redirect, render_template, request, session, flash

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
    return render_template("threads.html", threads=threads, forum_id=id)

@app.route("/forum/thread/<int:id>")
def messages_view(id):
    sql = """SELECT id, writer, message, date, thread_id
    FROM messages WHERE thread_id=:id"""
    result = db.session.execute(text(sql), {"id":id})
    messages = result.fetchall()
    return render_template("messages.html", messages=messages, thread_id=id)

@app.route("/loginpage")
def loginpage():
    return render_template("loginpage.html")


@app.route("/login",methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    sql = "SELECT id, password FROM users WHERE username=:username"
    result = db.session.execute(text(sql), {"username":username})
    user = result.fetchone()    

    if not user:
            flash("Väärä käyttäjänimi")
            return redirect("/loginpage")
    else:
        hash_value = user.password
        if check_password_hash(hash_value, password):
                session["username"] = username
                return redirect("/")
        else:
            flash("Väärä salasana")
            return redirect("/loginpage")

 
 
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

@app.route("/postmessage/<int:id>",methods=["POST"])
def postmessage(id):
    message = request.form["message"]
    writer = session["username"]
    thread_id = id
    sql = "INSERT INTO messages (writer, message, thread_id) VALUES (:writer, :message, :thread_id)"

    db.session.execute(text(sql), {"writer":writer, "message":message, "thread_id":thread_id})
    db.session.commit()
    return redirect(request.referrer)

@app.route("/postthread/<int:id>",methods=["POST"])
def postthread(id):
    title = request.form["title"]
    message = request.form["message"]
    writer = session["username"]
    sql = "INSERT INTO threads (title, owner, forum_id) VALUES (:title, :owner, :forum_id)"
    db.session.execute(text(sql), {"title":title, "owner":writer, "forum_id":id})
    db.session.commit()

    sql = "SELECT MAX(id) FROM threads WHERE forum_id=:id"
    result = db.session.execute(text(sql), {"id":id})
    thread_id = result.fetchall()

    sql = "INSERT INTO messages (writer, message, thread_id) VALUES (:writer, :message, :thread_id)"

    db.session.execute(text(sql), {"writer":writer, "message":message, "thread_id":thread_id[0][0]})
    db.session.commit()
    return redirect(request.referrer)
