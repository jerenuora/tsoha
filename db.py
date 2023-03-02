from os import getenv

from app import app

from flask_sqlalchemy import SQLAlchemy

if getenv("DEV") == "True":
    app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
else:
app.config["SQLALCHEMY_DATABASE_URI"] = getenv(
        "DATABASE_URL").replace("://", "ql://", 1)

app.secret_key = getenv("SECRET_KEY")

db = SQLAlchemy(app)
