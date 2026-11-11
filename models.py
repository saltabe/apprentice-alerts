# Database schema and access helpers, shared by app.py and daily_alert.py.

import os
import sqlite3


def get_connection():
    conn = sqlite3.connect(os.environ.get("DB_PATH", "users.db"))
    conn.row_factory = sqlite3.Row

    return conn


def init_db(conn):
    _create_users_table(conn)
    _create_ads_table(conn)


# ---------------------------------------------------------------------------
# Users table
# ---------------------------------------------------------------------------

def _create_users_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT
            , city TEXT
            , keyword TEXT
            , keyword_type TEXT
            )
    """)

    # migrate rows from before keyword_type existed - they were all
    # "include" keywords under the old single-field model
    columns = [row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "keyword_type" not in columns:
        conn.execute("ALTER TABLE users ADD COLUMN keyword_type TEXT")
        conn.execute("UPDATE users SET keyword_type = 'include' WHERE keyword_type IS NULL")
        conn.commit()


def insert_user(conn, email, city, keyword, keyword_type):
    conn.execute(
        "INSERT INTO users (email, city, keyword, keyword_type) VALUES (?, ?, ?, ?)",
        (email, city, keyword, keyword_type)
    )


def select_user(conn, email):
    return conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchall()


def select_all_users(conn):
    return conn.execute("SELECT * FROM users").fetchall()


def delete_user(conn, email):
    conn.execute("DELETE FROM users WHERE email = ?", (email,))


# ---------------------------------------------------------------------------
# Ads table
# ---------------------------------------------------------------------------

def _create_ads_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ads (
            edit_id INTEGER PRIMARY KEY
            , title TEXT
            , service_type TEXT
            , fee TEXT
            , salon TEXT
            , neighborhood TEXT
            , next_service_date TEXT
            )
    """)


def insert_ad(conn, edit_id, title, service_type, fee, salon, neighborhood, next_service_date):
    conn.execute("""
        INSERT INTO ads (
            edit_id
            , title
            , service_type
            , fee
            , salon
            , neighborhood
            , next_service_date
            )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (edit_id, title, service_type, fee, salon, neighborhood, next_service_date))


def select_ad(conn, edit_id):
    return conn.execute("SELECT * FROM ads WHERE edit_id = ?", (edit_id,)).fetchone()