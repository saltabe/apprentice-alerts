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
serializer = URLSafeSerializer(app.secret_key)

conn = models.get_connection()
models.init_db(conn)


def get_forms():
    email = request.form.get("email")
    city = request.form.get("city")
    keywords_str = request.form.get("keywords")

    return email, city, keywords_str


def format_keywords(keywords_str):
    return [item.strip() for item in keywords_str.split(',')]


def decode_token(token):
    try:
        return serializer.loads(token)
    except BadSignature:
        return None


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        conn = models.get_connection()

        email, city, keywords_str = get_forms()

        if not email:
            return redirect("/")

        if not city or city not in CITIES:
            return redirect("/")

        if not keywords_str:
            return redirect("/")

        keywords = format_keywords(keywords_str)

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
        old_email = decode_token(token)

        if not old_email:
            return redirect("/")

        action = request.form.get("action")

        if action == "cancel":
            models.delete_user(conn, old_email)
            conn.commit()
            flash("You've been unsubscribed.")
            return redirect("/")

        # below code is for if user modifies subscription

        email, city, keywords_str = get_forms()

        if not email:
            return redirect("/")

        if not city or city not in CITIES:
            return redirect("/")

        if not keywords_str:
            return redirect("/")

        # delete all existing entries for user
        # to keep it simple
        models.delete_user(conn, old_email)

        keywords = format_keywords(keywords_str)

        for keyword in keywords:
            models.insert_user(conn, email, city, keyword)

        conn.commit()

        flash("Your subscription has been updated.")

        return redirect("/")

    else:
        conn = models.get_connection()

        token = request.args.get("token")
        old_email = decode_token(token)

        if not old_email:
            return redirect("/")

        rows = models.select_user(conn, old_email)
        email = rows[0]["email"]
        city = rows[0]["city"]
        keywords = [row["keyword"] for row in rows]

        return render_template(
            "change.html",
            email=email,
            city=city,
            keywords=keywords,
            token=token,
            city_labels=CITY_LABELS,
        )


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
        requests.get(healthcheck_url, timeout=10)

    return "ok", 200