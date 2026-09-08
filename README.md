# Apprentice Alerts

Scrapes Salon Apprentice daily and emails subscribers when new offerings match their chosen keywords. Includes a small site for signing up and managing/removing a subscription.

## Layout

- `app.py` — Flask site: signup form, change/unsubscribe.
- `scraper.py` — fetches and parses Salon Apprentice listings.
- `mailer.py` — sends alert emails.
- `models.py` — database schema/access, shared by the app and the daily job.
- `daily_alert.py` — entry point for the scheduled job (scrape → match → email).
- `templates/` — HTML templates.
- `static/` — CSS/JS/assets.

## Setup

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in values
```

## Running the daily job

`daily_alert.py` is meant to run on a schedule (cron, or your host's scheduled-job feature) — not inside the Flask app process.
