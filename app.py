from flask import Flask, render_template, request, redirect, url_for, session, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random
from flask_mail import Mail, Message
from dotenv import load_dotenv
from datetime import datetime

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

pending_registrations = {}

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
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    owner = db.relationship("User", backref="items")
    is_giveaway = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    available_from = db.Column(db.Date)
    available_until = db.Column(db.Date)

class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    status = db.Column(db.String(20), default="pending")
    item = db.relationship("Item", backref="requests")
    requester = db.relationship("User")

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def send_reset_email(to_email, code):
    msg = Message("Campus Exchange password reset code",
            sender=app.config["MAIL_USERNAME"],
            recipients=[to_email])
    msg.body = f"Your password reset code is: {code}"
    mail.send(msg)

def send_verification_email(to_email, code):
    msg = Message("Campus Exchange verification code",
            sender=app.config["MAIL_USERNAME"],
            recipients=[to_email])
    msg.body = f"Your verification code is: {code}"
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
        code = str(random.randint(100000, 999999))
        pending_registrations[email] = {
            "name": name,
            "password_hash": generate_password_hash(password, method="pbkdf2:sha256"),
            "code": code,
        }
        session["pending_email"] = email
        send_verification_email(email, code)
        return render_template("verify.html", email=email)
    return render_template("register.html")

@app.route("/verify", methods=["POST"])
def verify():
    email = session.get("pending_email")
    code = request.form["code"]
    pending = pending_registrations.get(email)
    if not pending or pending["code"] != code:
        return render_template("verify.html", email=email, error="Wrong or expired code.")
    user = User(name=pending["name"], email=email, password_hash=pending["password_hash"])
    db.session.add(user)
    db.session.commit()
    pending_registrations.pop(email, None)
    session.pop("pending_email", None)
    login_user(user)
    return redirect(url_for("home"))


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
@login_required
def new_item():
    if request.method == "POST":
        from_str = request.form.get("available_from")
        until_str = request.form.get("available_until")
        available_from = datetime.strptime(from_str, "%Y-%m-%d").date() if from_str else None
        available_until = datetime.strptime(until_str, "%Y-%m-%d").date() if until_str else None
        today = datetime.utcnow().date()
        if available_from and available_from < today:
            return render_template("new_item.html", error="'Available from' can't be in the past.")
        if available_until and available_until < today:
            return render_template("new_item.html", error="'Available until' can't be in the past.")
        if available_from and available_until and available_until < available_from:
            return render_template("new_item.html", error="'Available until' can't be before 'Available from'.")
        item = Item(
            title=request.form["title"],
            description=request.form["description"],
            category=request.form["category"],
            owner_id=current_user.id,
            is_giveaway=bool(request.form.get("is_giveaway")),
            available_from=available_from,
            available_until=available_until,
        )
        db.session.add(item)
        db.session.commit()
        note = Notification(message="New item added: " + item.title)
        db.session.add(note)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("new_item.html")

@app.route("/my-items")
@login_required
def my_items():
    items = Item.query.filter_by(owner_id=current_user.id).all()
    return render_template("my_items.html", items=items)

@app.route("/my-loans")
@login_required
def my_loans():
    borrowing = Request.query.filter_by(
        requester_id=current_user.id, status="accepted"
    ).all()
    lending = Request.query.join(Item).filter(
        Item.owner_id == current_user.id, Request.status == "accepted"
    ).all()
    today = datetime.utcnow().date()
    return render_template("my_loans.html", borrowing=borrowing, lending=lending, today=today)

@app.route("/notifications")
@login_required
def notifications():
    notes = Notification.query.order_by(Notification.created_at.desc()).all()
    return render_template("notifications.html", notes=notes)

@app.route("/items/<int:item_id>")
def item_detail(item_id):
    item = Item.query.get_or_404(item_id)
    return render_template("item_detail.html", item=item)

@app.route("/items/<int:item_id>/request", methods=["POST"])
@login_required
def request_item(item_id):
    item = Item.query.get_or_404(item_id)
    borrow = Request(item_id=item.id, requester_id=current_user.id)
    db.session.add(borrow)
    db.session.commit()
    return redirect(url_for("item_detail", item_id=item.id))


@app.route("/requests/<int:request_id>/accept", methods=["POST"])
@login_required
def accept_request(request_id):
    borrow = Request.query.get_or_404(request_id)
    if borrow.item.owner_id != current_user.id:
        abort(403)
    borrow.status = "accepted"
    others = Request.query.filter(
        Request.item_id == borrow.item_id,
        Request.id != borrow.id,
    ).all()
    for other in others:
        other.status = "rejected"
    db.session.commit()
    return redirect(url_for("item_detail", item_id=borrow.item_id))


@app.route("/requests/<int:request_id>/reject", methods=["POST"])
@login_required
def reject_request(request_id):
    borrow = Request.query.get_or_404(request_id)
    if borrow.item.owner_id != current_user.id:
        abort(403)
    borrow.status = "rejected"
    db.session.commit()
    return redirect(url_for("item_detail", item_id=borrow.item_id))

@app.route("/requests/<int:request_id>/return", methods=["POST"])
@login_required
def return_request(request_id):
    borrow = Request.query.get_or_404(request_id)
    if current_user.id != borrow.requester_id and current_user.id != borrow.item.owner_id:
        abort(403)
    borrow.status = "returned"
    db.session.commit()
    return redirect(url_for("item_detail", item_id=borrow.item_id))


@app.route("/requests/<int:request_id>/recall", methods=["POST"])
@login_required
def recall_request(request_id):
    borrow = Request.query.get_or_404(request_id)
    if current_user.id != borrow.item.owner_id:
        abort(403)
    borrow.status = "returned"
    db.session.commit()
    return redirect(url_for("item_detail", item_id=borrow.item_id))

@app.route("/items/<int:item_id>/delete", methods=["POST"])
@login_required
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.owner_id != current_user.id:
        abort(403)
    Request.query.filter_by(item_id=item.id).delete()
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/items/<int:item_id>/extend", methods=["POST"])
@login_required
def extend_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.owner_id != current_user.id:
        abort(403)
    new_str = request.form.get("available_until")
    if new_str:
        new_until = datetime.strptime(new_str, "%Y-%m-%d").date()
        today = datetime.utcnow().date()
        if new_until >= today:
            item.available_until = new_until
            db.session.commit()
    return redirect(url_for("item_detail", item_id=item.id))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)