# Entry point for the daily job: scrape -> match against subscriptions -> email.
# Meant to be run on a schedule (cron, or your host's scheduled-job feature),
# not inside the Flask app itself.
