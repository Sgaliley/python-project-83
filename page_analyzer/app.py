from flask import Flask, render_template, request, redirect, url_for, flash
from .config import SECRET_KEY
from .db import (get_db_connection,
                 add_url,
                 get_url_by_id,
                 get_url_checks_by_id,
                 get_url_and_add_check,
                 get_all_urls_with_latest_check)
from .services import normalize_url
import validators


app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY


@app.route('/index')
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/urls', methods=["POST"])
def add_url_route():
    url = request.form['url'].strip().lower()

    if not validators.url(url):
        flash('Некорректный URL', 'danger')
        return render_template('index.html'), 422

    normalized_url = normalize_url(url)

    try:
        with get_db_connection() as conn:
            url_id, inserted = add_url(conn, normalized_url)
            conn.commit()

            if inserted:
                flash('Страница успешно добавлена', 'success')
            else:
                flash('Страница уже существует', 'info')

        return redirect(url_for('show_url', id=url_id))

    except Exception:
        flash('Произошла ошибка. Попробуйте позже.', 'danger')
        return redirect(url_for('index'))


@app.route('/urls/<int:id>')
def show_url(id):
    try:
        with get_db_connection() as conn:
            url = get_url_by_id(conn, id)

            if not url:
                flash('URL не найден', 'danger')
                return redirect(url_for('list_urls'))

            checks = get_url_checks_by_id(conn, id)

        return render_template('urls/detail.html', url=url, checks=checks)

    except Exception:
        flash('Ошибка при загрузке данных', 'danger')
        return redirect(url_for('list_urls'))


@app.route('/urls/<int:id>/checks', methods=['POST'])
def create_check(id):
    try:
        with get_db_connection() as conn:
            result = get_url_and_add_check(conn, id)
            if not result:
                flash('URL не найден', 'danger')
                return redirect(url_for('list_urls'))

            flash('Страница успешно проверена', 'success')

    except Exception:
        flash('Произошла ошибка при проверке', 'danger')

    return redirect(url_for('show_url', id=id))


@app.route('/urls')
def list_urls():
    try:
        with get_db_connection() as conn:
            urls = get_all_urls_with_latest_check(conn)

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
