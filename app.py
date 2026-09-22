from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "campus_exchange.db")

db = SQLAlchemy(app)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(60))


@app.route("/")
def home():
    items = Item.query.all()
    return render_template("index.html", items=items)


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


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)