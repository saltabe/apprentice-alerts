# Sends alert emails to subscribers, and builds the manage/unsubscribe links.
# Called by daily_alert.py.

from email.message import EmailMessage
import os
import smtplib

from dotenv import load_dotenv
from itsdangerous import URLSafeSerializer

load_dotenv()
secret_key = os.environ.get("SECRET_KEY")
serializer = URLSafeSerializer(secret_key)

URL = "https://yoursite.com"  # TODO: real site URL once hosted


def encode_token(email):
    return serializer.dumps(email)


def get_url(email):
    token = encode_token(email)

    return URL + "/update?token=" + token


def send_email(email, subject, body):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = os.environ.get("ALERTS_FROM_EMAIL")
    msg["To"] = email
    msg.set_content(body)

    with smtplib.SMTP(os.environ.get("SMTP_HOST"), int(os.environ.get("SMTP_PORT"))) as server:
        server.starttls()
        server.login(os.environ.get("SMTP_USERNAME"), os.environ.get("SMTP_PASSWORD"))
        server.send_message(msg)

# 4. What the email actually says — the body text, listing which ads matched — is the last piece, and depends on what shape daily_alert.py ends up passing in (probably a subscriber's email plus a list of matching ad dicts).