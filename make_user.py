from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
        u = User(name="Ali ",
                email="test.user@student.bth.se",
                password_hash=generate_password_hash("password123", method="pbkdf2:sha256"))
        db.session.add(u)
        db.session.commit()
        print("Skapade konto:", u.email)