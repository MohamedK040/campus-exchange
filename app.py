from flask import Flask, render_template, request, redirect, url_for, session, abort
from extensions import db, mail
from models import User, Item, Request, Notification, Review
from config import Config
from emails import send_reset_email, send_verification_email
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random
from datetime import datetime
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.config.from_object(Config)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


mail.init_app(app)

reset_codes = {} 

pending_registrations = {}

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


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

        image_filename = None
        file = request.files.get("image")
        if file and file.filename:
            filename = secure_filename(file.filename)
            image_filename = str(random.randint(10000, 99999)) + "_" + filename
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], image_filename))

        item = Item(
            title=request.form["title"],
            description=request.form["description"],
            category=request.form["category"],
            owner_id=current_user.id,
            is_giveaway=bool(request.form.get("is_giveaway")),
            available_from=available_from,
            available_until=available_until,
            image_filename=image_filename,
        )
        db.session.add(item)
        db.session.commit()
        note = Notification(message="New item added: " + item.title)
        db.session.add(note)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("new_item.html")

@app.route("/items/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.owner_id != current_user.id:
        abort(403)
    if request.method == "POST":
        from_str = request.form.get("available_from")
        until_str = request.form.get("available_until")
        available_from = datetime.strptime(from_str, "%Y-%m-%d").date() if from_str else None
        available_until = datetime.strptime(until_str, "%Y-%m-%d").date() if until_str else None
        if available_from and available_until and available_until < available_from:
            return render_template("edit_item.html", item=item, error="'Available until' can't be before 'Available from'.")
        item.title = request.form["title"]
        item.description = request.form["description"]
        item.category = request.form["category"]
        item.is_giveaway = bool(request.form.get("is_giveaway"))
        item.available_from = available_from
        item.available_until = available_until
        db.session.commit()
        return redirect(url_for("item_detail", item_id=item.id))
    return render_template("edit_item.html", item=item)

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
    notes = Notification.query.filter(
        (Notification.user_id == current_user.id) | (Notification.user_id == None)
    ).order_by(Notification.created_at.desc()).all()
    return render_template("notifications.html", notes=notes)

@app.route("/items/<int:item_id>")
def item_detail(item_id):
    item = Item.query.get_or_404(item_id)
    reviews = Review.query.filter_by(target_id=item.owner_id).order_by(Review.created_at.desc()).all()
    if reviews:
        avg_rating = round(sum(r.rating for r in reviews) / len(reviews), 1)
    else:
        avg_rating = None
    return render_template("item_detail.html", item=item, reviews=reviews, avg_rating=avg_rating)

@app.route("/items/<int:item_id>/request", methods=["POST"])
@login_required
def request_item(item_id):
    item = Item.query.get_or_404(item_id)
    borrow = Request(item_id=item.id, requester_id=current_user.id)
    db.session.add(borrow)
    db.session.commit()
    note = Notification(message=current_user.name + " requested to borrow " + item.title, user_id=item.owner_id)
    db.session.add(note)
    db.session.commit()
    return redirect(url_for("item_detail", item_id=item.id))


@app.route("/requests/<int:request_id>/accept", methods=["POST"])
@login_required
def accept_request(request_id):
    borrow = Request.query.get_or_404(request_id)
    if borrow.item.owner_id != current_user.id:
        abort(403)

    active_loan = Request.query.filter(
        Request.item_id == borrow.item_id,
        Request.status == "accepted",
        Request.id != borrow.id,
    ).first()
    if active_loan:
        return redirect(url_for("item_detail", item_id=borrow.item_id))

    borrow.status = "accepted"

    others = Request.query.filter(
        Request.item_id == borrow.item_id,
        Request.id != borrow.id,
        Request.status == "pending",
    ).all()
    for other in others:
        other.status = "rejected"

    note = Notification(message="Your request for " + borrow.item.title + " was accepted.", user_id=borrow.requester_id)
    db.session.add(note)

    db.session.commit()
    return redirect(url_for("item_detail", item_id=borrow.item_id))

@app.route("/requests/<int:request_id>/reject", methods=["POST"])
@login_required
def reject_request(request_id):
    borrow = Request.query.get_or_404(request_id)
    if borrow.item.owner_id != current_user.id:
        abort(403)
    borrow.status = "rejected"
    note = Notification(message="Your request for " + borrow.item.title + " was rejected.", user_id=borrow.requester_id)
    db.session.add(note)
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

@app.route("/requests/<int:request_id>/review", methods=["POST"])
@login_required
def leave_review(request_id):
    borrow = Request.query.get_or_404(request_id)
    if borrow.status != "returned":
        abort(403)
    if current_user.id == borrow.requester_id:
        target_id = borrow.item.owner_id
    elif current_user.id == borrow.item.owner_id:
        target_id = borrow.requester_id
    else:
        abort(403)
    existing = Review.query.filter_by(request_id=borrow.id, author_id=current_user.id).first()
    if existing:
        return redirect(url_for("item_detail", item_id=borrow.item_id))
    review = Review(
        rating=int(request.form["rating"]),
        comment=request.form.get("comment", ""),
        author_id=current_user.id,
        target_id=target_id,
        request_id=borrow.id,
    )
    db.session.add(review)
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
    app.run(debug=True, port=5001)