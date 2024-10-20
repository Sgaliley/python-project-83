from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse
import validators
from datetime import datetime
import requests
from bs4 import BeautifulSoup


load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')


def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn


@app.route('/index')
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/urls', methods=["POST"])
def add_url():
    url = request.form['url'].strip().lower()

    if not validators.url(url):
        flash('Некорректный URL', 'danger')
        return redirect(url_for('index'))

    parsed_url = urlparse(url)
    normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''INSERT INTO urls (name) VALUES (%s)
                    ON CONFLICT (name) DO NOTHING
                    RETURNING id''',
                    (normalized_url,)
                )
                result = cur.fetchone()

                if result:
                    flash('Страница успешно добавлена', 'success')
                    url_id = result['id']
                else:
                    flash('Страница уже существует', 'info')
                    cur.execute(
                        'SELECT id FROM urls WHERE name = %s', (normalized_url,)
                    )
                    url_id = cur.fetchone()['id']

                conn.commit()

            return redirect(url_for('show_url', id=url_id))

    except Exception as e:
        flash(f'Ошибка при добавлении страницы: {str(e)}', 'danger')
        return redirect(url_for('index'))


@app.route('/urls/<int:id>')
def show_url(id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT id, name, created_at FROM urls WHERE id = %s', (id,)
                )
                url = cur.fetchone()

                if not url:
                    flash('URL не найден', 'danger')
                    return redirect(url_for('list_urls'))

                cur.execute(
                    '''SELECT id, status_code, h1, title, description, created_at
                    FROM url_checks WHERE url_id = %s ORDER BY id DESC''', (id,)
                )
                checks = cur.fetchall()

        return render_template('urls/detail.html', url=url, checks=checks)

    except Exception as e:
        flash(f'Ошибка при загрузке данных: {str(e)}', 'danger')
        return redirect(url_for('list_urls'))


@app.route('/urls/<int:id>/checks', methods=['POST'])
def create_check(id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT name FROM urls WHERE id = %s', (id,))
                url = cur.fetchone()['name']

                response = requests.get(url)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')

                h1 = soup.h1.get_text(strip=True) if soup.h1 else ''
                title = soup.title.get_text(strip=True) if soup.title else ''
                description = None
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc and 'content' in meta_desc.attrs:
                    description = meta_desc['content']

                cur.execute(
                    '''INSERT INTO url_checks (url_id, status_code, h1, title, description, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)''',
                    (id, response.status_code, h1, title, description, datetime.now())
                )

                conn.commit()
                flash('Страница успешно проверена', 'success')

    except requests.RequestException as e:
        flash(f'Ошибка запроса: {str(e)}', 'danger')
    except Exception as e:
        flash(f'Ошибка проверки страницы: {str(e)}', 'danger')

    return redirect(url_for('show_url', id=id))


@app.route('/urls')
def list_urls():
    try:
        with get_db_connection() as conn:
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

        return render_template('urls/list.html', urls=urls)

    except Exception as e:
        flash(f'Ошибка при загрузке списка сайтов: {str(e)}', 'danger')
        return redirect(url_for('index'))


@app.errorhandler(404)
def pageNotFound(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internalServerError(error):
    return render_template('errors/500.html'), 500
