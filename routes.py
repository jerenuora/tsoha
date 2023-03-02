import secrets
from flask import redirect, render_template, request, session, flash, abort, make_response
from sqlalchemy.sql import text
from werkzeug.security import check_password_hash, generate_password_hash

from app import app
from db import db


@app.route("/")
def index():
    sql = "SELECT id, name FROM forums"
    result = db.session.execute(text(sql))
    forums = result.fetchall()

    sql = """SELECT f.name, count(t. title) FROM threads T
                LEFT JOIN  forums F ON t.forum_id = f.id GROUP BY f.name"""
    result = db.session.execute(text(sql))
    threadcount = result.fetchall()

    threaddata = {}
    for item in threadcount:
        threaddata[item[0]] = item[1:]

    sql = """SELECT F.name, count(M.message), max(M.date) FROM  threads T
                LEFT JOIN messages M  ON M.thread_id = T.id 
                LEFT JOIN forums f ON t.forum_id = F.id GROUP BY F.id """
    result = db.session.execute(text(sql))
    messagecount = result.fetchall()

    messagedata = {}
    for item in messagecount:
        messagedata[item[0]] = item[1:]

    return render_template("index.html", forums=forums,
                           threadcount=threaddata, messagecount=messagedata)


@app.route("/forum/<int:id>")
def thread_view(id):
    sql = "SELECT id, title, owner,  forum_id FROM threads WHERE forum_id=:id"
    result = db.session.execute(text(sql), {"id": id})
    threads = result.fetchall()
    sql = """SELECT T.title, count(M.message), max(date)  
            FROM messages M, threads T
            WHERE M.thread_id = T.id GROUP BY T.id ORDER BY T.id """
    result = db.session.execute(text(sql))
    messagecount = result.fetchall()

    messagedata = {}
    for item in messagecount:
        messagedata[item[0]] = item[1:]

    return render_template("threads.html", threads=threads, 
                           forum_id=id, messagecount=messagedata)


@app.route("/forum/thread/<int:id>")
def messages_view(id):
    sql = """SELECT id, writer, message, date, thread_id
                FROM messages WHERE thread_id=:id"""
    result = db.session.execute(text(sql), {"id": id})
    messages = result.fetchall()
    return render_template("messages.html", messages=messages, thread_id=id)

@app.route("/image/<string:username>")
def image(username):
    sql = """SELECT data FROM avatar A, users U 
                WHERE A.user_id=U.id AND U.username=:username"""
    result = db.session.execute(text(sql), {"username":username})
    data = result.fetchone()[0]
    response = make_response(bytes(data))
    response.headers.set("Content-Type", "image/jpeg")
    return response

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
    file = request.files["file"]
    name = file.filename
    if not name:
        with open("static/defaultavatar.jpg", "rb") as img:
            file = img.read()
            data = bytearray(file)
    else:
        if not name.endswith((".jpg", ".JPG", ".jpeg", ".JPEG")):
            return "Vain .jpg sallittu"
        data = file.read()
    if len(data) > 100*1024:
        flash("Liian iso tiedosto")
        return redirect("/signuppage")

    if not username or not password:
        flash("Täytä kaikki kentät")
        return redirect("/signuppage")
    if password != password_confirmation:
        flash("Salasanat eivät ole samat")
        return redirect("/signuppage")

    hash_value = generate_password_hash(password)
    try:
        sql = """INSERT INTO users (username, password) 
                    VALUES (:username, :password)"""
        db.session.execute(
            text(sql), {
                "username": username,
                "password": hash_value})
    except :
        flash("Jokin meni vikaan, kenties käyttäjänimi on jo varattu")
        return redirect("/signuppage")

    sql = "SELECT id FROM users WHERE username=:username"
    result = db.session.execute(text(sql), {"username": username})
    id = result.fetchone()

    sql = """INSERT INTO avatar (name,data,user_id) 
                VALUES (:name,:data,:user_id)"""
    db.session.execute(text(sql), {
        "name":name,
        "data":data,
        "user_id":id[0]})

    db.session.commit()

    session["username"] = username
    session["csrf_token"] = secrets.token_hex(16)
    return redirect("/")


@app.route("/postmessage/<int:id>", methods=["POST"])
def postmessage(id):
    message = request.form["message"]
    writer = session["username"]
    if len(message) < 1:
        flash("Viestissä on oltava sisältöä")
        return redirect(request.referrer)

    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)

    thread_id = id
    sql = """INSERT INTO messages (writer, message, thread_id)
                VALUES (:writer, :message, :thread_id)"""

    db.session.execute(
        text(sql), {
            "writer": writer,
            "message": message,
            "thread_id": thread_id})
    db.session.commit()
    return redirect(request.referrer)


@app.route("/postthread/<int:id>", methods=["POST"])
def postthread(id):
    title = request.form["title"]
    message = request.form["message"]
    writer = session["username"]
    if len(title) < 1:
        flash("Tyhjä otsikko ei kelpaa")
        return redirect(request.referrer)
    if len(message) < 1:
        flash("Viestissä on oltava sisältöä")
        return redirect(request.referrer)

    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)

    sql = """INSERT INTO threads (title, owner, forum_id) 
                VALUES (:title, :owner, :forum_id)"""
    db.session.execute(
        text(sql), {"title": title, "owner": writer, "forum_id": id})
    db.session.commit()

    sql = "SELECT MAX(id) FROM threads WHERE forum_id=:id"
    result = db.session.execute(text(sql), {"id": id})
    thread_id = result.fetchall()

    sql = """INSERT INTO messages (writer, message, thread_id)
                VALUES (:writer, :message, :thread_id)"""

    db.session.execute(
        text(sql), {
            "writer": writer,
            "message": message,
            "thread_id": thread_id[0][0]})
    db.session.commit()
    return redirect(request.referrer)


@app.route("/searchpage")
def searchpage():
    return render_template("search.html")

@app.route("/search", methods=["GET"])
def search():
    searchword = request.args.get("searchword")
    sql = """SELECT id, writer, message, date, thread_id
    FROM messages WHERE LOWER(message) LIKE LOWER(:searchword)"""
    result = db.session.execute(text(sql), {"searchword":"%"+searchword+"%"})
    messages = result.fetchall()
    sql = """SELECT id, title, owner, forum_id
    FROM threads WHERE LOWER(title) LIKE LOWER(:searchword)"""
    result = db.session.execute(text(sql), {"searchword":"%"+searchword+"%"})
    threads = result.fetchall()

    return render_template("search.html", messages=messages, threads=threads)

@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    destination = request.form.get("dest")

    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    if destination == "message":
        sql = "DELETE FROM messages WHERE id=:id"
        db.session.execute(text(sql), {"id":id})
    elif destination == "thread":
        sql = "DELETE FROM threads WHERE id=:id"
        db.session.execute(text(sql), {"id":id})
        sql = "DELETE FROM messages WHERE thread_id=:id"
        db.session.execute(text(sql), {"id":id})

    db.session.commit()
    return redirect(request.referrer)

@app.route("/editpage/<int:id>", methods=["GET"])
def editpage(id):
    destination = request.args.get("dest")

    if destination == "message":

        sql = """SELECT id, writer, message, date, thread_id
                    FROM messages WHERE id=:id"""
        result = db.session.execute(text(sql), {"id": id})
        message = result.fetchall()
        return render_template("editpage.html", message=message)

    elif destination == "thread":
        sql = """SELECT id, title, owner, forum_id
                    FROM threads WHERE id=:id"""
        result = db.session.execute(text(sql), {"id": id})
        thread = result.fetchall()

        return render_template("editpage.html", thread=thread)

@app.route("/edit/<int:id>", methods=["POST"])
def edit(id):
    destination = request.form.get("dest")
    if destination == "message":
        message = request.form["message"]
        if session["csrf_token"] != request.form["csrf_token"]:
            abort(403)

        sql = "UPDATE messages SET message=:message WHERE id=:id"
        db.session.execute(text(sql), {"id": id, "message": message})
    elif destination == "thread":
        title = request.form["thread"]
        if session["csrf_token"] != request.form["csrf_token"]:
            abort(403)

        sql = "UPDATE threads SET title=:title WHERE id=:id"
        db.session.execute(text(sql), {"id": id, "title": title})

    db.session.commit()

    return redirect(request.form.get("redir"))
