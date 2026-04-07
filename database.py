# -*- coding: utf-8 -*-
"""SQLite-???? ??? ???????? ???????? ????????????? ? ?????? ???? ???????????."""

import os
import sqlite3
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", "bot.db")


def get_connection():
    """?????????? ?????????? ? ??."""
    return sqlite3.connect(DB_PATH)


def init_db():
    """??????? ??????? users ? ????????? ??????? ????????????? ??? ?????????????."""
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                subscribed INTEGER DEFAULT 0,
                notify_day1 INTEGER DEFAULT 0,
                notify_day2 INTEGER DEFAULT 0,
                notify_day3 INTEGER DEFAULT 0,
                updated_at TEXT
            )
        """)
        conn.commit()
        for col, typ in [("specialty_id", "INTEGER"), ("specialty_name", "TEXT")]:
            try:
                conn.execute(f"ALTER TABLE users ADD COLUMN {col} {typ}")
                conn.commit()
            except sqlite3.OperationalError as e:
                if "duplicate" not in str(e).lower():
                    raise
    finally:
        conn.close()
    logger.info("?? ????????????????: %s", DB_PATH)


def ensure_user(user_id: int, username: str = None):
    """?????? ?????? ????????????, ???? ? ???."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)""",
            (user_id, username or ""),
        )
        conn.commit()
    finally:
        conn.close()


def set_subscribed(user_id: int, subscribed: bool = True):
    """???????? ???????????? ??? ???????????? ?? ?????."""
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE users SET subscribed = ?, updated_at = datetime('now')
               WHERE user_id = ?""",
            (1 if subscribed else 0, user_id),
        )
        conn.commit()
    finally:
        conn.close()


def set_notify_day(user_id: int, day: int, value: bool):
    """????????/????????? ??????????? ?? ???? (day: 1, 2 ??? 3)."""
    if day not in (1, 2, 3):
        return
    col = f"notify_day{day}"
    conn = get_connection()
    try:
        conn.execute(
            f"""UPDATE users SET {col} = ?, updated_at = datetime('now')
                WHERE user_id = ?""",
            (1 if value else 0, user_id),
        )
        conn.commit()
    finally:
        conn.close()


def set_specialty(user_id: int, specialty_id: int, specialty_name: str):
    """????????? ????????? ????????????? ????????????."""
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE users SET specialty_id = ?, specialty_name = ?, updated_at = datetime('now')
               WHERE user_id = ?""",
            (specialty_id, specialty_name or "", user_id),
        )
        conn.commit()
    finally:
        conn.close()


def get_user(user_id: int) -> dict | None:
    """?????????? ?????? ???????????? ??? None."""
    conn = get_connection()
    try:
        row = conn.execute(
            """SELECT user_id, username, subscribed, notify_day1, notify_day2, notify_day3,
                      specialty_id, specialty_name
               FROM users WHERE user_id = ?""",
            (user_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "user_id": row[0],
            "username": row[1],
            "subscribed": bool(row[2]),
            "notify_day1": bool(row[3]),
            "notify_day2": bool(row[4]),
            "notify_day3": bool(row[5]),
            "specialty_id": row[6] if len(row) > 6 else None,
            "specialty_name": (row[7] or "").strip() if len(row) > 7 else "",
        }
    finally:
        conn.close()


def get_users_for_day(day: int) -> list[int]:
    """?????????? ?????? user_id, ??????????? ?? ??????????? ?? ???? (1, 2 ??? 3)."""
    if day not in (1, 2, 3):
        return []
    col = f"notify_day{day}"
    conn = get_connection()
    try:
        rows = conn.execute(
            f"""SELECT user_id FROM users WHERE subscribed = 1 AND {col} = 1""",
        ).fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()


def get_users_for_any_day(days: list[int]) -> list[int]:
    """?????????? ?????????? ?????? user_id, ??????????? ???? ?? ?? ???? ?? ????."""
    valid = [d for d in days if d in (1, 2, 3)]
    if not valid:
        return []
    seen = set()
    result = []
    for d in valid:
        for uid in get_users_for_day(d):
            if uid not in seen:
                seen.add(uid)
                result.append(uid)
    return result


def get_all_subscribed_users() -> list[int]:
    """Return all user_id where subscribed = 1."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT user_id FROM users WHERE subscribed = 1",
        ).fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()