from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    users = User.query.all()
    for u in users:
        u.password_hash = generate_password_hash("password123", method="pbkdf2:sha256")
    db.session.commit()
    print("Alla losenord ar nu: password123")
    for u in users:
        print(" -", u.email)
