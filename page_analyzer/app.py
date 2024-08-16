from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
import os
import psycopg2
from urllib.parse import urlparse
import validators
from datetime import datetime

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

    # Валидация URL
    if not validators.url(url):
        flash('Некорректный URL', 'danger')
        return redirect(url_for('index'))

    parsed_url = urlparse(url)
    normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

    try:
        with conn.cursor() as cur:
            cur.execute('INSERT INTO urls (name) VALUES (%s) ON CONFLICT (name) DO NOTHING RETURNING id', (normalized_url,))
            result = cur.fetchone()
            
            if result is not None:
                flash('Страница успешно добавлена', 'success')
                url_id = result[0]
            else:
                flash('Страница уже существует', 'info')
                cur.execute('SELECT id FROM urls WHERE name = %s', (normalized_url,))
                url_id = cur.fetchone()[0]

            conn.commit()
    
            return redirect(url_for('show_url', id=url_id))

    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('index'))


@app.route('/urls')
def urls():
    with conn.cursor() as cur:
        cur.execute('SELECT id, name, created_at::date FROM urls ORDER BY id DESC')
        urls = cur.fetchall()

    return render_template('urls/list.html', urls=urls)


@app.route('/urls/<int:id>')
def show_url(id):
    with conn.cursor() as cur:
        cur.execute('SELECT id, name, created_at::date FROM urls WHERE id = %s', (id,))
        url = cur.fetchone()

    if not url:
        flash('URL not found.', 'danger')
        return redirect(url_for('urls'))

    return render_template('urls/detail.html', url=url)


@app.errorhandler(404)
def pageNotFound(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internalServerError(error):
    return render_template('errors/500.html'), 500


if __name__ == "__main__":
    app.run(debug=True)
