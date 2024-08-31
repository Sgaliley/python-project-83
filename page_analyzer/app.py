from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
import os
import psycopg2
from urllib.parse import urlparse
import validators
from datetime import datetime
import requests
from bs4 import BeautifulSoup


load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)


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
        with conn.cursor() as cur:
            cur.execute(
                '''INSERT INTO urls (name) VALUES (%s)
                ON CONFLICT (name) DO NOTHING
                RETURNING id''',
                (normalized_url,)
            )
            result = cur.fetchone()

            if result is not None:
                flash('Страница успешно добавлена', 'success')
                url_id = result[0]
            else:
                flash('Страница уже существует', 'info')
                cur.execute(
                    'SELECT id FROM urls WHERE name = %s', (normalized_url,)
                    )
                url_id = cur.fetchone()[0]

            conn.commit()

            return redirect(url_for('show_url', id=url_id))

    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('index'))


@app.route('/urls/<int:id>')
def show_url(id):
    with conn.cursor() as cur:
        cur.execute('''SELECT id,
                    name,
                    created_at::date
                    FROM urls
                    WHERE id = %s''', (id,))
        url = cur.fetchone()
        
        print(f"URL данные: {url}")  # Отладочный вывод
        print(f"URL данные: {url[0]}")

        cur.execute('''SELECT id,
                    status_code,
                    h1,
                    title,
                    description,
                    created_at::date
                    FROM url_checks
                    WHERE url_id = %s
                    ORDER BY id DESC''', (id,))
        checks = cur.fetchall()
        
        print(f"Checks данные: {checks}")  # Отладочный вывод
        print(f"Checks данные: {checks[0][0]}")

    if not url:
        flash('URL не найден.', 'danger')
        return redirect(url_for('list_urls'))

    # url_dict = {'id': url[0], 'name': url[1], 'created_at': url[2]}
    # checks_dict = {'id': checks[0][0],
    #                'status_code': checks[0][1],
    #                'h1': checks[0][2],
    #                'title': checks[0][3],
    #                'description': checks[0][4],
    #                'created_at': checks[0][5]}

    return render_template(
        'urls/detail.html',
        url=url,
        checks=checks)


@app.route('/urls/<int:id>/checks', methods=['POST'])
def create_check(id):
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT name FROM urls WHERE id = %s', (id,))
                url = cur.fetchone()[0]

                response = requests.get(url)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')

                h1 = soup.h1.get_text(strip=True) if soup.h1 else ''
                title = soup.title.get_text(strip=True) if soup.title else ''

                description = None
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc and 'content' in meta_desc.attrs:
                    description = meta_desc['content']

                cur.execute('''
                    INSERT INTO url_checks (url_id,
                    status_code,
                    h1,
                    title,
                    description,
                    created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (id,
                      response.status_code,
                      h1,
                      title,
                      description,
                      datetime.now()))

                conn.commit()
                flash('Страница успешно проверена', 'success')

    except Exception:
        flash('Произошла ошибка при проверке', 'danger')

    return redirect(url_for('show_url', id=id))


@app.route('/urls')
def list_urls():
    with conn.cursor() as cur:
        cur.execute('''
                    SELECT urls.id,
                           urls.name,
                           url_checks.created_at::date,
                           url_checks.status_code
                    FROM urls
                    LEFT JOIN (
                        SELECT DISTINCT ON (url_id) url_id,
                        status_code,
                        created_at
                        FROM url_checks AS last_check
                        ORDER BY url_id, created_at DESC
                            ) AS url_checks ON urls.id = url_checks.url_id
                    ORDER BY urls.created_at DESC;
                    ''')
        urls = cur.fetchall()

    urls_dict = [
        {'id': url[0],
         'name': url[1],
         'last_check': url[2],
         'last_status_code': url[3]}
        for url in urls]

    return render_template('urls/list.html', urls=urls_dict)


@app.errorhandler(404)
def pageNotFound(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internalServerError(error):
    return render_template('errors/500.html'), 500
