from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random
from flask_mail import Mail, Message
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "campus_exchange.db")
app.config["SECRET_KEY"] = "change-this-to-something-secret"

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")

mail = Mail(app)

reset_codes = {} 

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(60))


class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=False)
    requester_name = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(20), default="pending")
    item = db.relationship("Item", backref="requests")

def send_reset_email(to_email, code):
    msg = Message("Campus Exchange password reset code",
            sender=app.config["MAIL_USERNAME"],
            recipients=[to_email])
    msg.body = f"Your password reset code is: {code}"
    mail.send(msg)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        name = first_name + " " + last_name
        email = request.form["email"]
        password = request.form["password"]
        confirm = request.form["confirm_password"]
        if password != confirm:
            return render_template("register.html", error="Passwords do not match.")
        if not email.endswith("student.bth.se"):
            return render_template("register.html", error="Please use your BTH email address.")
        if User.query.filter_by(email=email).first():
            return render_template("register.html", error="That email is already registered.")
        user = User(name=name, email=email, password_hash=generate_password_hash(password, method="pbkdf2:sha256"))
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("home"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        remember = request.form.get("remember")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=bool(remember))
            return redirect(url_for("home"))
        return render_template("login.html", error="Wrong email or password.")
    return render_template("login.html")

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        if not email.endswith("student.bth.se"):
            return render_template("forgot_password.html", error="Please use your BTH email address.")
        session["reset_email"] = email
        user = User.query.filter_by(email=email).first()
        if user:
            code = str(random.randint(100000, 999999))
            reset_codes[email] = code
            send_reset_email(email, code)
        return render_template("reset_password.html", email=email)
    return render_template("forgot_password.html")

@app.route("/reset-password", methods=["POST"])
def reset_password():
    email = session.get("reset_email")
    code = request.form["code"]
    password = request.form["password"]
    confirm = request.form["confirm_password"]
    if password != confirm:
        return render_template("reset_password.html", email=email, error="Passwords do not match.")
    if reset_codes.get(email) != code:
        return render_template("reset_password.html", email=email, error="Wrong or expired code.")
    user = User.query.filter_by(email=email).first()
    if user:
        user.password_hash = generate_password_hash(password, method="pbkdf2:sha256")
        db.session.commit()
        reset_codes.pop(email, None)
        return render_template("login.html", error="Password reset! You can now log in.")
    return render_template("reset_password.html", email=email, error="Something went wrong.")

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/")
def home():
    q = request.args.get("q", "")
    if q:
        items = Item.query.filter(Item.title.contains(q)).all()
    else:
        items = Item.query.all()
    return render_template("index.html", items=items, q=q)


@app.route("/items/new", methods=["GET", "POST"])
def new_item():
    if request.method == "POST":
        item = Item(
            title=request.form["title"],
            description=request.form["description"],
            category=request.form["category"],
        )
        db.session.add(item)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("new_item.html")


@app.route("/items/<int:item_id>")
def item_detail(item_id):
    item = Item.query.get_or_404(item_id)
    return render_template("item_detail.html", item=item)

@app.route("/items/<int:item_id>/request", methods=["POST"])
def request_item(item_id):
    item = Item.query.get_or_404(item_id)
    borrow = Request(item_id=item.id, requester_name=request.form["requester_name"])
    db.session.add(borrow)
    db.session.commit()
    return redirect(url_for("item_detail", item_id=item.id))


@app.route("/requests/<int:request_id>/accept", methods=["POST"])
def accept_request(request_id):
    borrow = Request.query.get_or_404(request_id)
    borrow.status = "accepted"
    db.session.commit()
    return redirect(url_for("item_detail", item_id=borrow.item_id))


@app.route("/requests/<int:request_id>/reject", methods=["POST"])
def reject_request(request_id):
    borrow = Request.query.get_or_404(request_id)
    borrow.status = "rejected"
    db.session.commit()
    return redirect(url_for("item_detail", item_id=borrow.item_id))

@app.route("/items/<int:item_id>/delete", methods=["POST"])
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    Request.query.filter_by(item_id=item.id).delete()
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for("home"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)