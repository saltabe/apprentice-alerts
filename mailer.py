# Sends alert emails to subscribers, and builds the manage/unsubscribe links.
# Called by daily_alert.py.

from email.message import EmailMessage
from html import escape
import os
import smtplib

from dotenv import load_dotenv
from itsdangerous import URLSafeSerializer

load_dotenv()
secret_key = os.environ.get("SECRET_KEY")
serializer = URLSafeSerializer(secret_key)

URL = "https://apprentice.saltable.fyi"


def encode_token(email):
    return serializer.dumps(email)


def get_user_url(email):
    token = encode_token(email)

    return URL + "/update?token=" + token


def get_listing_url(ad):
    return (
        "https://www.salonapprentice.com/free-salon-services/"
        f"SalonApprentice_view.php?editid1={ad['edit_id']}"
    )


def build_plain_body(email, ads):
    lines = ["New listings that match your preferences", ""]

    for ad in ads:
        url = get_listing_url(ad)

        lines.append(ad["title"])
        lines.append(f"- {ad['service_type']}")
        lines.append(f"- {ad['fee']}")
        lines.append(f"- {ad['salon']}")
        lines.append(f"- {ad['neighborhood']}")
        lines.append(f"- {ad['next_service_date']}")
        lines.append("")
        lines.append(url)
        lines.append("")

    lines.append(f"Manage your alerts or unsubscribe here: {get_user_url(email)}")

    return "\n".join(lines)


def build_html_body(email, ads):
    intro = "<p>New listings that match your preferences</p>"

    header = (
        "<tr><th>Title</th><th>Service Type</th><th>Fee</th>"
        "<th>Salon</th><th>Neighborhood</th><th>Date</th></tr>"
    )
    rows = [header]

    for ad in ads:
        url = escape(get_listing_url(ad))

        values = [
            ad["title"],
            ad["service_type"],
            ad["fee"],
            ad["salon"],
            ad["neighborhood"],
            ad["next_service_date"],
        ]
        cells = "".join(f'<td><a href="{url}">{escape(value)}</a></td>' for value in values)

        rows.append("<tr>" + cells + "</tr>")

    manage_url = escape(get_user_url(email))
    footer = f'<p>Manage your alerts or unsubscribe <a href="{manage_url}">here</a></p>'

    return intro + "<table>" + "".join(rows) + "</table>" + footer


def send_email(email, subject, plain_body, html_body):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = os.environ.get("ALERTS_FROM_EMAIL")
    msg["To"] = email
    msg.set_content(plain_body)
    msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(os.environ.get("SMTP_HOST"), int(os.environ.get("SMTP_PORT"))) as server:
        server.starttls()
        server.login(os.environ.get("SMTP_USERNAME"), os.environ.get("SMTP_PASSWORD"))
        server.send_message(msg)


def write_email(email, ads):
    subject = "New listings from Salon Apprentice"
    plain_body = build_plain_body(email, ads)
    html_body = build_html_body(email, ads)

    send_email(email, subject, plain_body, html_body)