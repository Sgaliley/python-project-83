import os
from datetime import datetime

import psycopg2
from psycopg2.extras import NamedTupleCursor
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')


def get_connected():
    return psycopg2.connect(DATABASE_URL)


def find_by_id(id: int) -> tuple[int, str, datetime]:
    """Find a record in the database table 'url' by id."""
    with get_connected() as connection:
        with connection.cursor(cursor_factory=NamedTupleCursor) as cursor:
            cursor.execute("SELECT * FROM urls WHERE id = %s", (id, ))
            return cursor.fetchone()


def find_by_name(name: str) -> tuple[int, str, datetime]:
    """Find a record in the database table 'url' by url's name."""
    with get_connected() as connection:
        with connection.cursor(cursor_factory=NamedTupleCursor) as cursor:
            cursor.execute("SELECT * FROM urls WHERE name = %s", (name, ))
            return cursor.fetchone()


def find_checks(url_id: int) -> list[tuple[int, str, datetime]]:
    """Find a record in the database table 'url_checks' by url's id."""
    url_checks = []

    with get_connected() as connection:
        with connection.cursor(cursor_factory=NamedTupleCursor) as cursor:
            cursor.execute("SELECT * FROM url_checks WHERE url_id = %s\
                           ORDER BY id DESC",
                           (url_id, ))
            url_checks.extend(cursor.fetchall())

    return url_checks


def find_all_urls() -> list[tuple[int, str, datetime]]:
    """
    Find all added addresses together with the time
    and status code of their last check.
    """
    urls = []

    with get_connected() as connection:
        with connection.cursor(cursor_factory=NamedTupleCursor) as cursor:
            cursor.execute(
                "SELECT urls.id, urls.name, \
                MAX(url_checks.created_at) AS check_time, \
                url_checks.status_code FROM urls \
                LEFT JOIN url_checks \
                ON urls.id = url_checks.url_id \
                GROUP BY urls.id, url_checks.status_code \
                ORDER BY urls.id DESC;"
            )
            urls.extend(cursor.fetchall())

    return urls