from os import getenv

from app import app

from flask_sqlalchemy import SQLAlchemy

app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
app.secret_key = getenv("SECRET_KEY")

db = SQLAlchemy(app)
