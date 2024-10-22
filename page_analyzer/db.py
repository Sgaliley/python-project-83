import psycopg2
from psycopg2.extras import RealDictCursor
from .config import DATABASE_URL


def get_db_connection():
    '''Соединение с базой данных.'''
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn


def add_url(conn, url: str) -> int:
    '''
    Добавляет URL в базу данных, если он еще не существует.
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
    Получает список проверок для URL по его ID.
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
    Добавляет проверку для URL в базу данных.
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
    Получает список всех URL с последней проверкой.
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
