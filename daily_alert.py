# Entry point for the daily job: scrape -> match against subscriptions -> email.
# Called by app.py's /run-daily-alert route (triggered on a schedule by the
# GitHub Actions workflow), since the app process is the only one with access
# to the persistent disk the database lives on.

import sys

import mailer
import models
import scraper


def _build_tables(conn):
    models.init_db(conn)


def _filter_ads(conn):
    ads = scraper.loop_cities()

    return [ad for ad in ads if not models.select_ad(conn, ad["edit_id"])]


def _save_ads(conn, ads):
    for ad in ads:
        models.insert_ad(conn, **ad)

    conn.commit()


def _get_relevant_users(conn, ads):
    users = models.select_all_users(conn)

    # group each subscriber's city and keywords (by type); a user with no
    # include keywords matches every ad in their city (subject to exclude),
    # per the "exclude only" signup case
    user_keywords = {}
    for row in users:
        data = user_keywords.setdefault(row["email"], {"city": row["city"], "include": [], "exclude": []})
        data[row["keyword_type"]].append(row["keyword"].lower())

    matches = {}

    for ad in ads:
        searchable = f"{ad['title']} {ad['service_type']}".lower()

        for email, data in user_keywords.items():
            if data["city"] != ad["city"]:
                continue

            includes = data["include"]
            excludes = data["exclude"]

            included = not includes or any(kw in searchable for kw in includes)
            excluded = any(kw in searchable for kw in excludes)

            if included and not excluded:
                matches.setdefault(email, [])

                if ad not in matches[email]:
                    matches[email].append(ad)

    return matches


def _send_alerts(matches):
    for email, ads in matches.items():
        try:
            mailer.write_email(email, ads)
        except Exception as e:
            # one bad address or a transient SMTP error shouldn't stop
            # everyone else in the batch from getting their alert
            print(f"Failed to send alert to {email}: {e}", file=sys.stderr)


def main():
    conn = models.get_connection()
    _build_tables(conn)

    ads = _filter_ads(conn)
    _save_ads(conn, ads)

    matches = _get_relevant_users(conn, ads)
    _send_alerts(matches)


if __name__ == "__main__":
    main()
