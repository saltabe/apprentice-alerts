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


def _format_fee(fee):
    if fee == "No":
        return "Free"

    if fee == "Yes":
        return "Fee required"

    return fee


def _ad_details(ad):
    # blank fields (e.g. no salon listed) are dropped rather than shown as empty
    values = [ad["service_type"], _format_fee(ad["fee"]), ad["salon"], ad["neighborhood"], ad["next_service_date"]]

    return [value for value in values if value]


def build_plain_body(email, ads):
    lines = ["New listings that match your preferences:", ""]

    for ad in ads:
        url = get_listing_url(ad)

        lines.append(ad["title"])

        for detail in _ad_details(ad):
            lines.append(f"- {detail}")

        lines.append("")
        lines.append(url)
        lines.append("")

    lines.append(f"Update your subscription or unsubscribe from our emails: {get_user_url(email)}")

    return "\n".join(lines)


# email clients mostly ignore <style> blocks and external CSS, so every
# rule here has to be inline; these mirror static/styles.css's palette
_FONT = "font-family: -apple-system, 'Helvetica Neue', Helvetica, Arial, sans-serif;"
_TEXT = "#2b2b2b"
_MUTED = "#6b6b6b"
_BORDER = "#e5e2de"
_BG = "#faf9f7"
_CARD_BG = "#ffffff"
_ACCENT = "#b5654d"


def _build_ad_card(ad):
    url = escape(get_listing_url(ad))
    title = escape(ad["title"])
    details = " &middot; ".join(escape(value) for value in _ad_details(ad))

    return f"""
    <tr>
      <td style="padding: 0 0 16px;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
               style="background: {_CARD_BG}; border: 1px solid {_BORDER}; border-radius: 12px;">
          <tr>
            <td style="padding: 16px 20px;">
              <p style="margin: 0 0 6px; font-size: 16px; font-weight: 600; color: {_TEXT}; {_FONT}">{title}</p>
              <p style="margin: 0 0 12px; font-size: 13px; color: {_MUTED}; {_FONT}">{details}</p>
              <a href="{url}" style="font-size: 14px; font-weight: 600; color: {_ACCENT}; text-decoration: none; {_FONT}">View listing &rarr;</a>
            </td>
          </tr>
        </table>
      </td>
    </tr>
    """


def build_html_body(email, ads):
    intro = f'<p style="margin: 0 0 20px; font-size: 15px; color: {_TEXT}; {_FONT}">New listings that match your preferences:</p>'

    cards = "".join(_build_ad_card(ad) for ad in ads)

    manage_url = escape(get_user_url(email))
    footer = f"""
    <tr>
      <td style="padding: 16px 0 0; border-top: 1px solid {_BORDER};">
        <p style="margin: 16px 0 0; font-size: 13px; color: {_MUTED}; {_FONT}">
          <a href="{manage_url}" style="color: {_MUTED};">Update your subscription or unsubscribe</a> from our emails.
        </p>
      </td>
    </tr>
    """

    return f"""
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background: {_BG}; padding: 32px 16px;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width: 480px;">
            <tr><td style="padding: 0 0 4px;">{intro}</td></tr>
            {cards}
            {footer}
          </table>
        </td>
      </tr>
    </table>
    """


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