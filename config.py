import os
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    UPLOAD_FOLDER = os.path.join(basedir, "static", "uploads")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "campus_exchange.db")
    SECRET_KEY = "change-this-to-something-secret"
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
