# Flask web app: signup form, and the token-based manage/unsubscribe page.
# daily_alert.py (the actual scrape-and-email job) runs inside this same
# process, triggered by the /run-daily-alert route.

import os

import requests
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request
from itsdangerous import BadSignature, URLSafeSerializer

import daily_alert
import models
from scraper import CITIES, CITY_LABELS

load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
_serializer = URLSafeSerializer(app.secret_key)

models.init_db(models.get_connection())


def _get_forms():
    email = request.form.get("email")
    city = request.form.get("city")
    keywords_str = request.form.get("keywords")

    return email, city, keywords_str


def _format_keywords(keywords_str):
    return [item.strip() for item in keywords_str.split(',')]


def _decode_token(token):
    try:
        return _serializer.loads(token)
    except BadSignature:
        return None


def _signup_form_valid(email, city, keywords_str):
    return bool(email) and city in CITIES and bool(keywords_str)


def _render_manage_page(email, city, keywords, token):
    return render_template(
        "change.html",
        email=email,
        city=city,
        keywords=keywords,
        token=token,
        city_labels=CITY_LABELS,
    )


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        conn = models.get_connection()

        email, city, keywords_str = _get_forms()

        if not _signup_form_valid(email, city, keywords_str):
            return redirect("/")

        keywords = _format_keywords(keywords_str)

        for keyword in keywords:
            models.insert_user(conn, email, city, keyword)

        conn.commit()

        flash("You're in! We'll email you when an ad matches your preferences.")

        return redirect("/")

    else:
        return render_template("index.html", city_labels=CITY_LABELS)


@app.route("/update", methods=["GET", "POST"])
def update():
    if request.method == "POST":
        conn = models.get_connection()

        token = request.args.get("token")
        old_email = _decode_token(token)

        if not old_email:
            return redirect("/")

        action = request.form.get("action")

        if action == "cancel":
            models.delete_user(conn, old_email)
            conn.commit()
            flash("You've been unsubscribed.")
            return render_template("change.html", unsubscribed=True)

        # below code is for if user modifies subscription

        email, city, keywords_str = _get_forms()

        if not _signup_form_valid(email, city, keywords_str):
            return redirect("/")

        # delete all existing entries for user
        # to keep it simple
        models.delete_user(conn, old_email)

        keywords = _format_keywords(keywords_str)

        for keyword in keywords:
            models.insert_user(conn, email, city, keyword)

        conn.commit()

        flash("Your subscription has been updated.")

        return _render_manage_page(email, city, keywords, token)

    else:
        conn = models.get_connection()

        token = request.args.get("token")
        old_email = _decode_token(token)

        if not old_email:
            return redirect("/")

        rows = models.select_user(conn, old_email)
        email = rows[0]["email"]
        city = rows[0]["city"]
        keywords = [row["keyword"] for row in rows]

        return _render_manage_page(email, city, keywords, token)


@app.route("/run-daily-alert", methods=["POST"])
def run_daily_alert():
    secret = request.headers.get("X-Cron-Secret")

    if not secret or secret != os.environ.get("CRON_SECRET"):
        return "forbidden", 403

    healthcheck_url = os.environ.get("HEALTHCHECK_URL")

    try:
        daily_alert.main()
    except Exception:
        if healthcheck_url:
            requests.get(healthcheck_url + "/fail", timeout=10)
        raise

    if healthcheck_url:
        try:
            requests.get(healthcheck_url, timeout=10)
        except requests.RequestException:
            # the alert already succeeded; don't fail the whole request
            # just because the healthcheck ping itself had a blip
            pass

    return "ok", 200
