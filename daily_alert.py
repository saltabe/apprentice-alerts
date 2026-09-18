# Entry point for the daily job: scrape -> match against subscriptions -> email.
# Meant to be run on a schedule (cron, or your host's scheduled-job feature),
# not inside the Flask app itself.

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
        for row in users:
            if row["keyword"].lower() in ad["title"].lower():
                email = row["email"]

                if email not in matches:
                    matches[email] = []

                if ad not in matches[email]:
                    matches[email].append(ad)

    return matches


def send_alerts(matches):
    for email, ads in matches.items():
        mailer.write_email(email, ads)


def mark_ads_sent(conn, ads):
    for ad in ads:
        models.update_ad(conn, ad["edit_id"])

    conn.commit()


def main():
    conn = models.get_connection()
    build_tables(conn)

    ads = filter_ads(conn)
    save_ads(conn, ads)

    matches = get_relevant_users(conn, ads)
    send_alerts(matches)

    mark_ads_sent(conn, ads)


if __name__ == "__main__":
    main()
