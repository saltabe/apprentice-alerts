# Entry point for the daily job: scrape -> match against subscriptions -> email.
# Called by app.py's /run-daily-alert route (triggered on a schedule by the
# GitHub Actions workflow), since the app process is the only one with access
# to the persistent disk the database lives on.

import sys

import mailer
import models
import scraper


def build_tables(conn):
    models.init_db(conn)


def filter_ads(conn):
    ads = scraper.loop_cities()

    return [ad for ad in ads if not models.select_ad(conn, ad["edit_id"])]


def save_ads(conn, ads):
    for ad in ads:
        models.insert_ad(conn, **ad)

    conn.commit()


def get_relevant_users(conn, ads):
    users = models.select_all_users(conn)

    matches = {}

    for ad in ads:
        searchable = f"{ad['title']} {ad['service_type']}".lower()

        for row in users:
            if row["keyword"].lower() in searchable:
                email = row["email"]

                if email not in matches:
                    matches[email] = []

                if ad not in matches[email]:
                    matches[email].append(ad)

    return matches


def send_alerts(matches):
    for email, ads in matches.items():
        try:
            mailer.write_email(email, ads)
        except Exception as e:
            # one bad address or a transient SMTP error shouldn't stop
            # everyone else in the batch from getting their alert
            print(f"Failed to send alert to {email}: {e}", file=sys.stderr)


def main():
    conn = models.get_connection()
    build_tables(conn)

    ads = filter_ads(conn)
    save_ads(conn, ads)

    matches = get_relevant_users(conn, ads)
    send_alerts(matches)


if __name__ == "__main__":
    main()
