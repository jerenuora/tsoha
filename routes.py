from app import app
from flask import redirect, render_template, request, session, flash, abort

from db import db
from sqlalchemy.sql import text
import secrets
from werkzeug.security import check_password_hash, generate_password_hash


@app.route("/")
def index():
    sql = "SELECT id, name FROM forums"
    result = db.session.execute(text(sql))
    forums = result.fetchall()

    sql = "SELECT count(title) FROM threads GROUP BY forum_id ORDER BY forum_id"
    result = db.session.execute(text(sql))
    threadcount = result.fetchall()

    sql = """SELECT count(M.message), max(date) FROM messages M, threads T, forums F
                WHERE M.thread_id = T.id and T.forum_id = F.id GROUP BY F.id ORDER BY F.id"""
    result = db.session.execute(text(sql))
    messagecount = result.fetchall()

    return render_template("index.html", forums=forums, threadcount=threadcount, messagecount=messagecount)


@app.route("/forum/<int:id>")
def thread_view(id):
    sql = "SELECT id, title, forum_id FROM threads WHERE forum_id=:id"
    result = db.session.execute(text(sql), {"id": id})
    threads = result.fetchall()
    sql = """SELECT count(M.message), max(date)  FROM messages M, threads T
            WHERE M.thread_id = T.id GROUP BY T.id ORDER BY T.id """
    result = db.session.execute(text(sql))
    messagecount = result.fetchall()

    return render_template("threads.html", threads=threads, forum_id=id, messagecount=messagecount)


@app.route("/forum/thread/<int:id>")
def messages_view(id):
    sql = """SELECT id, writer, message, date, thread_id
    FROM messages WHERE thread_id=:id"""
    result = db.session.execute(text(sql), {"id": id})
    messages = result.fetchall()
    return render_template("messages.html", messages=messages, thread_id=id)


@app.route("/loginpage")
def loginpage():
    return render_template("loginpage.html")


@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    if not username or not password:
        flash("Syotä kirjautumistiedot")
        return redirect("/loginpage")

    sql = "SELECT id, password FROM users WHERE username=:username"
    result = db.session.execute(text(sql), {"username": username})
    user = result.fetchone()


    if not user:
        flash("Väärä käyttäjänimi")
        return redirect("/loginpage")

    hash_value = user.password
    if not check_password_hash(hash_value, password):
        flash("Väärä salasana")
        return redirect("/loginpage")

    session["username"] = username
    session["csrf_token"] = secrets.token_hex(16)
    return redirect("/")


@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")


@app.route("/signuppage")
def signuppage():
    return render_template("signuppage.html")


@app.route("/signup", methods=["POST"])
def signup():
    username = request.form["username"]
    password = request.form["password"]
    password_confirmation = request.form["password_confirmation"]
    
    if not username or not password:
        flash("Täytä kaikki kentät")
        return redirect("/signuppage")
    if password != password_confirmation:
        flash("Salasanat eivät ole samat")
        return redirect("/signuppage")

    hash_value = generate_password_hash(password)
    sql = "INSERT INTO users (username, password) VALUES (:username, :password)"
    db.session.execute(
        text(sql), {"username": username, "password": hash_value})
    db.session.commit()

    session["username"] = username
    session["csrf_token"] = secrets.token_hex(16)
    return redirect("/")


@app.route("/postmessage/<int:id>", methods=["POST"])
def postmessage(id):
    message = request.form["message"]
    writer = session["username"]
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)

    thread_id = id
    sql = "INSERT INTO messages (writer, message, thread_id) VALUES (:writer, :message, :thread_id)"

    db.session.execute(
        text(sql), {"writer": writer, "message": message, "thread_id": thread_id})
    db.session.commit()
    return redirect(request.referrer)


@app.route("/postthread/<int:id>", methods=["POST"])
def postthread(id):
    title = request.form["title"]
    message = request.form["message"]
    writer = session["username"]
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)

    sql = "INSERT INTO threads (title, owner, forum_id) VALUES (:title, :owner, :forum_id)"
    db.session.execute(
        text(sql), {"title": title, "owner": writer, "forum_id": id})
    db.session.commit()

    sql = "SELECT MAX(id) FROM threads WHERE forum_id=:id"
    result = db.session.execute(text(sql), {"id": id})
    thread_id = result.fetchall()

    sql = "INSERT INTO messages (writer, message, thread_id) VALUES (:writer, :message, :thread_id)"

    db.session.execute(
        text(sql), {"writer": writer, "message": message, "thread_id": thread_id[0][0]})
    db.session.commit()
    return redirect(request.referrer)


@app.route("/searchpage")
def searchpage():
   return render_template("search.html")

@app.route("/search", methods=["GET"])
def search(): 
    searchword = request.args.get("searchword")
    sql = text("""SELECT id, writer, message, date, thread_id
    FROM messages WHERE LOWER(message) LIKE LOWER(:searchword)""")
    result = db.session.execute(sql, {"searchword":"%"+searchword+"%"})
    messages = result.fetchall()
    sql = text("""SELECT id, title, owner, forum_id
    FROM threads WHERE LOWER(title) LIKE LOWER(:searchword)""")
    result = db.session.execute(sql, {"searchword":"%"+searchword+"%"})
    threads = result.fetchall()

    return render_template("search.html", messages=messages, threads=threads)

@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)

    sql = text("DELETE FROM messages WHERE id=:id")
    db.session.execute(sql, {"id":id})
    
    db.session.commit()
    return redirect(request.referrer)

@app.route("/editpage/<int:id>", methods=["GET"])
def editpage(id):
    sql = """SELECT id, writer, message, date, thread_id
    FROM messages WHERE id=:id"""
    result = db.session.execute(text(sql), {"id": id})
    message = result.fetchall()
    return render_template("editpage.html", message=message)

@app.route("/edit/<int:id>", methods=["POST"])
def edit(id):
    message = request.form["message"]

    sql = text("UPDATE messages SET message=:message WHERE id=:id  ")
    db.session.execute(sql, {"id": id, "message": message})
    db.session.commit()

    return redirect(request.form.get('redir'))
