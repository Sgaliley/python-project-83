from flask import Flask, render_template, request
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

@app.route('/index')
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/urls', methods=["POST", "GET"])
def urls():
    return render_template('urls.html')

@app.errorhandler(404)
def pageNotFound(error):
    return render_template('errors/404.html'), 404


if __name__ == "__main__":
    app.run(debug=True)