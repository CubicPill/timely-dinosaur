from flask import Flask


@app.route('/')
def index():
    pass


def main():
    global app
    app = Flask(__name__)


def init():
    main()
