from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "campus_exchange.db")
app.config["SECRET_KEY"] = "change-this-to-something-secret"

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


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        if not email.endswith("student.bth.se"):
            return render_template("register.html", error="Please use your BTH email address.")
        if User.query.filter_by(email=email).first():
            return render_template("register.html", error="That email is already registered.")
        user = User(name=name, email=email, password_hash=generate_password_hash(password))
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
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("home"))
        return render_template("login.html", error="Wrong email or password.")
    return render_template("login.html")


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


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)