# Sends alert emails to subscribers, and builds the manage/unsubscribe links.
# Called by daily_alert.py.

import os

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


# Where does email come from?

# 3. Sending an email. Python's standard library already has everything you need — no new dependency. smtplib handles the actual SMTP connection/sending; email.message.EmailMessage builds the message itself (subject, from, to, body). You'll read SMTP_HOST/SMTP_PORT/SMTP_USERNAME/SMTP_PASSWORD/ALERTS_FROM_EMAIL from .env — those variable names are already sitting in .env.example from when this project was first scaffolded.

# 4. What the email actually says — the body text, listing which ads matched — is the last piece, and depends on what shape daily_alert.py ends up passing in (probably a subscriber's email plus a list of matching ad dicts).