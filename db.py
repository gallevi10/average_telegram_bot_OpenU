# Average Bot - Telegram Bot for GPA Calculation
# Author: Gal Levi
# Date: February 2025
# License: MIT
# Version: 2.0
# Description: This file contains the database initialization and functions used by the bot.

import sqlite3
from utils import *

PATH = "data/database.db"

def setup_database() -> None:
    """Initializes the database and creates tables if they don't exist."""
    with sqlite3.connect(PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;") # enables write-ahead logging for better performance
        # creates the table if it doesn't exist
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                last_grades TEXT,
                saved_grades TEXT,
                exact_science INTEGER
            )
            """
        )

        conn.commit()


def update_last_grades(user_id : int, last_grades : list) -> None:
    """Updates the last entered grades of a user."""
    with sqlite3.connect(PATH) as conn:
        cursor = conn.cursor()

        last_grades_str = pack_grades(last_grades)

        cursor.execute(
            """
            INSERT INTO users (user_id, last_grades)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET last_grades=excluded.last_grades;
            """, (user_id, last_grades_str)
        )

        conn.commit()


def get_last_grades(user_id : int) -> list:
    """Retrieves the last entered grades of a user."""
    with sqlite3.connect(PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT last_grades FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone() # fetches the first row

    return unpack_grades(result[0]) if result and result[0] else []


def update_saved_grades(user_id : int, saved_grades : list) -> None:
    """Saves grades that the user chose to keep."""
    with sqlite3.connect(PATH) as conn:
        cursor = conn.cursor()

        saved_grades_str = pack_grades(saved_grades)

        cursor.execute(
            """
            INSERT INTO users (user_id, saved_grades)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET saved_grades=excluded.saved_grades;
        """, (user_id, saved_grades_str)
        )

        conn.commit()

def get_saved_grades(user_id : int) -> list:
    """Retrieves the grades that the user has saved."""
    with sqlite3.connect(PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT saved_grades FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()

    return unpack_grades(result[0]) if result and result[0] else []


def update_exact_science(user_id : int, exact_science : bool) -> None:
    """Updates the user's choice of exact science."""
    with sqlite3.connect(PATH) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO users (user_id, exact_science)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET exact_science=excluded.exact_science;
            """, (user_id, 1 if exact_science is True else 0)
        )

        conn.commit()


def get_exact_science(user_id : int) -> int:
    """Retrieves the user's choice of exact science."""
    with sqlite3.connect(PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT exact_science FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()

    return result[0] if result else -1


def get_total_users() -> int:
    """Retrieves the total number of users."""
    with sqlite3.connect(PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM users")
        result = cursor.fetchone()

    return result[0] if result else 0
