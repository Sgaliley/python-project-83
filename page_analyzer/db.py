import psycopg2
from psycopg2.extras import RealDictCursor
from .config import DATABASE_URL
from .services import fetch_page_data
from datetime import datetime


def get_db_connection():
    '''Database connection.'''
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn


def add_url(conn, url: str) -> (int, bool):
    '''
    Adds the URL to the database if it does not already exist.
    '''
    with conn.cursor() as cur:
        cur.execute(
            '''INSERT INTO urls (name) VALUES (%s)
            ON CONFLICT (name) DO NOTHING
            RETURNING id''',
            (url,)
        )
        result = cur.fetchone()

        if result:
            url_id = result['id']
            inserted = True
        else:
            cur.execute(
                '''SELECT id FROM urls
                WHERE name = %s''', (url,)
            )
            url_id = cur.fetchone()['id']
            inserted = False

    return url_id, inserted


def get_url_by_id(conn, id: int) -> dict:
    '''
    Получает информацию о URL по его ID.
    '''
    with conn.cursor() as cur:
        cur.execute(
            '''SELECT id, name, created_at
            FROM urls
            WHERE id = %s''', (id,)
        )
        url = cur.fetchone()

    return url


def get_url_checks_by_id(conn, id: int) -> list:
    '''
    Gets information about a URL by its ID.
    '''
    with conn.cursor() as cur:
        cur.execute(
            '''SELECT id,
                   status_code,
                   h1,
                   title,
                   description,
                   created_at
            FROM url_checks
            WHERE url_id = %s ORDER BY id DESC''', (id,)
        )
        checks = cur.fetchall()

    return checks


def add_url_check(conn, url_id: int, check_data: dict):
    '''
    Adds validation for the URL to the database.
    '''
    with conn.cursor() as cur:
        cur.execute(
            '''INSERT INTO url_checks (
                url_id,
                status_code,
                h1,
                title,
                description,
                created_at
            ) VALUES (%s, %s, %s, %s, %s, %s)''',
            (url_id,
             check_data['status_code'],
             check_data['h1'],
             check_data['title'],
             check_data['description'],
             check_data['created_at'])
        )


def get_all_urls_with_latest_check(conn) -> list:
    '''
    Gets a list of all URLs with the last validation.
    '''
    with conn.cursor() as cur:
        cur.execute('''
            SELECT urls.id,
                   urls.name,
                   url_checks.created_at,
                   url_checks.status_code
            FROM urls
            LEFT JOIN (
                SELECT DISTINCT ON (url_id) url_id,
                       status_code,
                       created_at
                FROM url_checks
                ORDER BY url_id, created_at DESC
            ) AS url_checks ON urls.id = url_checks.url_id
            ORDER BY urls.created_at DESC;
        ''')
        urls = cur.fetchall()

    return urls


def get_url_and_add_check(conn, id: int) -> dict:
    '''
    Получает URL по ID и добавляет проверку страницы.
    '''
    with conn.cursor() as cur:
        cur.execute('SELECT name FROM urls WHERE id = %s', (id,))
        url_row = cur.fetchone()
        if not url_row:
            return None

        url = url_row['name']
        page_data = fetch_page_data(url)
        page_data['created_at'] = datetime.now()

        add_url_check(conn, id, page_data)
        conn.commit()

    return page_data
