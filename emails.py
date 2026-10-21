from flask import current_app
from flask_mail import Message
from extensions import mail


def send_reset_email(to_email, code):
    msg = Message("Campus Exchange password reset code",
            sender=current_app.config["MAIL_USERNAME"],
            recipients=[to_email])
    msg.body = f"Your password reset code is: {code}"
    mail.send(msg)


def send_verification_email(to_email, code):
    msg = Message("Campus Exchange verification code",
            sender=current_app.config["MAIL_USERNAME"],
            recipients=[to_email])
    msg.body = f"Your verification code is: {code}"
    mail.send(msg)
