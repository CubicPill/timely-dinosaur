from flask import Flask


@app.route('/')
def index():
    pass


def save_result():
    pass


def read_current():
    pass


def main():
    global app
    app = Flask(__name__)
    print('Please go to http://localhost:2333 to view the web GUI')
    app.run(host='localhost', port=2333)


def init():
    main()
