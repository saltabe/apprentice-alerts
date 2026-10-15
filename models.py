# Database schema and access helpers, shared by app.py and daily_alert.py.

import os
import sqlite3


def get_connection():
    conn = sqlite3.connect(os.environ.get("DB_PATH", "users.db"))
    conn.row_factory = sqlite3.Row

    return conn


def init_db(conn):
    create_users_table(conn)
    create_ads_table(conn)


# ---------------------------------------------------------------------------
# Users table
# ---------------------------------------------------------------------------

def create_users_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT
            , city TEXT
            , keyword TEXT
            )
    """)


def insert_user(conn, email, city, keyword):
    conn.execute(
        "INSERT INTO users (email, city, keyword) VALUES (?, ?, ?)", (email, city, keyword)
    )


def select_user(conn, email):
    return conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchall()


def select_all_users(conn):
    return conn.execute("SELECT * FROM users").fetchall()


def select_emails(conn, keyword):
    rows = conn.execute("SELECT email FROM users WHERE keyword = ?", (keyword,)).fetchall()

    return [row["email"] for row in rows]


def update_user(conn, new_email, new_city, new_keyword, email, keyword):
    conn.execute(
        "UPDATE users SET email = ?, city = ?, keyword = ? WHERE email = ? AND keyword = ?",
        (new_email, new_city, new_keyword, email, keyword)
    )


def delete_user(conn, email):
    conn.execute("DELETE FROM users WHERE email = ?", (email,))


# ---------------------------------------------------------------------------
# Ads table
# ---------------------------------------------------------------------------

def create_ads_table(conn):
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